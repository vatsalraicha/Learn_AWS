# 18 — Azure Managed Airflow: ADF Workflow Orchestration Manager + Fabric Apache Airflow Jobs

## Why this module exists

Azure's managed Airflow story has shifted: the original **ADF Workflow Orchestration Manager** (WOM) launched 2023, was renamed/integrated into **Microsoft Fabric Data Factory** as "Apache Airflow Jobs" in 2024-2025, with WOM scheduled for retirement at the end of 2025. This module covers the transition and the current path.

---

## 1. The product line confusion

| Product | Status | Notes |
|---|---|---|
| **ADF Workflow Orchestration Manager** | **Retiring Dec 31, 2025** | Original managed Airflow in Azure Data Factory |
| **Fabric Data Factory Apache Airflow Jobs** | GA / preview late 2024-2025 | Successor — runs in Microsoft Fabric |
| **Astronomer Astro on Azure** | GA | Third-party managed (the practical alternative) |
| **Self-host on AKS** | DIY | Helm chart on AKS |

For new deployments: **Fabric Apache Airflow Jobs** OR **Astro on Azure** OR **self-host on AKS**. WOM is sunset.

---

## 2. Fabric Apache Airflow Jobs — architecture

- Runs inside **Microsoft Fabric** workspace.
- AKS-backed under the hood (managed by Microsoft).
- Uses **KubernetesExecutor** (not Celery).
- Tight integration with Fabric Data Factory pipelines, Lakehouse, OneLake.

For shops already on Fabric: this is the natural choice. For non-Fabric Azure shops: it's an awkward dependency.

---

## 3. DAG sync — git-based

Unlike MWAA's S3-blob upload model, Azure Managed Airflow syncs DAGs from a **git repository** (Azure DevOps, GitHub):

```
Azure DevOps repo
└── dags/
    ├── my_dag.py
    └── ...
```

Fabric polls the repo on a schedule. DAG changes propagate without an env restart.

This is **closer to the modern best practice** than MWAA's bucket-upload model.

---

## 4. Authentication

Microsoft Entra ID:
- UI auth via Entra (SSO).
- DAG-task auth via Managed Identity / Service Principal.
- Multi-tenant access via role assignments at the Fabric workspace level.

---

## 5. Secrets backend — Azure Key Vault

```
AIRFLOW__SECRETS__BACKEND=airflow.providers.microsoft.azure.secrets.key_vault.AzureKeyVaultBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"vault_url":"https://my-kv.vault.azure.net/", "connections_prefix":"airflow-connections", "variables_prefix":"airflow-variables", "sep":"-"}
```

Same caveat as module 08: KV secret names use `-` separator, not `/`.

---

## 6. Networking

- **Managed VNet** (default) — Microsoft-provided.
- **Customer VNet** integration — DAGs can reach private resources in your VNet.

For regulated workloads: customer VNet + private endpoints to all data resources.

---

## 7. When to choose Azure Managed Airflow

✅ **Choose Fabric Apache Airflow Jobs when**:
- Already on Microsoft Fabric.
- Need Airflow → Fabric Lakehouse / OneLake integration.
- Want managed without operational responsibility.

❌ **Pick Astro / self-host on AKS instead when**:
- Not on Fabric.
- Need flexibility WOM doesn't offer.
- Need newer Airflow versions earlier.

For a Sr Lead AI/ML candidate: **be aware** that Azure's managed Airflow is the youngest of the three big clouds and the most in-flux. A candid interview answer is: "On Azure, for regulated workloads, I'd lean to Astro Hybrid on AKS or self-host on AKS; Fabric Apache Airflow Jobs is a fit for Fabric-first shops."

---

## 8. The Optum / current-employer angle

The user's current shop (Optum) is heavy Azure + Databricks. If they use managed Airflow, it's likely:

- **Self-host on AKS** with Astronomer's Helm chart (most operationally mature).
- **Astro Hybrid** if budget allows.
- **Fabric Apache Airflow Jobs** if migration to Fabric is in progress.

WOM (the legacy) is being decommissioned; anyone on it is migrating.

---

## 9. Comparison

| | MWAA | Composer 3 | Fabric Airflow Jobs | Astro |
|---|---|---|---|---|
| Cloud | AWS | GCP | Azure | Any |
| Maturity | High | High | Newer | High (vendor) |
| Executor | Celery | KubernetesExecutor (Composer 3) | KubernetesExecutor | Yes |
| Custom image | No | Yes | Limited | Yes |
| Pricing | Per env-hour | Per vCPU-hour | Bundled with Fabric | Per AU-hour |
| Private network | PRIVATE_ONLY | PSC | Customer VNet | Hybrid VPC |

---

## Sanity check

1. The original Azure managed Airflow product is retiring. What replaces it?
2. Fabric Apache Airflow Jobs uses which executor?
3. DAG sync model in Azure Managed Airflow — how does it differ from MWAA?
4. Azure Key Vault as Secrets Backend — what naming quirk requires a config tweak?
5. When does Astro on Azure beat Fabric Apache Airflow Jobs?

---

## Sources

- [Fabric Data Factory Apache Airflow Jobs](https://learn.microsoft.com/en-us/fabric/data-factory/apache-airflow-jobs-concepts)
- [ADF Workflow Orchestration Manager (legacy)](https://learn.microsoft.com/en-us/azure/data-factory/workflow-orchestration-manager)
- [Azure Key Vault Secrets Backend](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/secrets-backends/azure-key-vault.html)

→ Next: [19 — Astronomer + self-hosted on-prem](19_astro_and_onprem.md)
