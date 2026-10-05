# 13 — Infrastructure as Code with Terraform

## Why this module exists

Terraform (and its 2023 OSS fork **OpenTofu**) is the lingua franca of cloud infrastructure. Capital One uses Terraform. AWS-shop interviews assume Terraform fluency. This is a net-new module (no other Topic in the project goes deep on Terraform).

## 1. The IaC tool landscape (2026)

| Tool | Lang | Cloud | When |
|---|---|---|---|
| **Terraform** (HashiCorp, BUSL since Aug 2023) | HCL | All | Industry default; BUSL = source-available, not OSS |
| **OpenTofu** (Linux Foundation, fork) | HCL | All | OSS Terraform-compatible; growing 2024–2026 |
| **AWS CloudFormation** | YAML/JSON | AWS-only | AWS-native; weak DX vs Terraform |
| **AWS CDK** | TS/Py/Java/Go | AWS-only | Programming language; transpiles to CFN |
| **Pulumi** | TS/Py/Go/.NET | All | Real-language IaC; smaller community |
| **Crossplane** | YAML (K8s CRDs) | All | K8s-native IaC; for GitOps shops |
| **Bicep** | DSL | Azure-only | CFN-equivalent for Azure |

The 2026 reality:
- **Pure OSS shops** → OpenTofu
- **Established Terraform shops** → mostly still on Terraform; some moving to OpenTofu
- **AWS-only shops** → Terraform or CDK
- **K8s-native shops** → Crossplane increasing

## 2. Terraform installation + first project

```bash
brew install terraform   # or: brew install opentofu
terraform version
terraform init           # download providers, init backend
terraform plan           # preview
terraform apply          # apply
terraform destroy        # tear down
```

Minimal project:
```
.
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
└── terraform.tfvars     # gitignored — secrets/env-specific
```

```hcl
# versions.tf
terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
  backend "s3" {
    bucket         = "my-tf-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf-state-lock"   # state locking
    encrypt        = true
  }
}

# variables.tf
variable "region" {
  type    = string
  default = "us-east-1"
}

# main.tf
provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "logs" {
  bucket = "my-logs-${random_id.suffix.hex}"
  force_destroy = false

  tags = {
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

# outputs.tf
output "bucket_name" {
  value = aws_s3_bucket.logs.id
}
```

## 3. Resources, Data Sources, Providers

- **Resource** — something you create + manage (`aws_instance`, `aws_s3_bucket`).
- **Data Source** — something you read but don't manage (`data "aws_ami" "ubuntu"`).
- **Provider** — the plugin that talks to a cloud (AWS, Azure, K8s, GitHub, Datadog).

```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
}
```

## 4. The Terraform commands you'll run

```bash
terraform init                # download providers + init backend
terraform fmt -recursive      # canonical formatting
terraform validate            # syntax + basic checks
terraform plan                # show what will change
terraform plan -out=p.tfplan  # save plan
terraform apply p.tfplan      # apply saved plan (CI/CD pattern)
terraform apply -auto-approve # skip prompt
terraform destroy             # tear down
terraform state list          # what's in state
terraform state show <addr>   # inspect resource state
terraform state mv <old> <new>  # rename without recreate
terraform import <addr> <id>  # adopt existing resource into state
terraform output              # values
terraform workspace list      # workspaces (not for env separation — use dir + backend)
```

## 5. State — the most important concept

Terraform tracks **what it manages** in a state file. State maps resource addresses → cloud IDs. Without state, Terraform can't tell what to create vs update vs destroy.

- **Local state** (`terraform.tfstate` in directory) — for solo learning only
- **Remote state** — S3 + DynamoDB locking (AWS), Azure Storage + lease, GCS + locks, Terraform Cloud/Enterprise
- **State is sensitive** — contains computed values, sometimes secrets — encrypt at rest, restrict access
- **Never edit state by hand** — use `terraform state` commands

## 6. Variables + Environment Variables

```hcl
variable "region" {
  type    = string
  default = "us-east-1"
}

variable "tags" {
  type    = map(string)
  default = {}
}
```

Set values via:
- `terraform.tfvars` file (auto-loaded)
- `*.auto.tfvars` files
- `-var "region=us-west-2"` flag
- `TF_VAR_region=us-west-2` env var
- Prompted at runtime if no default

For secrets: never put in `.tf` or committed `.tfvars`. Use `TF_VAR_*` env vars (from CI/CD secret store) or read from Vault/Secrets Manager via data source.

## 7. Output Values

```hcl
output "vpc_id" {
  value = aws_vpc.main.id
}

output "db_endpoint" {
  value     = aws_rds_cluster.main.endpoint
  sensitive = true   # masks from console output
}
```

Outputs are consumed by other Terraform configs (via `terraform_remote_state` data source) or by CI/CD scripts.

## 8. Provisioners (use sparingly)

```hcl
resource "aws_instance" "web" {
  # ...
  provisioner "remote-exec" {
    inline = ["sudo apt update", "sudo apt install -y nginx"]
    connection {
      type     = "ssh"
      user     = "ubuntu"
      host     = self.public_ip
      private_key = file("~/.ssh/id_ed25519")
    }
  }
}
```

**Anti-pattern.** Use Ansible (Module 16), cloud-init `user_data`, or baked AMIs. Provisioners are non-idempotent escape hatches.

## 9. Modules — the DRY mechanism

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.13"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
  azs  = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  enable_nat_gateway = true
}
```

**Public Terraform Registry** (https://registry.terraform.io) hosts thousands of modules. Quality varies; prefer modules from cloud-provider orgs (terraform-aws-modules, hashicorp, etc.). For Capital One scale: internal-private module registry with vetted modules.

## 10. CI/CD for Terraform

```yaml
# GitHub Actions snippet
on: pull_request
jobs:
  tf-plan:
    runs-on: ubuntu-latest
    permissions: { id-token: write, contents: read, pull-requests: write }
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ secrets.AWS_ROLE_ARN }}, aws-region: us-east-1 }
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform fmt -check -recursive
      - run: terraform validate
      - run: terraform plan -no-color -out=tfplan
      - uses: actions/github-script@v7
        with:
          script: |
            const plan = require('child_process').execSync('terraform show -no-color tfplan').toString();
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner, repo: context.repo.repo,
              body: `\`\`\`\n${plan.slice(0, 65000)}\n\`\`\``
            })
```

Patterns:
1. **Plan in CI on PR**, apply on merge to main (after manual approval)
2. **Atlantis** or **Terraform Cloud** for governance
3. **Open Policy Agent (Rego)** or **checkov / tfsec** for policy-as-code gates

## 11. Best practices (the 12-point checklist)

1. **Remote state with locking** — never local state for shared infra
2. **One state per env** — separate directories or workspaces; never share prod + dev state
3. **Pin provider + module versions** — `~> 5.80`, not unconstrained
4. **`terraform fmt` + `validate` in CI** — enforce
5. **Run plan in CI on PR** — block merge if plan fails
6. **Apply gated by manual approval** — for prod
7. **No secrets in repo** — env vars from CI secret store
8. **Tag every resource** — Environment, Owner, ManagedBy, CostCenter
9. **Modules for repeatable patterns** — DRY at scale
10. **`for_each` over `count`** for resources from collections (count breaks on reorder)
11. **`terraform import` for adopting existing resources** — don't recreate
12. **Drift detection** — scheduled plan against prod, alert on drift

## 12. Quick self-check

1. What does `terraform init` do?
2. Why is local state dangerous for team work?
3. When would you use `data` vs `resource`?
4. Why are provisioners considered an anti-pattern?
5. What's the difference between Terraform and OpenTofu, and why does it matter?

(Answers: downloads providers + initializes backend; no locking, single source of truth lost, secrets in plaintext; data for existing resources you reference, resource for things you manage; non-idempotent, run-once nature breaks Terraform's declarative model; OpenTofu is the OSS fork after HashiCorp's BUSL relicense — matters for OSS-purity shops and avoiding vendor lock-in.)
