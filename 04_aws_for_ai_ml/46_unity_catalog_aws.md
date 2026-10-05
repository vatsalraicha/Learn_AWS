# Module 46 — Unity Catalog on AWS

> **What this is:** Unity Catalog on AWS — S3 backing, instance profiles vs Azure service principals, storage credentials, external locations, Lake Formation interop.

---

## 1. Unity Catalog on AWS — what changes

Topic 02 covered UC fundamentals on Azure. On AWS:

- **Managed storage** uses **S3 buckets** (vs ADLS Gen2 on Azure).
- **Storage credentials** are backed by **IAM roles** (vs Azure service principals).
- **Self-assuming IAM role** required (Jan 2025) for the cross-account role.
- **External locations** point to S3 paths, governed by UC.

## 2. Storage credentials

A **Storage Credential** in UC = a managed credential UC uses to access cloud storage.

On AWS:
```
Storage Credential
  ├── Type: AWS IAM Role
  ├── Role ARN: arn:aws:iam::<account>:role/<UCRole>
  └── (External ID for trust)
```

The role's trust policy allows the Databricks service principal (in Databricks' AWS account) to assume it with the external ID condition.

## 3. External locations

A **bridge between UC and S3**:
```
External Location
  ├── URL: s3://<bucket>/<prefix>
  ├── Storage Credential: <previous>
  └── Read/write permissions granted in UC
```

UC enforces grants on external locations; the underlying S3 bucket can still have its own IAM but should be **locked down to deny direct S3 access** to UC-managed prefixes — otherwise users can bypass UC.

## 4. Self-assuming role mandate (Jan 2025)

Databricks now requires the UC cross-account role to be **self-assuming** — it can assume itself. This adds defense in depth: even if Databricks' service principal is compromised, the attacker can't trivially escalate.

## 5. Lake Formation interop

The big question: **what happens when both UC and Lake Formation govern the same S3 bucket?**

Two patterns:

### Pattern A: UC primary, no LF

UC governs S3; Lake Formation doesn't see those tables. Athena/Redshift Spectrum access via UC's Iceberg REST endpoint (2024 feature).

### Pattern B: LF primary, UC reads via Glue Catalog federation

Lake Formation owns the catalog; UC federates to it. Databricks queries against LF-managed tables go through LF's permission model.

**AWS Glue Catalog federation to UC** (2024 GA) makes Pattern B viable. Tables governed by LF appear in UC as federated objects.

**Capital One implication:** they likely have both running. The pattern likely:
- **Lake Formation** as the AWS-native catalog for non-Databricks consumers (Athena, Redshift Spectrum, EMR).
- **Unity Catalog** as the catalog for Databricks workloads.
- **Iceberg REST + Glue Catalog federation** as the bridge.

## 6. Three-level namespace

UC uses a **catalog.schema.table** namespace (vs Hive's `database.table`). Same on AWS as Azure.

## 7. Governance differences from Azure

- **No Purview integration** — DataZone is the AWS analog (third-party).
- **Audit log delivery** to S3 (vs Azure storage).
- **Lineage** UI same; backed by UC's metastore.

## 8. Credential vending

For workloads outside Databricks that need S3 access governed by UC:
- UC issues **temporary STS credentials** scoped to a specific path/permission.
- Caller uses these creds to access S3 directly.

Pattern: a Glue job or Lambda calls UC API → gets temp creds → reads S3.

## 9. Pitfalls

- **Direct S3 access bypasses UC** — must remove direct IAM grants on UC-managed prefixes.
- **LF and UC double-governing the same tables** without a clear primary causes confusion.
- **Trust policy without External ID** is insecure.
- **Self-assuming role mandate** missed → workspace creation fails (post-Jan 2025).

## 10. Capital One lens

Likely catalog stack:
```
S3 raw zone
  ↓
Glue Catalog (metastore) — Lake Formation governs
  ↓
Glue Iceberg REST Catalog
  ↓
Unity Catalog federates → Databricks consumers
  ↓
DataZone for discovery / subscription (overlays both)
```

This isn't trivial — operating two governance frameworks consistently is the open question worth raising in an interview.

## 11. Sanity check

1. What's the AWS storage credential made of?
2. Why is the self-assuming role mandate a defense-in-depth measure?
3. How can UC and Lake Formation coexist on the same S3 data?
4. What does Glue Iceberg REST Catalog federation enable?
5. What's credential vending used for?

## 12. Cross-references

- **Topic 02 Module 9** — UC fundamentals on Azure (pre-req)
- **Module 12** — Lake Formation + Glue Catalog + Iceberg
- **Module 10** — S3 + Iceberg + S3 Tables

## Primary sources

- [`databricks_aws_uc.html`](../../research_inputs/04_aws_for_ai_ml/downloads/databricks_on_aws/databricks_aws_uc.html)
- Research report: [`11_databricks_on_aws.md`](../../research_inputs/04_aws_for_ai_ml/11_databricks_on_aws.md)
