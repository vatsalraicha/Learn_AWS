# Topic 06 — FACTS.md (Apache Airflow)

> Atomic, citable facts. Provider package versions, MWAA env classes, Composer GA/EOL dates, Airflow 3 release, exam metadata.
>
> **Format:** one fact per line, citation in square brackets, last-verified date.
>
> **Last updated:** 2026-05-21 (seed)

---

## Airflow core release history

- **Apache Airflow** open-sourced by Airbnb **June 2015**; Apache Incubator **March 2016**; **Top-Level Project January 2019**. [Source: airflow.apache.org/history; ASF press release] [Verified 2026-05-21]
- **Airflow 2.0** released **December 17, 2020**. TaskFlow API, scheduler HA (multiple active schedulers), DAG serialization, smart sensors (later retired). [Source: airflow.apache.org/blog/airflow-two-point-oh-is-here] [Verified 2026-05-21]
- **Airflow 2.3** (Apr 2022): dynamic task mapping. **2.4** (Sep 2022): Datasets + data-driven scheduling. **2.5** (Dec 2022): Object Storage abstraction. **2.6** (Apr 2023): callbacks improvements. **2.7** (Aug 2023): setup/teardown, cluster activity dashboard. **2.8** (Dec 2023): listener API, Object Storage XCom backend. **2.9** (Apr 2024): Dataset events UI, OpenLineage v2.x. **2.10** (Aug 2024): DAG-level dataset events, hybrid executors. [Source: airflow.apache.org changelogs] [Verified 2026-05-21]
- **Airflow 3.0** released **April 22, 2025** at Airflow Summit. Headline changes: **Task SDK** (task execution decoupled from scheduler DB), **multi-cluster scheduler**, **React-based UI** (replaces FAB UI), **deadlines** (replaces SLA misses), **Assets** (renamed from Datasets), **DAG versioning**, multiple breaking changes from 2.x. [Source: airflow.apache.org/blog 2025; Airflow Summit 2025 keynote] [Verified 2026-05-21]
- **Python support**: Airflow 2.10 supports 3.8–3.12; Airflow 3.0 supports 3.9–3.12. [Source: airflow.apache.org/docs] [Verified 2026-05-21]

## Architecture limits & defaults

- **XCom soft warning** at **48 KB** (default for `xcom_max_size`); **hard ceiling** depends on metadata DB BLOB column — PostgreSQL `bytea` ~1 GB, MySQL `LONGBLOB` ~4 GB but slow. **Production target: keep XCom < 1 MB.** [Source: airflow.apache.org/docs configuration reference; PostgreSQL bytea docs] [Verified 2026-05-21]
- **Default `sql_alchemy_pool_size` = 5**; production typically 15–30 with `pool_pre_ping = True`. [Source: airflow.apache.org/docs] [Verified 2026-05-21]
- **`scheduler_heartbeat_sec` default = 5s**. Heartbeat timeout `scheduler_health_check_threshold` default 30s. [Source: airflow.apache.org/docs] [Verified 2026-05-21]
- **Multiple schedulers** supported since Airflow 2.0; uses Postgres row-level locks (`SELECT FOR UPDATE SKIP LOCKED`). MySQL requires 8.0+ with same locks. [Source: airflow.apache.org/docs HA scheduler] [Verified 2026-05-21]
- **Triggerer** process introduced in 2.2 for deferrable operators. Async (asyncio) — one process handles thousands of triggers. [Source: AIP-40, Airflow docs] [Verified 2026-05-21]

## Security baseline

- **`fernet_key`** encrypts Connection passwords and Variables in metadata DB. **Rotation** via `airflow rotate-fernet-key` after appending new key to `AIRFLOW__CORE__FERNET_KEY`. [Source: airflow.apache.org/docs/apache-airflow/stable/security] [Verified 2026-05-21]
- **`webserver_secret_key`** signs session cookies — MUST be identical across webserver replicas. [Source: airflow.apache.org/docs] [Verified 2026-05-21]
- **Auth Manager** abstraction GA 2.8 (Dec 2023). FAB Auth Manager is default. **AWS Auth Manager** plugs IAM-based access. **Simple Auth Manager** is for testing only. [Source: airflow.apache.org/docs auth-manager] [Verified 2026-05-21]
- **FAB built-in roles**: Admin, Op, User, Viewer, Public. Custom roles + per-DAG `access_control` field for granular control. [Source: airflow.apache.org/docs security/access-control] [Verified 2026-05-21]
- **`expose_config = False`** (recommended): prevents UI from showing airflow.cfg contents which may include secrets. [Source: airflow.apache.org/docs configuration] [Verified 2026-05-21]
- **Known CVE-2020-11978** — Example DAG `example_trigger_target_dag` RCE; example DAGs should be disabled (`load_examples=False`) in any non-dev environment. [Source: nvd.nist.gov; airflow security advisory] [Verified 2026-05-21]

## Secrets backends (built-in to provider packages)

- **AWS Secrets Manager + Parameter Store** via `apache-airflow-providers-amazon` (`SecretsManagerBackend`, `SystemsManagerParameterStoreBackend`). [Source: airflow.apache.org/docs/apache-airflow-providers-amazon] [Verified 2026-05-21]
- **GCP Secret Manager** via `apache-airflow-providers-google` (`CloudSecretManagerBackend`). [Source: airflow.apache.org/docs/apache-airflow-providers-google] [Verified 2026-05-21]
- **Azure Key Vault** via `apache-airflow-providers-microsoft-azure` (`AzureKeyVaultBackend`). [Source: airflow.apache.org/docs/apache-airflow-providers-microsoft-azure] [Verified 2026-05-21]
- **HashiCorp Vault** via `apache-airflow-providers-hashicorp` (`VaultBackend`). [Source: airflow.apache.org/docs/apache-airflow-providers-hashicorp] [Verified 2026-05-21]
- **Order of precedence**: Secrets Backend → Environment Variables (AIRFLOW_CONN_*, AIRFLOW_VAR_*) → Metadata DB. [Source: airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/connections] [Verified 2026-05-21]

## MWAA — Amazon Managed Workflows for Apache Airflow

- **GA**: November 24, 2020 (re:Invent 2020). [Source: aws.amazon.com/blogs Nov 2020] [Verified 2026-05-21]
- **Environment classes & pricing (us-east-1, 2026)**: mw1.small ~$0.49/hr, mw1.medium ~$0.79/hr, mw1.large ~$1.59/hr, mw1.xlarge ~$2.97/hr, mw1.2xlarge ~$5.78/hr (storage + metadata DB IO billed separately). [Source: aws.amazon.com/managed-workflows-for-apache-airflow/pricing] [Verified 2026-05-21]
- **Supported Airflow versions in MWAA** (2026-05): 2.8.1, 2.9.2, 2.10.1, **2.10.3** (latest GA). MWAA does **not** support Airflow 3.0 yet — confirm at quote time. [Source: docs.aws.amazon.com/mwaa/latest/userguide/airflow-versions.html] [Verified 2026-05-21]
- **Webserver access modes**: PUBLIC_ONLY (internet-accessible UI), PRIVATE_ONLY (VPC-only, requires VPN/Direct Connect). [Source: docs.aws.amazon.com/mwaa] [Verified 2026-05-21]
- **DAG storage**: S3 bucket with **versioning enabled (mandatory)**. `dags/`, `plugins.zip`, `requirements.txt`, `startup.sh`. [Source: docs.aws.amazon.com/mwaa] [Verified 2026-05-21]
- **`requirements.txt` constraints**: must include the Airflow constraints URL (`-c https://raw.githubusercontent.com/apache/airflow/constraints-X.Y.Z/constraints-3.X.txt`); no system packages, no compiled deps not on PyPI. [Source: docs.aws.amazon.com/mwaa/latest/userguide/working-dags-dependencies] [Verified 2026-05-21]
- **Triggerer process**: supported in MWAA for Airflow 2.7+ environments. [Source: docs.aws.amazon.com/mwaa] [Verified 2026-05-21]
- **CloudWatch log groups**: webserver, scheduler, worker, task, DAGProcessor. [Source: docs.aws.amazon.com/mwaa] [Verified 2026-05-21]

## Cloud Composer (GCP)

- **GA**: 2018. [Source: cloud.google.com/composer history] [Verified 2026-05-21]
- **Composer 2**: GKE Autopilot-based, GA 2021. **Composer 3**: GA April 2024; serverless control-plane components, PSC networking, smaller environments, scale-to-near-zero. [Source: cloud.google.com/blog Apr 2024] [Verified 2026-05-21]
- **Composer 1 EOL**: scheduled 2024–2025; users migrated to Composer 2 then 3. [Source: cloud.google.com/composer/docs/composer-1] [Verified 2026-05-21]
- **Composer 3 Workload Identity Federation**: KSA-to-GSA binding via annotations; no JSON keys. [Source: cloud.google.com/composer/docs/composer-3/use-workload-identity] [Verified 2026-05-21]
- **DAG storage**: GCS bucket auto-provisioned per environment, `dags/`, `plugins/`, `data/`. [Source: cloud.google.com/composer/docs] [Verified 2026-05-21]
- **Composer 3 pricing**: per-vCPU-hour for environment components + storage. Cheaper baseline than Composer 2 for low-utilization envs. [Source: cloud.google.com/composer/pricing] [Verified 2026-05-21]

## Azure Managed Airflow (Workflow Orchestration Manager)

- **GA**: ADF **Workflow Orchestration Manager** GA April 2024; also surfaces in **Microsoft Fabric Data Factory** as "Apache Airflow Jobs" (preview/GA 2024–2025 — confirm at quote time). [Source: learn.microsoft.com/azure/data-factory/airflow-overview] [Verified 2026-05-21]
- **DAG sync model**: git-sync from Azure DevOps / GitHub repo (different from MWAA's S3-blob upload). [Source: learn.microsoft.com/azure/data-factory] [Verified 2026-05-21]
- **Auth**: Azure AD / Entra ID via FAB OIDC; per-env Managed Identity or Service Principal for DAG-side auth. [Source: learn.microsoft.com/azure/data-factory] [Verified 2026-05-21]
- **Key Vault Backend** wiring documented. [Source: learn.microsoft.com/azure/data-factory] [Verified 2026-05-21]

## Astronomer

- **Astronomer** founded 2018; Astro Cloud platform GA. **Astro Hosted** (multi-tenant SaaS) and **Astro Hybrid** (data-plane in customer cloud account) are the two flavors. [Source: astronomer.io/product] [Verified 2026-05-21]
- **Astro Runtime** = Apache Airflow + Astronomer additions (extra providers, smart caching, better logging defaults). Versioned independently. [Source: docs.astronomer.io/astro/runtime-image-architecture] [Verified 2026-05-21]
- **Astro CLI** (`astro`) — local dev via Docker, `astro dev start`, push via `astro deploy`. [Source: docs.astronomer.io/astro/cli/install-cli] [Verified 2026-05-21]
- **Astronomer Cosmos** — community library that renders dbt projects as Airflow tasks dynamically. [Source: astronomer.github.io/astronomer-cosmos] [Verified 2026-05-21]

## Lineage & observability

- **OpenLineage**: LF AI & Data project (incubation); 1.0 spec released Aug 2022. `openlineage-airflow` provider extracts lineage automatically for many operators. [Source: openlineage.io spec] [Verified 2026-05-21]
- **Marquez**: reference OpenLineage backend. LF AI & Data project. [Source: marquezproject.ai] [Verified 2026-05-21]
- **OpenTelemetry support**: GA in Airflow 2.9 (Apr 2024) for traces and metrics. [Source: airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/otel.html] [Verified 2026-05-21]
- **StatsD metrics**: long-standing; emit to Datadog StatsD or to Prometheus via statsd_exporter. [Source: airflow.apache.org/docs] [Verified 2026-05-21]

## Provider packages (latest as of 2026-05-21 — confirm at quote)

- `apache-airflow-providers-amazon` 9.x line
- `apache-airflow-providers-google` 12.x line
- `apache-airflow-providers-microsoft-azure` 11.x line
- `apache-airflow-providers-snowflake` 6.x line
- `apache-airflow-providers-databricks` 7.x line
- `apache-airflow-providers-dbt-cloud` 4.x line
- `apache-airflow-providers-openlineage` 2.x line
- `apache-airflow-providers-cncf-kubernetes` 9.x line

[Source: pypi.org/project/apache-airflow-providers-*] [Verified 2026-05-21]

## Certifications

| Cert | Issuer | Cost USD | Format | Validity |
|---|---|---:|---|---|
| Apache Airflow Fundamentals | Astronomer | $150 | 60 min / 75 MCQ, online proctored | 2 years |
| DAG Authoring for Apache Airflow | Astronomer | $150 | 60 min / 75 MCQ, online proctored | 2 years |
| Astronomer Certification for Apache Airflow Operations | Astronomer | $150 | 60 min / 75 MCQ, online proctored | 2 years |

[Source: academy.astronomer.io] [Verified 2026-05-21]

- **AWS DEA-C01** covers MWAA basics (~5% of exam blueprint). [Source: aws.amazon.com/certification/certified-data-engineer-associate] [Verified 2026-05-21]
- **GCP Professional Data Engineer** covers Cloud Composer in the Orchestration domain. [Source: cloud.google.com/certification/data-engineer] [Verified 2026-05-21]
- **Azure DP-700 (Fabric Data Engineer)** covers Apache Airflow Jobs in Fabric. **DP-203** (legacy, retiring early 2026) covered ADF but not Airflow specifically. [Source: learn.microsoft.com/certifications] [Verified 2026-05-21]

## Capital One Airflow / orchestration signal

- Capital One **published MLOps spine** is **Step Functions + EKS + KServe + SageMaker + Glue + Snowflake/Databricks**. Airflow is used in some data-engineering teams for ETL into the warehouse but is **not** the dominant orchestrator. [Inference from public C1 tech blog + job postings — see Topic 04 CAPITAL_ONE.md] [Verified 2026-05-21]
- **Snowflake is heavily used at Capital One** for analytics + features; this is where Airflow most often appears in their stack (data engineering teams). [Source: capitalone.com/software; C1 + Snowflake partner case studies] [Verified 2026-05-21]
