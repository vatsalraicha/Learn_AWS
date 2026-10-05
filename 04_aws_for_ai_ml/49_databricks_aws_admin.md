# Module 49 — Databricks-AWS Admin & Ops

> **What this is:** MWS Account API, Terraform Databricks provider, workspace deployment patterns, DBU economics, audit log delivery, KMS key separation.

---

## 1. MWS Account API endpoints

The Multi-Workspace Service API lives at `https://accounts.cloud.databricks.com`.

Key resources:
- **Credentials** — cross-account IAM role.
- **Networks** — VPC + subnets + SG references.
- **Storage** — S3 bucket for root storage.
- **Customer-managed keys (CMKs)** — KMS for workspace, managed services, S3.
- **Workspaces** — composed of above.
- **Log delivery** — config for audit logs to S3.

## 2. Terraform two-provider pattern

```hcl
# Account-level provider
provider "databricks" {
  alias      = "mws"
  host       = "https://accounts.cloud.databricks.com"
  account_id = "..."
  username   = "..."
  password   = "..."
}

# Workspace-level provider
provider "databricks" {
  alias  = "workspace"
  host   = databricks_mws_workspaces.this.workspace_url
  token  = "..."
}
```

Use the account provider to create the workspace; use the workspace provider to manage inside it (clusters, jobs, secrets, UC).

## 3. Workspace deployment patterns

**Single-account-multi-workspace**:
- Pro: simpler IAM.
- Con: blast radius shared.

**Multi-account-multi-workspace** (Capital One likely):
- Pro: isolation per LOB or per env.
- Con: more complex Terraform; cross-account RAM for shared VPCs.

## 4. Billing and DBU economics

DBU rates vary by SKU (Module 48). System tables expose usage data inside Databricks:

```sql
SELECT workspace_id, sku_name, sum(usage_quantity) AS dbus
FROM system.billing.usage
WHERE usage_date >= current_date - INTERVAL 30 DAY
GROUP BY workspace_id, sku_name
ORDER BY dbus DESC;
```

Pair with AWS Cost Explorer for EC2 + EBS + S3 + NAT GW costs.

## 5. Audit log delivery

Configure log delivery to S3:
- **Workspace audit logs** — every UI/API action.
- **Account-level audit logs** — account-API actions.

Format: JSON, partitioned by date and workspace_id.

Consumers:
- **Datadog / Splunk** via Kinesis Firehose forwarding.
- **CloudTrail Lake** for cross-correlation.
- **Athena queries** for ad-hoc investigations.

## 6. KMS key separation

Best practice for regulated finance:
- **Workspace key** — encrypts notebook content, job results, secrets.
- **Managed services key** — encrypts control-plane-stored metadata.
- **Storage key** — encrypts S3 root storage and DBFS.

Separating keys lets you revoke one without breaking the others.

## 7. Audit logs vs CloudTrail

| | Databricks audit logs | CloudTrail |
|---|---|---|
| Captures | Databricks API actions | AWS API actions (including those Databricks makes) |
| Latency | Minutes | ~15 min |
| Retention | S3-lifecycle-controlled | CloudTrail Lake or S3 |
| Best for | "What did user X do in Databricks?" | "What AWS resources did Databricks create?" |

For full audit story, **collect both**.

## 8. Workspace deployment in CI

```hcl
resource "databricks_mws_workspaces" "card_ml_prod" {
  provider           = databricks.mws
  account_id         = var.databricks_account_id
  workspace_name     = "card-ml-prod"
  aws_region         = "us-east-1"
  credentials_id     = databricks_mws_credentials.card_ml_prod.credentials_id
  storage_configuration_id = databricks_mws_storage_configurations.card_ml_prod.storage_configuration_id
  network_id         = databricks_mws_networks.card_ml_prod.network_id
  managed_services_customer_managed_key_id = databricks_mws_customer_managed_keys.managed_services.customer_managed_key_id
  storage_customer_managed_key_id = databricks_mws_customer_managed_keys.storage.customer_managed_key_id
  private_access_settings_id = databricks_mws_private_access_settings.card_ml_prod.private_access_settings_id
}
```

## 9. Operational runbooks

- **Workspace deprovisioning** — graceful (drain jobs first) vs hard.
- **CMK rotation** — managed by AWS; verify workspaces don't break.
- **Region migration** — workspace bound to one control-plane region; multi-region = multi-workspace.

## 10. Pitfalls

- **Two-provider Terraform** complexity — easy to misconfigure.
- **CMK without correct grants** — workspace creation fails.
- **Missing private access settings** — workspace UI publicly accessible.
- **Direct S3 access to root bucket** — bypasses UC + Databricks audit trail.

## 11. Capital One lens

Probable setup:
- **Multi-account, multi-workspace** (per LOB × per env).
- **Terraform CI** for workspace lifecycle.
- **Audit logs to S3 → Datadog**.
- **Per-LOB CMKs** with 90-day rotation.
- **Slingshot** (their commercial product) likely used internally for Databricks cost optimization too.

## 12. Sanity check

1. What are the four MWS account-level resources required for a workspace?
2. Why are two Terraform providers (account vs workspace) needed?
3. What's in Databricks audit logs that's not in CloudTrail, and vice versa?
4. Why separate CMKs for workspace, managed services, and storage?
5. What does "private access settings" enforce?

## 13. Cross-references

- **Module 45** — Databricks-AWS architecture
- **Module 47** — networking (private access)
- **Module 50** — KMS deep
- **Module 56** — cost discipline

## Primary sources

- [`databricks_mws_api.html`](../../research_inputs/04_aws_for_ai_ml/downloads/databricks_on_aws/databricks_mws_api.html)
- Terraform Databricks provider docs (live)
- Research report: [`11_databricks_on_aws.md`](../../research_inputs/04_aws_for_ai_ml/11_databricks_on_aws.md)
