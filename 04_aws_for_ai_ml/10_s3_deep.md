# Module 10 — S3 Deep

> **What this is:** S3 storage classes, lifecycle, replication, S3 Tables (Iceberg-native), Express One Zone, Object Lambda, Access Points, encryption, performance limits, Mountpoint. The data-lake substrate.
>
> **Why it matters:** every Capital One workload reads or writes S3. The 2019 breach exfiltrated from S3. S3 cost optimization can be 7-figure annual savings. SageMaker training, EMR, Glue, Athena, Lake Formation all sit on S3.
>
> **Cert mapping:** SAA-C03, DEA-C01 (Data Store 26%), SCS-C03 (S3 protections).

---

## 1. Storage classes (price/latency tradeoff)

| Class | Latency | Storage cost (relative) | When |
|---|---|---|---|
| **Standard** | ms first-byte | 1× | Default — hot training data, model artifacts |
| **Standard-IA** | ms | 0.55× | 30-day min; per-GB retrieval fee. Older training inputs |
| **One Zone-IA** | ms | 0.44× | Single-AZ — only for reproducible derived features |
| **Intelligent-Tiering** | ms (Freq/IA), ms-min (Archive) | varies | Unknown access patterns. Small monitoring fee per 1000 objects (<128KB never tiered) |
| **Glacier Instant Retrieval** | ms | 0.2× | Quarterly access; 90-day min |
| **Glacier Flexible Retrieval** | 1–5 min Expedited / 3–5 hr Std / 5–12 hr Bulk | 0.07× | Backups, occasional access |
| **Glacier Deep Archive** | 12+ hr | 0.04× | 7-year regulatory retention (SOX, FFIEC) |

11 nines durability across all classes; 99.99% availability on Standard.

## 2. Lifecycle, versioning, replication

- **Lifecycle policies** transition or expire objects on age, tags, size filters. **`AbortIncompleteMultipartUpload`** is the single most-omitted rule and silently bleeds money.
- **Versioning** is bucket-level. Once enabled, only "suspended" — never disabled. Required for **Object Lock** and MFA-Delete.
- **Replication**:
  - **SRR** (same region) for log aggregation, dev/prod fanout.
  - **CRR** (cross-region) for DR.
  - **Multi-Region Access Points (MRAP)** route to lowest-latency replica via Global Accelerator.
  - **S3 Replication Time Control (RTC)** — 99.99% replication within 15 min with billing SLA.

## 3. S3 Tables (GA Dec 2024)

A new bucket type purpose-built for tabular Iceberg data:

- **Automatic compaction** and snapshot expiration.
- **Unreferenced-file cleanup**.
- Table-level RBAC.
- Native Athena/EMR/Redshift integration; **Glue Iceberg REST catalog** integration mid-2025.
- **Up to 10× higher TPS** on Iceberg writes vs self-managed Iceberg on Standard S3.
- **3× faster queries** vs self-managed Iceberg.

**Federation pattern** for Capital One: raw zone on S3 Standard, curated Iceberg tables in S3 Tables for SLA-bound consumers.

## 4. Object Lambda & Access Points

- **Access Points** — named hostnames with their own bucket policy. Scoped per VPC or per workload. Capital One uses one per microservice.
- **Object Lambda Access Points** — invoke a Lambda on `GetObject` to transform data inline: **PII redaction, Databolt token swap** for downstream consumers without re-materializing the dataset.
- **Multi-Region Access Points** — single global endpoint over replicated buckets.

## 5. Encryption & compliance

| | What it is | Use case |
|---|---|---|
| **SSE-S3** | AES-256, S3-managed | Default since Jan 2023; no extra cost |
| **SSE-KMS** | Customer-managed key | PCI-DSS — required to demonstrate key custody |
| **SSE-C** | Customer-supplied key per request | HSM-backed key custody outside AWS |
| **DSSE-KMS** | Dual-layer KMS | CNSA / FIPS-mandated (GovCloud) |

**Bucket Key** — caches a data key per bucket, cuts KMS API calls by **up to 99%**. Always enable for KMS-encrypted buckets at scale.

**Object Lock** — WORM:
- **Governance mode** — IAM with privilege can override.
- **Compliance mode** — no override, not even root. Required for FINRA 17a-4(f) immutable broker-dealer records.

**Block Public Access (BPA)** — account-level kill switch. **ON by SCP for every Capital One account.**

**S3 Access Grants** (2023) — IAM Identity Center–based grants that issue temporary credentials scoped to prefix. Replaces sprawling bucket policies for user-level access.

## 6. Performance & limits

**3,500 PUT/POST/DELETE per second per prefix. 5,500 GET/HEAD per second per prefix.**

The prefix is whatever character sequence precedes the partition you key on, **not the leading directory**. The partition workarounds:

- **Hash-prefix object keys**: `<8-char hash>/<rest of path>` distributes load across virtual prefixes.
- **Partitioned prefixes**: `dt=2026-05-15/hour=03/` naturally distributes hot writes.
- **Iceberg sidesteps** this naturally — metadata writes distribute across many manifests.

**S3 Express One Zone** (Nov 2023) — single-AZ "directory bucket" class:
- **Single-digit-millisecond** latency.
- ~50% lower request cost than S3 Standard.
- **7-10× faster** on small-object workloads.
- Trade-off: single AZ. Replicate critical training shards into S3 Standard.

**S3 Mountpoint** (GA Aug 2023) — POSIX-ish FUSE mount; high-throughput read, append-only write, no rename. SageMaker training jobs use this when `pipe` mode isn't fast enough.

**S3 Batch Operations** — operate across billions of objects via inventory manifest (re-encrypt, restore, invoke Lambda).

## 7. Pitfalls and anti-patterns

- **Lifecycle to Glacier on tiny objects** costs more than the storage savings (per-object overhead).
- **Forgetting `s3:RestoreObject`** in IAM blocks Athena queries against Glacier partitions.
- **Replication doesn't replicate pre-existing objects** — run S3 Batch Replication explicitly (since 2022).
- **KMS key policy must allow the role, not the bucket** — KMS denies don't show in S3 logs, only in CloudTrail.
- **Missing `AbortIncompleteMultipartUpload`** lifecycle rule — multipart upload fragments accumulate forever.
- **Bucket Key disabled** at scale → high KMS API costs.

## 8. Capital One lens

- S3 is **the** lake substrate. Bucket naming convention: `co-<lob>-<env>-<purpose>-<region>` (e.g., `co-card-prd-features-use1`).
- Every bucket: **BPA on, default SSE-KMS w/ Bucket Key, versioning on**, lifecycle for expiring multipart and aging non-current versions.
- **Databolt tokenization runs upstream of S3** — raw PAN never lands; tokens only.
- Iceberg curated tables migrating to **S3 Tables** buckets through 2026.

## 9. Sanity check

1. What are the per-prefix request rate limits, and how do you work around them?
2. When would you use S3 Express One Zone vs Standard?
3. What does Object Lock Compliance mode enforce that Governance mode doesn't?
4. How does Bucket Key reduce KMS cost?
5. Why does S3 Tables matter for Iceberg performance?

## 10. Cross-references

- **Module 12** — Lake Formation FGAC layered on S3 catalog tables
- **Module 14** — Glue Spark reading/writing S3 Iceberg
- **Module 22, 24** — Redshift Spectrum, Athena reading S3
- **Module 41** — SageMaker training reading S3 via Mountpoint / pipe / DRA
- **Module 52** — Databolt tokenization upstream of S3

## Primary sources

- [`S3_Best_Practices.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/S3_Best_Practices.pdf)
- Research report: [`04_storage_data_lake.md`](../../research_inputs/04_aws_for_ai_ml/04_storage_data_lake.md)
