# Terraform — HIPAA/PCI-style regulated-finance VPC
#
# What it builds:
#   - VPC with 3 AZs
#   - Public subnets (for ALBs only, not workloads)
#   - Private subnets (with NAT egress for app workloads)
#   - Isolated subnets (no egress; for SageMaker, RDS, sensitive)
#   - Gateway endpoints for S3 and DynamoDB (free)
#   - Interface endpoints for SageMaker, KMS, ECR, STS, Secrets Manager
#   - VPC Flow Logs to S3
#
# This is the regulated-finance starter VPC pattern. Capital One's actual
# topology is hub-and-spoke with this kind of VPC as a "spoke" in a workload
# account, shared from a network account via RAM.

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "az_count" {
  type    = number
  default = 3
}

variable "tags" {
  type = map(string)
  default = {
    Environment      = "prod"
    DataClassification = "Confidential"
    Compliance       = "pci"
    Owner            = "ml-platform-team@example.com"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# =====================================================
# VPC
# =====================================================

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = merge(var.tags, { Name = "ml-platform-vpc" })
}

# =====================================================
# Subnets — three tiers
# =====================================================

# Public subnets (for ALBs, NAT GWs only)
resource "aws_subnet" "public" {
  count                   = var.az_count
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = false
  tags                    = merge(var.tags, { Name = "public-${count.index}", Tier = "public" })
}

# Private subnets (workloads needing internet egress via NAT)
resource "aws_subnet" "private" {
  count             = var.az_count
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags              = merge(var.tags, { Name = "private-${count.index}", Tier = "private" })
}

# Isolated subnets (no internet egress, SageMaker, RDS, sensitive)
resource "aws_subnet" "isolated" {
  count             = var.az_count
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 20)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags              = merge(var.tags, { Name = "isolated-${count.index}", Tier = "isolated" })
}

# =====================================================
# Internet Gateway + NAT (for private tier only)
# =====================================================

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = merge(var.tags, { Name = "igw" })
}

resource "aws_eip" "nat" {
  count  = var.az_count
  domain = "vpc"
  tags   = merge(var.tags, { Name = "nat-eip-${count.index}" })
}

resource "aws_nat_gateway" "main" {
  count         = var.az_count
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  tags          = merge(var.tags, { Name = "nat-${count.index}" })
}

# =====================================================
# Route tables
# =====================================================

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = merge(var.tags, { Name = "rt-public" })
}

resource "aws_route_table" "private" {
  count  = var.az_count
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }
  tags = merge(var.tags, { Name = "rt-private-${count.index}" })
}

resource "aws_route_table" "isolated" {
  count  = var.az_count
  vpc_id = aws_vpc.main.id
  # No default route — isolated tier truly has no egress
  tags   = merge(var.tags, { Name = "rt-isolated-${count.index}" })
}

resource "aws_route_table_association" "public" {
  count          = var.az_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = var.az_count
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "isolated" {
  count          = var.az_count
  subnet_id      = aws_subnet.isolated[count.index].id
  route_table_id = aws_route_table.isolated[count.index].id
}

# =====================================================
# Gateway endpoints (free) — S3, DynamoDB
# =====================================================

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = concat(aws_route_table.private[*].id, aws_route_table.isolated[*].id)

  # Endpoint policy: only allow principals in this org
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = "*"
      Action    = "*"
      Resource  = "*"
      Condition = {
        StringEquals = {
          "aws:PrincipalOrgID" = data.aws_organizations_organization.current.id
        }
      }
    }]
  })

  tags = merge(var.tags, { Name = "vpce-s3" })
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = concat(aws_route_table.private[*].id, aws_route_table.isolated[*].id)
  tags              = merge(var.tags, { Name = "vpce-ddb" })
}

# =====================================================
# Interface endpoints — SageMaker, KMS, ECR, STS, etc.
# =====================================================

resource "aws_security_group" "vpc_endpoints" {
  name   = "vpc-endpoints-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "sg-vpc-endpoints" })
}

locals {
  interface_endpoints = [
    "sagemaker.api",
    "sagemaker.runtime",
    "kms",
    "ecr.api",
    "ecr.dkr",
    "sts",
    "secretsmanager",
    "logs",
    "ssm",
    "ssmmessages",
    "ec2messages",
  ]
}

resource "aws_vpc_endpoint" "interface" {
  for_each            = toset(local.interface_endpoints)
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.${each.key}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.isolated[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(var.tags, { Name = "vpce-${each.key}" })
}

# =====================================================
# VPC Flow Logs to S3
# =====================================================

resource "aws_flow_log" "vpc" {
  vpc_id               = aws_vpc.main.id
  traffic_type         = "ALL"
  log_destination_type = "s3"
  log_destination      = "arn:aws:s3:::${var.flow_logs_bucket}/vpc-flow-logs/"
  log_format           = "$${version} $${account-id} $${interface-id} $${srcaddr} $${dstaddr} $${srcport} $${dstport} $${protocol} $${packets} $${bytes} $${start} $${end} $${action} $${log-status} $${vpc-id} $${subnet-id} $${instance-id} $${tcp-flags} $${pkt-srcaddr} $${pkt-dstaddr} $${flow-direction} $${traffic-path}"

  tags = merge(var.tags, { Name = "vpc-flow-logs" })
}

variable "flow_logs_bucket" {
  type        = string
  description = "S3 bucket for VPC Flow Logs (must already exist with proper bucket policy)"
}

data "aws_region" "current" {}
data "aws_organizations_organization" "current" {}

# =====================================================
# Outputs
# =====================================================

output "vpc_id" {
  value = aws_vpc.main.id
}

output "isolated_subnet_ids" {
  value       = aws_subnet.isolated[*].id
  description = "Use these for SageMaker, RDS, sensitive workloads"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "Use these for app workloads needing NAT egress"
}

# Cost estimate (us-east-1, May 2026):
# - 3 NAT GW: $32/mo × 3 = $96/mo + $0.045/GB processed
# - 11 Interface endpoints × 3 AZs × $0.01/hr × 730 = $241/mo
# - 2 Gateway endpoints: free
# - Flow Logs to S3: storage cost only
# - Total VPC infrastructure: ~$340/mo before data transfer
