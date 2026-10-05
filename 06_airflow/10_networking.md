# 10 — Networking Airflow: private webserver, mTLS, VPC endpoints, egress controls

## Why this module exists

Airflow's network surface is wider than most realize — webserver, scheduler, triggerer, workers, metadata DB, plus all the systems tasks talk to. Each is a control point.

---

## 1. The components' network roles

| Component | Inbound | Outbound |
|---|---|---|
| Webserver | UI clients (humans), API clients | Metadata DB, Secrets Backend |
| Scheduler | (none from outside) | Metadata DB, Secrets Backend, DAG storage, executor (Celery broker / K8s API) |
| Triggerer | (none from outside) | Metadata DB, External APIs being polled |
| Workers | (none) | All data sources (very wide!) |
| Metadata DB | Webserver, Scheduler, Triggerer, Workers | (storage only) |

**Workers have the widest egress surface** because they need to talk to Snowflake, Databricks, S3, EMR, custom APIs, Slack, etc. This is the blast radius if a worker is compromised.

---

## 2. Webserver: private deployment

Production Airflow webserver should:

- Have no public IP.
- Be behind an internal LB (AWS ALB, GCP Internal LB, Azure App Gateway).
- TLS terminated at the LB.
- OIDC auth (via oauth2-proxy if FAB-OIDC is insufficient).
- WAF in front for L7 protection.
- API rate limited.

For MWAA `PRIVATE_ONLY` mode: webserver only reachable via VPC. For Composer 3: Private IP environments with PSC. For Astro Hybrid: data-plane in customer VPC.

---

## 3. Scheduler / Worker egress

Workers need outbound:

- Cloud APIs (S3, KMS, Secrets Manager) → **VPC endpoints** (AWS) / **Private Google Access** (GCP) / **Private endpoints** (Azure).
- Data systems (Snowflake, Databricks) → **PrivateLink** (Snowflake, Databricks).
- Internal services (custom APIs) → VPC routing.

For a regulated shop: **default-deny outbound; allowlist per destination.**

```hcl
# AWS NSG / SG for worker
egress {
  from_port = 443
  to_port = 443
  protocol = "tcp"
  prefix_list_ids = [data.aws_prefix_list.s3.id]  # S3
}
egress {
  from_port = 443
  to_port = 443
  protocol = "tcp"
  cidr_blocks = ["10.50.0.0/16"]                  # internal services
}
```

---

## 4. Snowflake PrivateLink

For Snowflake from Airflow workers, **don't use the public Snowflake endpoint**. Configure Snowflake PrivateLink:

```
worker (VPC) → PrivateLink endpoint → Snowflake
```

Snowflake conn host: `myorg.privatelink.snowflakecomputing.com`. No internet egress for queries.

Same pattern for Databricks (PrivateLink), Confluent Cloud, MongoDB Atlas, etc.

---

## 5. mTLS

Webserver: TLS in (from clients). For mTLS within Airflow components: typically not needed for K8s-internal (service mesh handles east-west). For external API calls, mTLS at the boundary if the service requires it.

For Airflow REST API + machine clients: TLS + JWT auth; mTLS optional via API gateway.

---

## 6. Metadata DB networking

The metadata DB is the single most-sensitive backing store. Protect:

- Only reachable from scheduler/webserver/triggerer/worker subnets.
- TLS-enabled (Postgres `sslmode=require`).
- IAM auth where supported (RDS Postgres / Aurora IAM auth) — eliminates static DB password.
- Audit logging to CloudWatch / Cloud Logging / Log Analytics.
- Encrypted at rest with CMK.

For MWAA: AWS manages the DB; it's already private. For Composer: same. For self-host: own this.

---

## 7. DAG storage networking

Depending on deployment:

- **MWAA**: S3 bucket; access via S3 Gateway Endpoint.
- **Composer**: GCS bucket; Private Google Access.
- **Azure Managed Airflow**: git-sync from Azure DevOps / GitHub.
- **Self-host with git-sync**: outbound to git provider (allowlist `github.com` / your GitLab).
- **Self-host with image-baked**: pulls image; same path as image pulls.

For air-gapped self-host: internal git mirror; internal registry.

---

## 8. KubernetesExecutor — pod-level network

In K8sExecutor, each task pod has:

- Its own ServiceAccount (with IRSA / WIF / Entra MI).
- Its own NetworkPolicy (potentially).
- Pod-level SG (AWS).
- Mesh-injected sidecar (if Istio/Linkerd present).

This is **per-task network isolation**. You can have different DAGs with different egress allowlists. The strongest model.

---

## 9. The "Airflow on a private network" pattern

```
┌─────────────────────────────────────────────────────────────────┐
│ Private VPC (regulated zone)                                    │
│                                                                  │
│  ┌──────────────┐    ┌─────────────────┐                         │
│  │ Internal ALB │    │ EKS cluster     │                         │
│  │ (with WAF)   │    │ (private API)   │                         │
│  └──────┬───────┘    │                 │                         │
│         │            │  Airflow:       │                         │
│   ┌─────▼──────┐     │   - Webserver   │                         │
│   │ Webserver  │ ◀───┼─────────────────┘                         │
│   │ (FAB+OIDC) │     │   - Scheduler   │                         │
│   └────────────┘     │   - Triggerer   │                         │
│                      │   - Workers     │                         │
│                      └────────┬────────┘                         │
│                               │                                  │
│         ┌─────────────────────┼─────────────────────┐            │
│         │                     │                     │            │
│  ┌──────▼──────┐  ┌───────────▼─────────┐  ┌────────▼─────┐      │
│  │ RDS Postgres│  │ S3 (Gateway EP)    │  │ Snowflake    │      │
│  │ (TLS, CMK)  │  │ S3 / EFS / FSx     │  │ PrivateLink  │      │
│  └─────────────┘  │ Secrets Mgr (IFC)  │  └──────────────┘      │
│                   │ KMS (IFC)          │                         │
│                   └────────────────────┘                         │
└──────────────────────────────────────────────────────────────────┘
       ↑
       │ (only via Bastion / Zero-Trust gateway)
   Human admin
```

No internet egress. Human access via Bastion or zero-trust gateway (Cloudflare Access, Zscaler, AWS Verified Access).

---

## 10. Egress filtering for the worker — the Cloud Custodian–style policy

A common policy enforced by network firewall + IaC linting:

- Workers can egress to: KMS, Secrets Manager, S3 (specific prefixes), CloudWatch Logs, RDS (own DB), Snowflake (specific account), Databricks (own workspace).
- Workers CANNOT egress to: `0.0.0.0/0`, `169.254.169.254` (IMDS — task IAM role replaces), other accounts' resources, public DockerHub.

For a regulated FinOps + security shop: Falco rule + Cloud Custodian rule, both enforced.

---

## Sanity check

1. The worker is the widest egress surface. Why?
2. Snowflake PrivateLink — what does it replace and why?
3. Metadata DB networking — what's the lockdown checklist?
4. K8sExecutor + per-task NetworkPolicy — what does this give you that Celery doesn't?
5. Why is `169.254.169.254` blocked from worker pods?

---

## Sources

- [Snowflake PrivateLink](https://docs.snowflake.com/en/user-guide/private-snowflake-service)
- [Databricks PrivateLink](https://docs.databricks.com/security/network/classic/privatelink.html)
- [MWAA networking](https://docs.aws.amazon.com/mwaa/latest/userguide/networking-about.html)
- [Composer 3 networking](https://cloud.google.com/composer/docs/composer-3/configure-private-ip)

→ Next: [11 — XCom & data passing](11_xcom_data_passing.md)
