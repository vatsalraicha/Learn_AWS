# 17 — Cloud Composer (GCP)

## Why this module exists

GCP's managed Airflow. The Composer 3 generation (GA April 2024) brought serverless components and simpler networking. This module covers both Composer 2 and 3.

---

## 1. Composer 2 vs Composer 3

| | Composer 2 | Composer 3 |
|---|---|---|
| Architecture | GKE Autopilot cluster | Serverless components |
| Scaling | Up + down within env | Smaller baseline, scales to near-zero |
| Identity | Workload Identity | Workload Identity Federation (new model) |
| Networking | Private IP / Public | Private Service Connect (PSC) |
| Custom images | Limited | Full custom container option |
| Pricing | Per-env infra | Per vCPU-hour + storage |

For new deployments in 2025-2026: **Composer 3**.

---

## 2. Architecture (Composer 3)

- Airflow components run in a Google-managed project (the **service producer project**).
- Connects to **your** project via PSC.
- DAG bucket in **your** project (GCS).
- Logs to **your** Cloud Logging.

Trade-off: opaque control plane vs predictable cost.

---

## 3. Supported Airflow versions

Composer 3 typically supports the latest 2-3 Airflow 2.x lines + early support for 3.0 (rolling). Confirm at quote.

---

## 4. Workload Identity Federation for Composer 3

Each Composer env binds a **Kubernetes service account** to a **GCP service account**:

```bash
gcloud composer environments update my-env --location us-central1 \
  --update-airflow-configs core-default_pool_task_slot_count=64

# To use a per-DAG GSA (Composer 3):
gcloud iam service-accounts add-iam-policy-binding \
  ml-tasks@my-proj.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-proj.svc.id.goog[composer-user-workloads/airflow-worker]"
```

Tasks now run as the per-task GSA — no JSON keys.

---

## 5. DAG storage — GCS

Composer auto-provisions a GCS bucket per env:

- `dags/` — auto-synced.
- `plugins/` — synced on env update.
- `data/` — your scratch area.

Pattern: CI pushes DAGs via `gsutil rsync` or `gcloud storage cp`. Sync is fast (~30s).

CMEK encryption on the bucket; bucket retention if required.

---

## 6. PyPI packages

```bash
gcloud composer environments update my-env --location us-central1 \
  --update-pypi-packages-from-file requirements.txt
```

Composer triggers a rolling image rebuild (~10-20 min). For custom system packages: use the **custom container image** option in Composer 3.

---

## 7. Secrets backend — GCP Secret Manager

```bash
gcloud composer environments update my-env --location us-central1 \
  --update-airflow-configs \
    secrets-backend=airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend,\
    secrets-backend_kwargs='{"connections_prefix":"airflow-connections","variables_prefix":"airflow-variables","project_id":"my-proj"}'
```

The Composer env's GSA needs `roles/secretmanager.secretAccessor` on the secrets.

---

## 8. Networking — private environments

Composer 3 with private IP:

```bash
gcloud composer environments create my-env --location us-central1 \
  --image-version composer-3-airflow-2.10.3 \
  --enable-private-environment \
  --enable-private-endpoint \
  --network my-vpc --subnetwork my-subnet
```

Connects via **Private Service Connect** — no need to peer VPCs. Cleaner than Composer 2's VPC-peering model.

For VPC-SC: place project in a service perimeter; Composer can be inside.

---

## 9. CMEK and at-rest encryption

Pass CMEK on environment create:

```bash
gcloud composer environments create my-env --location us-central1 \
  --kms-key projects/.../keyRings/.../cryptoKeys/composer
```

Applies to:
- GKE cluster (Composer 2) / control plane state.
- GCS DAG bucket.
- Cloud SQL metadata DB.
- Pub/Sub queue.

---

## 10. Logging — Cloud Logging

Default destination. Filter by logName + DAG ID. Export sinks to BigQuery / GCS for long-term retention. CMEK on log buckets.

---

## 11. Comparison vs MWAA

| | MWAA | Composer 3 |
|---|---|---|
| Pricing model | Per env-hour (fixed) | Per vCPU-hour (variable) |
| Idle cost | Always-on baseline | Scales to near-zero |
| Custom image | No | **Yes** |
| Airflow 3.0 support | No (2026-05) | Earlier |
| Private network | PRIVATE_ONLY mode | PSC-based |
| Secrets | AWS Secrets Manager | GCP Secret Manager |
| Region selection | Per env | Per env |
| Composer ergonomics | Fewer moving parts | More flexible |

For greenfield GCP shops: Composer 3 is the default. For multi-cloud: Astronomer Astro often wins on consistency.

---

## 12. The Composer 3 reference architecture

```
Project: data-platform
├── VPC (private subnets only)
├── Cloud Composer 3 env (private IP, PSC)
│   ├── GCS DAG bucket (CMEK)
│   ├── Cloud SQL metadata (CMEK)
│   ├── Workload Identity binding per task
│   ├── Secret Manager backend
│   └── Cloud Logging (CMEK)
│
└── Org Policy: 
    - disable SA JSON keys
    - require CMEK on all resources
    - VPC-SC perimeter
```

---

## Sanity check

1. Composer 2 vs Composer 3 — name two architectural differences.
2. How does Composer 3 connect to customer projects?
3. Custom container images — Composer 3 supports them; Composer 2?
4. Composer's auto-provisioned GCS bucket — what lives there and at what sync cadence?
5. CMEK on Composer covers what at-rest stores?

---

## Sources

- [Cloud Composer docs](https://cloud.google.com/composer/docs)
- [Composer 3 overview](https://cloud.google.com/composer/docs/composer-3/composer-overview)
- [Composer Workload Identity](https://cloud.google.com/composer/docs/composer-3/use-workload-identity)
- [Composer Secret Manager backend](https://cloud.google.com/composer/docs/composer-3/configure-secret-manager)
- [Composer pricing](https://cloud.google.com/composer/pricing)

→ Next: [18 — Azure Managed Airflow](18_azure_managed_airflow.md)
