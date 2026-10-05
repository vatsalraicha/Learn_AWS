# 32 — Certifications: Astronomer (Fundamentals / DAG Authoring / Operations), DEA-C01, PDE, DP-700, DP-203

> *"For the Capital One target: take **AWS DEA-C01** (covers MWAA) and **Astronomer DAG Authoring**. Skip Fundamentals (too basic). Skip Azure/GCP certs unless you're targeting those clouds."*

## Why this module exists

Airflow has no Apache-issued cert; **Astronomer** is the de facto vendor. AWS / GCP / Azure cover their managed Airflow inside broader data certs.

---

## 1. The cert landscape

| Cert | Issuer | Cost USD | Format | Time | Validity |
|---|---|---:|---|---|---|
| **Apache Airflow Fundamentals** | Astronomer | $150 | 75 MCQ, 60 min | 60 min | 2 yr |
| **DAG Authoring for Apache Airflow** | Astronomer | $150 | 75 MCQ, 60 min | 60 min | 2 yr |
| **Astronomer Certification for Airflow Operations** | Astronomer | $150 | 75 MCQ, 60 min | 60 min | 2 yr |
| **AWS DEA-C01** (Data Engineer Associate) | AWS | $150 | ~65 questions, 130 min | 130 min | 3 yr |
| **GCP Professional Data Engineer (PDE)** | GCP | $200 | ~50 q, 120 min | 120 min | 2 yr |
| **Azure DP-700** (Fabric Data Engineer) | Microsoft | $165 | ~45-65 q, 100 min | 100 min | 1 yr |
| **Azure DP-203** (Azure Data Engineer) | Microsoft | $165 | **Retired Mar 2025** | — | — |

---

## 2. Verdict for "Sr AI/ML Engineer → Capital One"

| Cert | Verdict |
|---|---|
| Apache Airflow Fundamentals | **Skip** — too basic for a Sr engineer |
| DAG Authoring | **Buy** — validates production DAG patterns |
| Astronomer Operations | **Skip-or-bundle** — useful if you operate Airflow; covered tangentially by CKA |
| AWS DEA-C01 | **Buy** — covers MWAA + broader AWS data eng |
| GCP PDE | **Skip** unless you're targeting GCP |
| Azure DP-700 | **Skip** unless Optum mandates Fabric |

Recommended 2-cert set for Capital One target: **AWS DEA-C01 + Astronomer DAG Authoring**.

---

## 3. AWS DEA-C01 (the credibility cert)

GA Nov 2023. Domains:

- Data Ingestion + Transformation (~34%).
- Data Store Management (~26%).
- Data Operations + Support (~22%).
- Data Security & Governance (~18%).

MWAA covered ~5%. Glue, Lambda, Step Functions, EMR, Athena, Redshift, S3, Kinesis, DynamoDB — all in scope.

For Capital One: more relevant than the AI Engineer (AIP-C01) cert for the data-engineering-adjacent Sr Lead AI/ML role.

Study: ~50 hours. Stéphane Maarek's course; AWS official sample questions; Tutorials Dojo practice tests.

---

## 4. Astronomer DAG Authoring (the depth cert)

Tests DAG authoring patterns specifically:
- TaskFlow API.
- Dynamic task mapping.
- Sensors + deferrable.
- XCom patterns.
- Connections + Secrets Backend.
- Datasets.
- Setup/teardown.
- Trigger rules.

Study: ~10 hours. Astronomer Academy has the official prep course (free).

Passing demonstrates **you write production-grade DAGs**. The right cert for the Lead role.

---

## 5. Astronomer Fundamentals (the "I just used Airflow once" cert)

Tests Airflow basics:
- What's a DAG.
- Operators vs Tasks.
- Basic scheduling.

Skip for a Sr engineer. Pass the DAG Authoring cert directly.

---

## 6. Astronomer Operations (the SRE cert)

Tests operating Airflow:
- Executors.
- Scaling.
- Failure modes.
- Astro-specific patterns.

Useful if you'll operate (not just author). Skip if your shop is on MWAA / Composer / Astro Hosted (you don't operate it).

---

## 7. GCP Professional Data Engineer

If you're targeting a GCP shop. Covers Cloud Composer + BigQuery + Dataproc + Dataflow + Pub/Sub.

For Capital One: not the right cert.

---

## 8. Azure DP-700 (Fabric Data Engineer)

Replaces DP-203. Covers Fabric (the new bundled platform): Lakehouse, Data Factory, Pipelines, Apache Airflow Jobs.

Skip for Capital One. Buy if Optum directs you to Fabric.

---

## 9. The 18-month plan augmented for Topic 06

If you're doing the cert plan from Topic 05's module 33 (CKAD/CKA/CKS + DOP-C02):

| Months | Cert | Topic |
|---|---|---|
| 1-2 | CKAD | K8s app dev |
| 3-5 | CKA | K8s admin |
| 6-9 | CKS | K8s security |
| 10-11 | **AWS DEA-C01** | Data eng (covers MWAA) |
| 12-13 | **Astronomer DAG Authoring** | Airflow depth |
| 14-15 | AWS DOP-C02 | DevOps (covers EKS) |
| 16-18 | AWS MLA-C01 / AIP-C01 | ML platform / GenAI |

The full set in 18 months at 3 hr/week.

---

## 10. Study resources

- **Astronomer Academy** (free) — official Airflow prep + courses.
- **Marc Lamberti's Airflow course** (Udemy, ~$15) — most popular.
- **AWS Skill Builder** — official AWS prep.
- **Tutorials Dojo** — practice exams for AWS.
- **A Cloud Guru / Pluralsight** — supplementary.

For Astronomer DAG Authoring: Marc Lamberti's course on Astronomer Academy is the canonical prep. ~10 hours of video + practice.

---

## 11. Real interview signal

Certs are the door; conversation is the room. Pair certs with:

- **Personal lab** running Airflow on K8s (CKS + Airflow combo).
- **OSS contribution** — a provider PR or a bug fix.
- **Blog post / talk** — explain a tricky pattern you implemented.

For Capital One: a personal lab showing "I deployed Airflow on EKS with IRSA + Cosmos + dbt + OpenLineage + Cosign-signed images" beats any cert.

---

## Sanity check

1. Two certs for Capital One target — which?
2. AWS DEA-C01 covers MWAA at what depth?
3. Astronomer Fundamentals — skip for a Sr engineer. Why?
4. Azure DP-203 status as of mid-2026?
5. Replacement for DP-203 covering Apache Airflow Jobs in Fabric?

---

## Sources

- [Astronomer Academy](https://academy.astronomer.io/)
- [AWS Certified Data Engineer – Associate](https://aws.amazon.com/certification/certified-data-engineer-associate/)
- [GCP Professional Data Engineer](https://cloud.google.com/certification/data-engineer)
- [Microsoft DP-700 (Fabric Data Engineer)](https://learn.microsoft.com/credentials/certifications/exams/dp-700/)
- [Marc Lamberti's Airflow course](https://marclamberti.com/)

→ End of Topic 06.
