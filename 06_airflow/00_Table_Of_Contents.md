# Topic 06 — Table of Contents

> Master index. Use this to navigate; use [`README.md`](README.md) for the why-and-how-to-read-this overview.

## Part A — Airflow fundamentals
1. [History & landscape — why Airflow, where it fits, where it doesn't](01_history_landscape.md)
2. [Core concepts — DAG, Task, Operator, Sensor, Hook, Connection, Variable, XCom, Pool, Dataset](02_core_concepts.md)
3. [Architecture — Webserver, Scheduler, Triggerer, Workers, Metadata DB, DAG storage](03_architecture.md)
4. [Executors deep — Sequential / Local / Celery / Kubernetes / CeleryKubernetes / Edge](04_executors.md)
5. [DAG authoring — TaskFlow, dynamic task mapping, deferrable operators, setup/teardown](05_dag_authoring.md)
6. [Scheduling deep — logical date, data interval, timetables, catchup, backfill, Datasets/Assets](06_scheduling.md)

## Part B — Sensors, secrets, and security
7. [Sensors & triggers — poke vs reschedule vs deferrable](07_sensors_triggers.md)
8. [Connections, Variables, and Secrets Backends](08_secrets_backends.md)
9. [**Securing Airflow** — RBAC, Auth Manager, FAB, OIDC, audit logs](09_securing_airflow.md)
10. [**Networking Airflow** — private webserver, mTLS, VPC endpoints, egress controls](10_networking.md)

## Part C — Data flow, lineage, observability
11. [XCom & data passing — limits, custom XCom backend, anti-patterns](11_xcom_data_passing.md)
12. [Data-flow design — idempotency, hash-based skip, dataset-driven scheduling](12_data_flow_design.md)
13. [Lineage with OpenLineage — Marquez, Atlan/DataHub, Unity Catalog interop](13_lineage_openlineage.md)
14. [Observability — StatsD, Prometheus, OpenTelemetry, log handlers per cloud](14_observability.md)

## Part D — Managed Airflow per cloud
15. [Airflow on Kubernetes — KubernetesExecutor, KubernetesPodOperator, KEDA](15_airflow_on_k8s.md)
16. [**MWAA — AWS Managed Workflows for Apache Airflow**](16_mwaa_aws.md)
17. [**Cloud Composer — GCP**](17_composer_gcp.md)
18. [**Azure Managed Airflow** — ADF + Fabric](18_azure_managed_airflow.md)
19. [**Astronomer + self-hosted on-prem**](19_astro_and_onprem.md)

## Part E — Integrations
20. [Snowflake + Redshift + BigQuery + Synapse — DWH operator patterns](20_dwh_integrations.md)
21. [Databricks integration](21_databricks_integration.md)
22. [Spark family — EMR, EMR Serverless, EMR-on-EKS, Dataproc, Glue](22_spark_emr_dataproc_glue.md)
23. [ML platform operators — SageMaker, Vertex AI, Azure ML, MLflow, KFP](23_ml_platforms.md)
24. [Airflow + dbt — Astronomer Cosmos](24_dbt_airflow.md)
25. [Alternative orchestrators — Prefect, Dagster, Argo, Step Functions, Databricks Workflows](25_alternatives.md)

## Part F — Production, scale, future
26. [CI/CD for DAGs](26_cicd_dags.md)
27. [SRE — failure modes & on-call playbook](27_sre_failure_modes.md)
28. [Cost & scaling — KEDA, deferrable, right-sizing](28_cost_scaling.md)
29. [Multi-tenancy patterns](29_multi_tenancy.md)
30. [**Airflow 3.0 deep — Task SDK, deadlines, multi-cluster, asset-centric, UI rewrite**](30_airflow_3.md)
31. [Migration & version strategy](31_migration.md)
32. [Certifications](32_certifications.md)

## Companion files
- [README.md](README.md) — topic overview
- [FACTS.md](FACTS.md) — atomic citable facts with last-verified dates
- [quizzes/](quizzes/) — per-part quizzes
- [code/](code/) — example DAGs, Helm fragments, Terraform per cloud
