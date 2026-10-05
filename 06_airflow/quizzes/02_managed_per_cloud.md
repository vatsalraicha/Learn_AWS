# Quiz — Part D: Managed Airflow per cloud (modules 16-19)

The user's explicit ask material.

---

## Section 1 — MWAA (module 16)

1. MWAA environment classes — what does mw1.large cost roughly per month at baseline?
2. PRIVATE_ONLY webserver mode — how do humans reach the UI?
3. Why does the S3 DAG bucket REQUIRE versioning?
4. requirements.txt constraints — what URL must you reference, and what does it prevent?
5. Execution role vs (separately) per-task IAM in MWAA — why split?
6. As of mid-2026, MWAA supports Airflow 3.0?
7. When do you outgrow MWAA? List three signals.

## Section 2 — Composer (module 17)

8. Composer 2 vs Composer 3 — name two architectural differences.
9. Composer 3 uses what for connecting to customer projects?
10. CMEK on Composer covers what at-rest stores?

## Section 3 — Azure (module 18)

11. ADF Workflow Orchestration Manager status as of end of 2025?
12. Fabric Apache Airflow Jobs uses what executor?
13. DAG sync model — how does it differ from MWAA?

## Section 4 — Astronomer + self-host (module 19)

14. Astro Hosted vs Astro Hybrid — which fits "regulated data must stay in our VPC"?
15. Astro CLI workflow — three commands.
16. Self-host Helm — list five things you must operate yourself.
17. Air-gapped path — Astro Software vs Apache Helm chart?

---

## Answer key

1. `mw1.large` at ~$1.59/hr × 730 hrs ≈ **$1,160/mo baseline**, plus workers + metadata DB IO. Realistic ~$1,500-2,500/mo total.

2. Via VPN, Direct Connect, or a Bastion host inside the VPC. Zero-trust gateway (Verified Access) is increasingly the path.

3. MWAA tracks versioned objects for `plugins.zip` and `requirements.txt` — without versioning, MWAA cannot pin to a specific deploy.

4. `https://raw.githubusercontent.com/apache/airflow/constraints-X.Y.Z/constraints-3.X.txt`. Prevents pip from wildly resolving deps and breaking the environment.

5. Execution role is what MWAA itself uses (image pull, log push, secret fetch). Per-task IAM is what DAGs use for data access (S3, Snowflake, Databricks). Splitting follows least-privilege.

6. **No.** As of mid-2026, MWAA does not yet support Airflow 3.0. Confirm at quote time — AWS adds support on a delayed cadence.

7. Need K8sExecutor (MWAA is Celery-only); need Airflow 3.0; cannot tolerate plugin-restart latency; need custom OS packages; need to shell into workers.

8. Composer 2: GKE Autopilot-based. Composer 3: serverless components + control plane outside customer project + PSC networking + scale-to-near-zero baseline.

9. **Private Service Connect (PSC)** — no VPC peering needed.

10. GKE cluster state, GCS DAG bucket, Cloud SQL metadata DB, Pub/Sub queues. Everything that touches data.

11. **Retiring Dec 31, 2025.** Migrate to Fabric Apache Airflow Jobs (or Astro on Azure).

12. **KubernetesExecutor**, on Microsoft-managed AKS.

13. Azure: **git-sync** from Azure DevOps / GitHub. MWAA: S3-bucket upload. Azure's model is closer to modern best practice.

14. **Astro Hybrid.** Control plane in Astronomer's cloud; data plane (workers, DAGs, secrets) in your VPC.

15. `astro dev init` (scaffold), `astro dev start` (local Docker), `astro deploy` (image-build + push + roll-out).

16. HA Postgres; Redis (if Celery); DAG sync (git-sync sidecar / image-baked); Vault for secrets; KEDA autoscaling; Falco for runtime security; Velero for backup; cert-manager + ingress TLS; OIDC for auth; observability (Prom/Grafana/Loki); patch cadence; upgrades.

17. Astro Software: same Helm chart as Astro Hybrid but fully customer-operated. Apache Helm chart: pure OSS, no Astronomer sub fee. Astro Software gives you Astro CLI + Astronomer-provided images + support; Apache chart gives you raw bits.
