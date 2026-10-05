# Module 11 — EFS, FSx, EBS for ML

> **What this is:** the block (EBS) and file (EFS, FSx) storage options for ML workloads, with the decision matrix for "what storage do I need for this training job?"

---

## 1. EBS volume types

| Type | Max IOPS | Max throughput | Notes |
|---|---|---|---|
| **gp3** | 16,000 | 1,000 MB/s | **Default.** Decouples IOPS/throughput from size; 20% cheaper than gp2. |
| **gp2** | 16,000 | 250 MB/s | Legacy; IOPS scale with size. Avoid for new builds. |
| **io2 Block Express** | 256,000 | 4,000 MB/s | Sub-ms latency, 99.999% durability, multi-attach. SQL Server / kdb+. |
| **st1** | 500 | 500 MB/s | Throughput-optimized HDD; sequential (Kafka logs, big-data temp). |
| **sc1** | 250 | 250 MB/s | Cold HDD; cheap colocated archive. |

- **Snapshots** are incremental, stored in S3. **Fast Snapshot Restore (FSR)** pre-warms blocks; charged per AZ-snapshot pair.
- **EBS Multi-Attach** (io1/io2) — same volume to up to 16 Nitro instances in one AZ. Filesystem must be cluster-aware (GFS2, OCFS2). Mostly Oracle RAC, not ML.
- **Encryption** — default-on at account level; KMS CMK.

## 2. EFS (NFSv4)

Two performance modes:
- **General Purpose** (default) — low-latency.
- **Max I/O** (legacy) — higher latency but more parallel IOPS.

Three throughput modes:
- **Bursting** — credit-based; exhausts silently at sustained load.
- **Provisioned** — pay for committed throughput.
- **Elastic** (the modern default) — pays per usage, no provisioning.

**EFS Intelligent-Tiering** — lifecycle to IA / Archive after N days idle; up to 92% cheaper for cold data. First read after tiering pays a per-GB retrieval fee.

**Use cases:**
- Shared notebooks
- SageMaker Studio home directories
- Airflow DAG sync across workers
- Not for training I/O at >10 GB/s

## 3. FSx flavors

### FSx for Lustre

POSIX parallel filesystem; up to **terabits/s throughput**, sub-ms latency.

- **Scratch** — single-AZ, no replication, cheapest, ideal for ephemeral training runs.
- **Persistent** — replicated within AZ; 50/100/200/500/1000 MB/s/TiB throughput tiers.
- **S3-linked filesystems (DRA — Data Repository Association)** — lazy-loads from S3 on first read; writes back via `lustre_release` or DRA export. **Critical for SageMaker / EKS training** where dataset lives in S3 but training expects POSIX.
- **2024**: metadata IOPS provisioning — decouples metadata IOPS for many-small-file ML workloads (image / token shards).

### FSx for OpenZFS

Single-AZ or multi-AZ; snapshots, zero-copy clones. Multi-AZ added 2023. Shared dev environments, low-volume analytics.

### FSx for Windows File Server

SMB; AD-integrated. Legacy app shares, not ML.

### FSx for NetApp ONTAP

Multi-protocol (NFS + SMB + iSCSI), FlexClone snapshots, SnapMirror to on-prem NetApp; FabricPool tiering to S3. Capital One uses ONTAP as landing zone for on-prem feeds bridging to cloud.

## 4. Picking storage for ML

| Workload | Pick |
|---|---|
| Training I/O > 1 GB/s, > 1 TB dataset | **FSx Lustre Persistent + S3 DRA** |
| Many small files (images, audio, JSONL) | **FSx Lustre with provisioned metadata IOPS** or **S3 Express One Zone via Mountpoint** |
| Shared notebook + small dataset (< 100 GB) | **EFS Elastic Throughput** |
| Single-node training, dataset fits | **gp3 EBS** |
| Distributed training checkpoint store | **S3 Express One Zone** (2024+ SageMaker recommendation) |

## 5. Pitfalls

- **FSx Lustre data hydration**: lazy-load means **first epoch is slow** unless you `hsm_restore` (preload). Always preload for benchmarking.
- **EFS Bursting** throughput exhausts burst credits silently — switch to Elastic for production.
- **gp2 burst-balance starvation** on small (<100 GB) volumes — gp3 with provisioned IOPS solves it.
- **io2 BX is region-limited** — check before architecting.
- **Snapshots without lifecycle** pile up — use Data Lifecycle Manager (DLM).

## 6. Capital One lens

- gp3 EBS as compute root default.
- EFS Elastic Throughput for Studio domains.
- FSx Lustre Persistent for large training runs (linked to S3 DRA for dataset access).
- ONTAP for on-prem-to-cloud feed bridges (treating it as the gateway, not the lake).

## 7. Sanity check

1. When does FSx Lustre Persistent + S3 DRA beat just reading from S3 with Mountpoint?
2. What's the difference between EFS Bursting and Elastic throughput modes, and when does Bursting silently break?
3. What's the gp3 vs gp2 difference and why are new builds always gp3?
4. When would you pick FSx ONTAP over OpenZFS?
5. What's the recommended checkpoint store for SageMaker distributed training in 2024+?

## 8. Cross-references

- **Module 10** — S3 (DRA endpoint, Mountpoint)
- **Module 36** — SageMaker training (FSx Lustre integration patterns)
- **Module 40** — HyperPod (FSx Lustre as the cluster storage tier)

## Primary sources

- [`EBS_UserGuide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/EBS_UserGuide.pdf)
- [`EFS_UserGuide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/EFS_UserGuide.pdf)
- [`FSx_Lustre_UserGuide.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/FSx_Lustre_UserGuide.html)
- Research report: [`04_storage_data_lake.md`](../../research_inputs/04_aws_for_ai_ml/04_storage_data_lake.md)
