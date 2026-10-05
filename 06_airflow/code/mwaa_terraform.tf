# MWAA environment — production-grade Terraform reference
# References: Topic 06 module 16 (MWAA).

# ── S3 bucket for DAGs ───────────────────────────────────────────────────
resource "aws_s3_bucket" "dags" {
  bucket = "${var.org}-mwaa-dags-${var.env}"
}

resource "aws_s3_bucket_versioning" "dags" {
  bucket = aws_s3_bucket.dags.id
  versioning_configuration { status = "Enabled" }    # MWAA requires versioning
}

resource "aws_s3_bucket_server_side_encryption_configuration" "dags" {
  bucket = aws_s3_bucket.dags.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.mwaa.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "dags" {
  bucket                  = aws_s3_bucket.dags.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── KMS CMK for MWAA + logs ─────────────────────────────────────────────
resource "aws_kms_key" "mwaa" {
  description             = "CMK for MWAA env ${var.env}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# ── IAM execution role for MWAA ─────────────────────────────────────────
data "aws_iam_policy_document" "mwaa_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["airflow.amazonaws.com", "airflow-env.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "mwaa_exec" {
  name               = "mwaa-${var.env}-exec"
  assume_role_policy = data.aws_iam_policy_document.mwaa_trust.json
}

resource "aws_iam_role_policy" "mwaa_exec_perms" {
  role   = aws_iam_role.mwaa_exec.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = "airflow:*", Resource = "*" },
      { Effect = "Allow", Action = [
        "s3:GetObject*", "s3:GetBucket*", "s3:List*", "s3:GetEncryptionConfiguration"
      ], Resource = [
        aws_s3_bucket.dags.arn, "${aws_s3_bucket.dags.arn}/*"
      ]},
      { Effect = "Allow", Action = "kms:Decrypt",
        Resource = aws_kms_key.mwaa.arn },
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
        Resource = "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.current.account_id}:secret:airflow/*" },
      { Effect = "Allow", Action = [
        "logs:CreateLogStream", "logs:PutLogEvents", "logs:GetLogEvents",
        "logs:GetLogRecord", "logs:DescribeLogGroups", "logs:DescribeLogStreams",
        "logs:GetQueryResults"
      ], Resource = "arn:aws:logs:${var.region}:*:log-group:airflow-${var.env}-*" },
      { Effect = "Allow", Action = ["cloudwatch:PutMetricData"], Resource = "*" },
      { Effect = "Allow", Action = ["sqs:*"],
        Resource = "arn:aws:sqs:${var.region}:*:airflow-celery-*" },
      # for K8sPodOperator → EKS
      { Effect = "Allow", Action = ["sts:AssumeRole"],
        Resource = "arn:aws:iam::*:role/mwaa-eks-pod-launcher" },
    ]
  })
}

# ── VPC endpoints (no NAT — fully private) ──────────────────────────────
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.private_route_table_ids
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.private_subnet_ids
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = true
}

# Similar for: ecr.api, ecr.dkr, kms, logs, sqs, monitoring

# ── The MWAA env ────────────────────────────────────────────────────────
resource "aws_mwaa_environment" "this" {
  name              = "mwaa-${var.env}"
  airflow_version   = "2.10.3"
  environment_class = "mw1.large"

  source_bucket_arn  = aws_s3_bucket.dags.arn
  dag_s3_path        = "dags"
  plugins_s3_path    = "plugins.zip"
  requirements_s3_path = "requirements.txt"

  execution_role_arn = aws_iam_role.mwaa_exec.arn
  kms_key            = aws_kms_key.mwaa.arn

  webserver_access_mode = "PRIVATE_ONLY"   # regulated-finance default

  network_configuration {
    security_group_ids = [aws_security_group.mwaa.id]
    subnet_ids         = var.private_subnet_ids
  }

  logging_configuration {
    dag_processing_logs { enabled = true, log_level = "WARNING" }
    scheduler_logs      { enabled = true, log_level = "INFO" }
    task_logs           { enabled = true, log_level = "INFO" }
    webserver_logs      { enabled = true, log_level = "INFO" }
    worker_logs         { enabled = true, log_level = "INFO" }
  }

  airflow_configuration_options = {
    "core.load_examples" = "False"
    "core.dag_dir_list_interval" = "300"
    "webserver.expose_config" = "False"
    "secrets.backend" = "airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend"
    "secrets.backend_kwargs" = jsonencode({
      connections_prefix = "airflow/connections"
      variables_prefix   = "airflow/variables"
    })
  }

  min_workers = 1
  max_workers = 10

  tags = {
    Team       = "data-platform"
    CostCenter = "data-eng"
    Env        = var.env
  }
}

# ── Outputs ─────────────────────────────────────────────────────────────
data "aws_caller_identity" "current" {}

output "webserver_url" {
  value = aws_mwaa_environment.this.webserver_url
}
