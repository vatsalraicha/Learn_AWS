# 16 — MWAA: Amazon Managed Workflows for Apache Airflow

> *"For Capital One's AWS-native posture, MWAA + PRIVATE_ONLY + Secrets Manager backend + KMS + K8sPodOperator-to-EKS is the conventional answer."*

## Why this module exists

MWAA is the AWS-native managed Airflow. This module is the depth on its environment classes, networking, IAM, secrets, and limits. Critical for the Capital One target.

---

## 1. The MWAA architecture

- Fargate-based (workers run as Fargate tasks).
- VPC-injected — runs in YOUR VPC; reaches YOUR private resources.
- Hidden control plane (AWS-managed RDS Postgres, MQ for Celery, scheduler).
- Webserver: separate Fargate task.
- Triggerer: supported since 2.7+ MWAA versions.

You don't manage K8s; AWS handles it.

---

## 2. Environment classes (2026)

| Class | vCPU / Memory | $/hr (us-east-1) | Use case |
|---|---|---:|---|
| `mw1.small` | 1 / 2 GB | ~$0.49 | Dev / very small |
| `mw1.medium` | 2 / 4 GB | ~$0.79 | Small teams |
| `mw1.large` | 4 / 8 GB | ~$1.59 | Standard prod |
| `mw1.xlarge` | 8 / 16 GB | ~$2.97 | Many DAGs |
| `mw1.2xlarge` | 16 / 32 GB | ~$5.78 | Largest |

Plus the metadata DB storage + worker autoscaling counts. Pricing is per-environment-hour; minimum spend even when idle.

For comparison: `mw1.large` × 730 hrs = ~$1,160/mo baseline + workers.

---

## 3. Supported Airflow versions

MWAA supports a rolling subset of Airflow 2.x. As of 2026-05: 2.8.1, 2.9.2, 2.10.1, 2.10.3 typically.

**MWAA does NOT support Airflow 3.0 yet** as of mid-2026 — confirm at quote time. For 3.0, alternatives: self-host on EKS or Astronomer.

---

## 4. VPC requirements

MWAA injects into your VPC. Requirements:

- **Two private subnets in different AZs**.
- **Route to internet** (NAT GW) OR all required services via **VPC endpoints**.
- **Security group** allowing intra-environment communication.

For regulated finance: VPC endpoints (no NAT). The endpoints needed:

- `com.amazonaws.<region>.s3` (Gateway endpoint — for DAG bucket).
- `com.amazonaws.<region>.ecr.api` + `.ecr.dkr` (for image pulls if using K8sPodOperator).
- `com.amazonaws.<region>.secretsmanager`.
- `com.amazonaws.<region>.logs` (CloudWatch).
- `com.amazonaws.<region>.kms`.
- `com.amazonaws.<region>.monitoring` (CloudWatch metrics).
- `com.amazonaws.<region>.sqs` (for the internal queue).
- Plus per-service endpoints (Snowflake PrivateLink, etc.).

---

## 5. Webserver access modes

- **`PUBLIC_ONLY`** — webserver reachable via internet (with IAM auth).
- **`PRIVATE_ONLY`** — webserver reachable only from VPC. Requires Direct Connect / VPN / VPN-via-bastion for human access.

For regulated finance: `PRIVATE_ONLY` + Bastion / zero-trust gateway.

---

## 6. DAG storage — S3

MWAA reads DAGs from a designated S3 bucket:

- `dags/` folder — DAG `.py` files (synced ~30s).
- `plugins.zip` — custom operators/hooks (synced on env restart).
- `requirements.txt` — PyPI deps (synced on env restart).
- `startup.sh` (2.10+) — custom startup script (synced on env restart).

**Versioning MUST be enabled** on the bucket. MWAA pins to a specific version per `requirements.txt` / `plugins.zip` upload.

CMK encryption on the bucket. KMS key policy must allow the MWAA execution role.

---

## 7. requirements.txt — the constraints rule

```
# requirements.txt
--constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.3/constraints-3.11.txt"

apache-airflow-providers-snowflake==5.5.1
apache-airflow-providers-databricks==6.7.0
dbt-core==1.8.0
dbt-snowflake==1.8.0
astronomer-cosmos==1.5.0
```

Must reference the constraints URL for the exact Airflow version. Otherwise pip resolves wildly. MWAA will reject builds that don't pin to Airflow's constraints.

No system-level packages (no apt-install). For C libraries (e.g., psycopg2 wheels): use the wheel built for manylinux; works.

---

## 8. plugins.zip

Custom Airflow plugins: operators, hooks, macros. Zipped, uploaded. Synced on env restart (~5-20 min).

Use sparingly. Prefer:
- Provider packages from PyPI (via requirements.txt).
- Custom code in `dags/` (DAG-private classes).

---

## 9. IAM — execution role vs worker permissions

Two roles:

- **Execution role** — the role MWAA itself uses (S3 access to DAG bucket, secrets, KMS, logs, ECR for K8sPodOperator).
- **Task role** — what DAG tasks actually use to call AWS APIs.

Common pattern: same role for both, scoped tight. Or split for least privilege.

```json
// Execution role - example minimum
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["airflow:*"], "Resource": "*"},
    {"Effect": "Allow", "Action": ["s3:GetObject*","s3:GetBucket*","s3:List*"],
     "Resource": ["arn:aws:s3:::myorg-mwaa-dags-prod","arn:aws:s3:::myorg-mwaa-dags-prod/*"]},
    {"Effect": "Allow", "Action": "kms:Decrypt",
     "Resource": "arn:aws:kms:us-east-1:123:key/<cmk>"},
    {"Effect": "Allow", "Action": "secretsmanager:GetSecretValue",
     "Resource": "arn:aws:secretsmanager:us-east-1:123:secret:airflow/*"},
    {"Effect": "Allow", "Action": ["logs:CreateLogStream","logs:PutLogEvents"],
     "Resource": "arn:aws:logs:us-east-1:123:log-group:airflow-*"}
  ]
}
```

For DAGs that call SageMaker / Snowflake / Databricks: add those permissions on the role. Or use **AssumeRole** to a per-DAG role from within tasks.

---

## 10. Secrets Manager backend

```python
# Set as env var in MWAA UI:
AIRFLOW__SECRETS__BACKEND="airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend"
AIRFLOW__SECRETS__BACKEND_KWARGS='{"connections_prefix":"airflow/connections","variables_prefix":"airflow/variables"}'
```

Now `conn_id=snowflake_prod` → `airflow/connections/snowflake_prod` in Secrets Manager.

This is the **mandatory pattern** for regulated MWAA. Don't put real credentials in the MWAA UI's Connections tab.

---

## 11. Logging — CloudWatch

MWAA ships 5 log groups:

- `airflow-<env>-DAGProcessing`
- `airflow-<env>-Scheduler`
- `airflow-<env>-WebServer`
- `airflow-<env>-Worker`
- `airflow-<env>-Task`

Enable per log group; `INFO` is the floor; `DEBUG` is expensive (lots of bytes). Encrypt with CMK; lifecycle to Glacier.

For volume: a busy production env can produce $500-1000/mo in CloudWatch costs if not tuned.

---

## 12. Scaling

MWAA autoscales workers between 1 and `MaxWorkers` (set on env). Triggerer is fixed.

Worker count scales based on queued tasks. Cold worker startup ~2 min, so very short DAGs see scheduling lag. For consistent throughput: set `MinWorkers` > 1.

---

## 13. The Capital One MWAA pattern

```
Capital One AWS account (regulated VPC)
│
├── MWAA env (mw1.large)
│   ├── PRIVATE_ONLY webserver (reached via Bastion / Verified Access)
│   ├── S3 DAG bucket (CMK + versioning + VPC GW endpoint)
│   ├── Execution role: Secrets Manager + KMS + logs + ECR-pull
│   ├── Secrets Backend: airflow/connections/* in Secrets Manager
│   ├── No NAT — all access via VPC endpoints
│   └── Logs → CloudWatch (CMK)
│
├── DAGs:
│   - Snowflake ETL (SnowflakeOperator with conn from Secrets Mgr)
│   - Databricks job trigger (DatabricksRunNowOperator)
│   - SageMaker pipeline trigger (PythonOperator → SageMaker SDK)
│   - K8sPodOperator → EKS cluster (heavy ML work)
│
└── Cloud Custodian policies:
    - "MWAA env must be PRIVATE_ONLY in prod"
    - "DAG bucket must have CMK + versioning"
    - "MWAA execution role: no wildcards"
```

---

## 14. Limitations of MWAA

- No Airflow 3.0 yet.
- No shell into the workers / scheduler (debugging via logs + env restart).
- No custom Postgres / metadata DB tuning.
- No Celery customization.
- Plugin sync is slow (env restart required for `plugins.zip` / `requirements.txt` changes).
- Triggerer scaling is fixed (no horizontal scaling).
- No per-DAG resource limits — pools and `max_active_runs` only.

When you outgrow MWAA: Astro Hybrid (Astronomer in your VPC) or self-host on EKS.

---

## 15. Cost optimization

- `MinWorkers` = 1, `MaxWorkers` per peak.
- Right-size environment class — `mw1.medium` is enough for many shops.
- Aggressive log rotation; turn off DEBUG.
- Deferrable operators reduce worker hours dramatically.
- K8sPodOperator into spot EKS nodes for the actual heavy lifting.

---

## Sanity check

1. PRIVATE_ONLY webserver — how do humans reach it?
2. The S3 DAG bucket must have what setting enabled, and why?
3. requirements.txt constraints — why does MWAA enforce them?
4. Two IAM roles in MWAA — what does each cover?
5. Secrets Manager backend wiring — what env vars do you set in MWAA?
6. When do you outgrow MWAA?

---

## Sources

- [MWAA docs](https://docs.aws.amazon.com/mwaa/)
- [MWAA pricing](https://aws.amazon.com/managed-workflows-for-apache-airflow/pricing/)
- [MWAA networking](https://docs.aws.amazon.com/mwaa/latest/userguide/networking-about.html)
- [MWAA + Secrets Manager](https://docs.aws.amazon.com/mwaa/latest/userguide/connections-secrets-manager.html)
- [MWAA versions](https://docs.aws.amazon.com/mwaa/latest/userguide/airflow-versions.html)

→ Next: [17 — Cloud Composer (GCP)](17_composer_gcp.md)
