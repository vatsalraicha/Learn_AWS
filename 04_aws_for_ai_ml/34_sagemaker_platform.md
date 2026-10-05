# Module 34 — SageMaker Platform Map

> **What this is:** the SageMaker product landscape — Studio Classic vs new Studio, Domains, Spaces, Unified Studio, Code Editor, the 2018→2026 evolution.

---

## 1. The three eras of SageMaker

- **Notebook Instances era (2017-2022)** — single-user EC2-based Jupyter. Still exists, increasingly deprecated.
- **Studio Classic era (2019-2023)** — multi-user JupyterLab inside a Domain, with the older console UI.
- **New Studio era (2023+)** — redesigned UX combining JupyterLab + Code Editor (VS Code-based) + Canvas + RStudio in a single web app.

## 2. Studio Domains

A **Domain** is the multi-user SageMaker workspace boundary. Each Domain has:

- **VPC config** (the network it lives in).
- **KMS key** for at-rest encryption.
- **IAM execution role**.
- **Authentication mode**: IAM Identity Center or IAM.
- **N user profiles** — one per ML practitioner.

## 3. User profiles and Spaces

- **User profile** = a person in the Domain.
- **Space** = a workspace within the Domain. Two flavors:
  - **Private space** — single-user JupyterLab / Code Editor / RStudio.
  - **Shared space** — multiple users collaborate in the same JupyterLab.

Each Space runs on a specific instance type (e.g., `ml.t3.medium` for cheap dev, `ml.g5.2xlarge` for GPU prototyping).

## 4. The 2024 story: SageMaker Unified Studio

**SageMaker Unified Studio** (GA late 2024) integrates SageMaker with:
- **DataZone** (governance + discovery)
- **Glue** (ETL)
- **EMR** (Spark)
- **Athena** (ad-hoc SQL)
- **MWAA** (Airflow orchestration)
- **SageMaker AI** (training, inference, etc.)

The pitch: **one interface for the entire data+AI lifecycle**, with DataZone-mediated discovery and subscription. Replaces "log into Glue console for ETL, SageMaker for training, EMR for Spark."

This is the strategic direction — new builds in 2026 should target Unified Studio.

## 5. Code Editor

VS Code-based IDE in Studio. Same Domain, KMS, IAM as JupyterLab.

For engineers who prefer VS Code over JupyterLab — same underlying compute.

## 6. SageMaker Catalog

DataZone-integrated catalog visible in Studio. Browse, request access to datasets, then materialize them in your Space.

## 7. RStudio in SageMaker

Posit-licensed RStudio Workbench bundled in Studio Domains. For R users.

## 8. Custom Studio images

You can ship custom Docker images as Studio kernel choices — `tensorflow-with-our-tooling`, `pytorch-2.5-with-our-libs`. Critical for regulated orgs that vendor specific library versions.

## 9. Evolution timeline

| Year | Event |
|---|---|
| 2017 | SageMaker GA (Notebook Instances era) |
| 2019 | Studio Classic GA |
| 2020 | Pipelines, Feature Store, Clarify GA |
| 2021 | Training Compiler, Inference Recommender |
| 2022 | Studio Lab (free educational), JumpStart matures |
| 2023 | New Studio redesigned UX; HyperPod GA |
| 2024 | Unified Studio, Inference Components, MLflow integration, HyperPod EKS-based |

## 10. 2024-2026 changes

- **Unified Studio** (the headline).
- **MLflow integration** — SageMaker hosts MLflow tracking server.
- **Inference Components** (Module 37) — new endpoint cost model.
- **HyperPod EKS-based** GA (Module 40).
- **Code Editor** matured.

## 11. Pitfalls

- **Idle Studio Apps** — running JupyterServer or KernelGateway apps cost money. Auto-shutdown lifecycle config is the fix.
- **Studio Domain has a single EFS** — large user-profile homes accumulate; budget for EFS storage.
- **Migration from Notebook Instances** is non-trivial — different IAM, different code paths.
- **Two Studio versions** (Classic vs new) cause confusion. Stick to one per Domain.

## 12. Capital One lens

Capital One almost certainly runs many Studio Domains, one per LOB or per platform team. Custom Studio images vendored with internal libraries. Unified Studio likely in adoption.

## 13. Sanity check

1. Studio Classic vs new Studio — what's the difference?
2. What's a Domain vs a Space?
3. What does Unified Studio integrate?
4. Why do regulated orgs care about custom Studio images?
5. What's the auto-shutdown pattern for Studio Apps?

## 14. Cross-references

- **Modules 35-41** — the rest of SageMaker
- **Module 12** — DataZone integration via Unified Studio
- **Module 53** — Capital One MLOps spine

## Primary sources

- SageMaker Developer Guide (archived as PDF)
- Unified Studio docs (archived)
- Research report: [`09_sagemaker.md`](../../research_inputs/04_aws_for_ai_ml/09_sagemaker.md)
