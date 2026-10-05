# 19 — Astronomer (Astro) + self-hosted on-prem (Helm)

## Why this module exists

Two non-cloud-native managed paths: **Astronomer Astro** (the dominant commercial Airflow vendor) and **self-host on K8s via Helm**. For regulated finance that outgrows MWAA/Composer/Azure Managed: this is where you go.

---

## 1. Astronomer (Astro) — the offerings

| Offering | Hosted by | Data plane | Use case |
|---|---|---|---|
| **Astro Hosted** | Astronomer | Astronomer's AWS account | Fastest start; multi-tenant SaaS |
| **Astro Hybrid** | Astronomer (control plane) | **Customer's** AWS / GCP / Azure account | Regulated data stays in your VPC |
| **Astro Software** | Customer | Customer | Fully self-host with Astronomer's Helm chart |

For regulated finance: **Astro Hybrid**. Control plane in Astronomer; workers + DAGs + data in your cloud account.

---

## 2. Why Astro

- **Latest Airflow versions** — fast track to 2.10+, 3.0+ (often weeks faster than MWAA).
- **Astro CLI** — local dev with `astro dev start` (Docker Compose stack).
- **Image-based deploys** — `astro deploy` builds a Docker image with your DAGs + deps, pushes to Astro registry, rolls out. Cleaner than git-sync.
- **Astro Workspaces + Deployments** — multi-team, multi-env hierarchy.
- **Astro Observe** — built-in observability.
- **Astro Cloud IDE** — web-based DAG authoring (optional).

---

## 3. Astro CLI workflow

```bash
# Initialize project
astro dev init
# Adds: Dockerfile, requirements.txt, packages.txt, dags/, plugins/

# Local dev
astro dev start                  # spawns Docker Compose: Postgres + Airflow

# Deploy
astro login
astro deploy <deployment-id>     # builds image, pushes, rolls out
```

Image-based deploys mean a deploy is immutable — promotion = digest pin. Cleaner than MWAA's bucket model.

---

## 4. Astro pricing

Astro Units (AU) — each ~ $0.30-0.50/hr. A dev env: ~$0.35/hr → ~$255/mo. A prod env: $1500-5000/mo minimum.

More expensive than MWAA/Composer for steady state. Justified by:
- Newer Airflow earlier.
- Better observability.
- Image-based deploy.
- 24/7 support.

For Capital One: budget exists; Astro Hybrid is plausible if MWAA's limits bite.

---

## 5. Self-host with Helm — the alternative

For the budget-conscious or already-on-K8s shop:

```bash
helm install airflow apache-airflow/airflow -n airflow --create-namespace -f values.yaml
```

Module 15 covered the patterns. Recap of the operational burden:

- HA Postgres (CloudNativePG / RDS / managed).
- Redis (if Celery; not needed for K8sExecutor).
- DAG sync (git-sync sidecar OR image-baked).
- Vault for secrets.
- KEDA for autoscaling.
- Falco / runtime security.
- Velero for backup.
- Cert-manager for ingress TLS.
- Monitoring stack (Prom / Grafana / Loki / OTel).

You operate every layer. For mature ops teams: cheaper. For small teams: false economy — Astro or MWAA wins.

---

## 6. Astro Hybrid for regulated finance

```
Customer AWS account (regulated VPC)
├── EKS cluster (operated by Astronomer)
│   ├── KubernetesExecutor
│   ├── DAGs run as K8s pods (per-task IRSA)
│   ├── Astro images with your code
│   └── Vault / Secrets Manager backend
│
├── S3 buckets (CMK)
├── Snowflake PrivateLink
└── Databricks PrivateLink

Astronomer SaaS (cross-account)
├── Control plane: API, UI, deployment orchestration
└── Observability platform
```

Customer's data never leaves their VPC. Control plane handles UI + Deployment lifecycle. Best of both worlds when budget allows.

---

## 7. The on-prem path (air-gapped)

If you can't even use Astro Hybrid (regulated air-gap):

- **Astro Software**: fully self-host with Astronomer's Helm chart + on-prem Postgres + on-prem registry.
- **Apache Helm chart**: pure OSS, no Astronomer.

Air-gap requirements:
- Internal git mirror for DAGs.
- Internal PyPI mirror for deps.
- Internal Docker registry (Harbor).
- Vault for secrets.
- All Airflow Helm-chart image pulls from internal registry.

---

## 8. The decision matrix

| Need | Pick |
|---|---|
| AWS-native, willing to live with MWAA's limits | **MWAA** |
| Need latest Airflow + better dev UX | **Astro Hybrid on AWS** |
| GCP-native | **Composer 3** |
| Azure + already on Fabric | **Fabric Apache Airflow Jobs** |
| Azure + not Fabric | **Astro on Azure** or self-host |
| Air-gapped regulated | **Astro Software** or self-host Helm |
| Tiny team, big budget | **Astro Hosted** |
| Tiny team, small budget | **Self-host on managed K8s** |

For Capital One: MWAA covers most needs; Astro Hybrid for teams that need 3.0 or richer dev UX earlier.

---

## 9. Migration paths

- **MWAA → Astro Hybrid on AWS**: lift-and-shift DAGs; rewire connections; migrate secrets backend (typically same Secrets Manager). Days.
- **Composer 2 → Composer 3**: in-place upgrade via gcloud; some breaking changes around custom container. Weeks.
- **Self-host → Astro Hybrid**: image-based deploy migration; Astro takes over operations.
- **2.x → 3.0**: regardless of host, see module 31 (Migration).

---

## Sanity check

1. Astro Hosted vs Astro Hybrid vs Astro Software — which is right for "regulated data must stay in our VPC"?
2. Astro's deploy model is image-based. Why is that an upgrade over MWAA's S3-bucket-upload?
3. Self-host Helm — list five operational responsibilities you take on.
4. For an air-gapped shop, what's the deployment path?
5. When does Astro Hybrid beat MWAA for Capital One?

---

## Sources

- [Astronomer Astro docs](https://docs.astronomer.io/astro/)
- [Astro CLI](https://docs.astronomer.io/astro/cli/install-cli)
- [Astro Hybrid](https://docs.astronomer.io/astro/hybrid-overview)
- [Apache Airflow Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/)

→ Next: [20 — DWH integrations](20_dwh_integrations.md)
