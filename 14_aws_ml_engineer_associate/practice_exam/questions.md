# AWS Certified Machine Learning Engineer – Associate (MLA-C01) — Practice Question Bank

> **Scope:** 500 exam-realistic questions covering the four official domains of the MLA-C01 exam.
>
> **Weighting (matches the official exam guide):**
> - **Domain 1 — Data Preparation for ML (28%)** → Q1–Q140 (140 questions)
> - **Domain 2 — ML Model Development (26%)** → Q141–Q270 (130 questions)
> - **Domain 3 — Deployment and Orchestration of ML Workflows (22%)** → Q271–Q380 (110 questions)
> - **Domain 4 — ML Solution Monitoring, Maintenance, and Security (24%)** → Q381–Q500 (120 questions)
>
> **Format:** Each question is single-answer multiple choice (A–D) unless prefixed with "(Select TWO)" or "(Select THREE)". The real exam is **65 questions in 130 minutes** (~2 min per question); pace yourself accordingly. **Pass threshold:** 720/1000 scaled (~72%).
>
> **Parseable format** — used by the companion Flask quiz app:
> ```
> ## Q{n} — Domain {N}: {domain name}
> **Objective:** {one-line objective from the exam guide}
>
> {question stem}
>
> - A. {option}
> - B. {option}
> - C. {option}
> - D. {option}
>
> **Answer:** {letter or comma-separated for multi-select}
>
> **Explanation:** {why correct, why distractors fail}
> ```

---

# Domain 1 — Data Preparation for Machine Learning (28%)

## Q1 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose an appropriate data format based on the SageMaker built-in algorithm's content-type contract

A team will train SageMaker **Factorization Machines** on a 500 GB sparse rating matrix in S3. The data is currently stored as gzipped CSV. They want the AWS-recommended high-performance ingest path. Which format and SDK helper should they use?

- A. Convert to Parquet with Snappy compression and read via FastFile mode.
- B. Convert to RecordIO-protobuf (sparse variant) using `sagemaker.amazon.common.write_spmatrix_to_sparse_tensor` and stream via Pipe mode.
- C. Keep gzipped CSV and use File mode with `text/csv`.
- D. Convert to TFRecord with GZIP compression and use Pipe mode.

**Answer:** B

**Explanation:** Factorization Machines is one of the SageMaker built-ins where RecordIO-protobuf is the only realistic content type for production-scale training, and AWS's recommended sparse path is `write_spmatrix_to_sparse_tensor`. CSV is technically listed but performs poorly; XGBoost is the built-in that lives on CSV/libsvm. Parquet and TFRecord are not accepted content types for Factorization Machines.

---

## Q2 — Domain 1: Data Preparation for Machine Learning
**Objective:** Match SageMaker built-in algorithms to their required input content types

Which SageMaker built-in algorithm does **NOT** accept `application/x-recordio-protobuf` as a training content type?

- A. K-Means
- B. Linear Learner
- C. PCA
- D. XGBoost

**Answer:** D

**Explanation:** XGBoost is the documented exception in the built-in algorithm table; it accepts only `text/csv` or `text/libsvm` (and Parquet in newer container versions for File/FastFile mode), never RecordIO-protobuf. K-Means, Linear Learner, PCA, k-NN, RCF, LDA, NTM, Factorization Machines and Seq2Seq all accept RecordIO-protobuf and CSV.

---

## Q3 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize content-type contracts for SageMaker BlazingText and DeepAR

A data scientist needs to train **DeepAR** on multiple time series stored in S3. What content type and per-line shape must the training data follow?

- A. `text/csv` with header row and target in the first column
- B. `application/x-recordio-protobuf` with one dense tensor per series
- C. `application/jsonlines` with one JSON object per time series containing `start`, `target`, optional `cat`, and `dynamic_feat`
- D. `text/libsvm` with one labeled row per timestep

**Answer:** C

**Explanation:** DeepAR and BlazingText both consume `application/jsonlines` — DeepAR puts one time series per line with `{start, target, cat, dynamic_feat}` fields. CSV and RecordIO-protobuf are not the documented DeepAR content types, and libsvm is XGBoost-only.

---

## Q4 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify why a SageMaker training job silently produces a poor model from a header-row CSV

A teammate uploaded a CSV to S3 with header row `customer_id,age,income,target` and pointed a SageMaker Linear Learner training job at it. The job runs to completion but the model has near-random accuracy. Which two issues explain the failure? **(Select TWO)**

- A. SageMaker built-in algorithms require **no header row**; the first training row is being parsed as numeric data.
- B. Linear Learner needs the **label in column 0**; with the current layout the label is in column 3 and `customer_id` is being treated as the target.
- C. CSV must always be GZIP-compressed for Linear Learner.
- D. Linear Learner requires `application/x-recordio-protobuf` exclusively and CSV is silently ignored.
- E. The bucket must be in S3 Express One Zone for header detection to work.

**Answer:** A, B

**Explanation:** Two distinct traps fire together. The SageMaker docs state that CSV files for built-ins must have no header and that the target must be in the first column. The header row gets parsed as a numeric record and the actual label column is misaligned. CSV is accepted, no compression is required, and storage class is irrelevant.

---

## Q5 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish data formats from table formats

An interviewer asks "what file format does an Apache Iceberg table use?" Which answer is correct?

- A. Iceberg is its own binary file format.
- B. Iceberg stores data files as Parquet (or optionally ORC/Avro) and stores manifest files as Avro, with a `metadata.json` pointing to the current snapshot.
- C. Iceberg uses CSV for data and JSON for manifests.
- D. Iceberg files are gzipped RecordIO-protobuf records.

**Answer:** B

**Explanation:** Iceberg is a **table format**, not a data format. It sits on top of Parquet (data files) and Avro (manifest list and manifest files) with a `metadata.json` pointer. Confusing the two layers is the most common conceptual trap on the exam — "file format" answers must be Parquet/ORC/Avro/CSV/JSON, while "table format providing ACID transactions" answers are Iceberg/Hudi/Delta.

---

## Q6 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply the splittability rule to choose a Spark-friendly compressed text format

A team's Spark job on EMR is single-threaded against a 100 GB CSV file. Why, and which one change fixes it without changing the row format?

- A. gzip is a single deflate stream and is not splittable, so Spark cannot parallelize the read; switch the compression to bzip2 or remove compression.
- B. Spark cannot read CSV at all; convert to JSON.
- C. CSV cannot exceed 1 GB per file in Spark; split into 100 1-GB files.
- D. Spark requires LZO compression for parallel CSV reads.

**Answer:** A

**Explanation:** Gzipped CSV is non-splittable because gzip is one continuous deflate stream — Spark must single-thread the decode. bzip2 is block-structured and therefore splittable, as are Parquet/ORC/Avro container files. The 1-GB ceiling is fictional and Spark reads CSV natively.

---

## Q7 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick the right format for Bedrock fine-tuning input

A team is fine-tuning Claude on Amazon Bedrock with conversation-style examples. What file shape must they upload to S3?

- A. One JSON document containing an array of all examples
- B. JSONL — one JSON object per line, no outer array, no commas between examples, UTF-8 without BOM
- C. CSV with `prompt,completion` columns
- D. Parquet with a `messages` column of nested struct arrays

**Answer:** B

**Explanation:** Bedrock and JumpStart fine-tuning paths require JSONL where each line is a self-contained JSON object. Outer arrays, trailing commas, smart quotes, and BOM bytes are common reasons fine-tuning jobs reject "valid-looking" files. CSV and Parquet are not Bedrock fine-tuning inputs.

---

## Q8 — Domain 1: Data Preparation for Machine Learning
**Objective:** Reason about Parquet's columnar advantages for ML training

A SageMaker training job needs 10 features out of a 200-column Parquet dataset partitioned by date, filtering on `event_date BETWEEN '2026-04-01' AND '2026-04-30'`. Which two Parquet mechanics minimize bytes read from S3? **(Select TWO)**

- A. Column pruning — only the 10 requested column chunks are fetched as ranged GETs.
- B. Predicate pushdown using per-row-group `min`/`max` statistics; row groups outside the date range are skipped without reading data bytes.
- C. Dictionary encoding at the file level forces every reader to download the dictionary header for the entire dataset.
- D. Parquet automatically decrypts SSE-KMS objects without calling KMS.
- E. The 4-byte `PAR1` magic number contains row counts that eliminate the need for predicates.

**Answer:** A, B

**Explanation:** Column pruning and predicate pushdown via min/max statistics in the footer are the two Parquet features that cut bytes read at the S3 byte-range level. Dictionary encoding is page-level (not whole-file) and is invisible to the reader. Parquet has no special KMS interaction, and the magic number does not store statistics.

---

## Q9 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose between Parquet and Avro for streaming versus analytical access

A team writes one event at a time from a Kafka producer and the schema evolves frequently. Downstream analytics scans column subsets across years of data. Which format pairing is canonical?

- A. CSV for both layers
- B. Avro for transport (Kafka/MSK) with Glue Schema Registry, Parquet for rest in S3 / Iceberg
- C. RecordIO-protobuf for both
- D. JSON for transport, ORC for rest

**Answer:** B

**Explanation:** Avro's row-oriented binary layout and schema-evolution semantics make it the canonical Kafka envelope; Parquet's columnar layout makes it the canonical analytical-store format. The common pattern is Avro for transport and Parquet for rest, with a Flink or Spark job bridging the two. CSV is non-validated and slow at scale; RecordIO-protobuf is SageMaker built-in-specific.

---

## Q10 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick the Glue Schema Registry compatibility mode for a producer-adds-optional-field scenario

A Kinesis producer is about to add a new optional field to its Avro schema. Consumers running older code must keep working without re-deploy. Which Glue Schema Registry compatibility mode is sufficient?

- A. NONE
- B. BACKWARD
- C. FORWARD
- D. FULL_ALL

**Answer:** B

**Explanation:** BACKWARD compatibility means the new schema can read data written by the previous schema; equivalently, *old consumers can ignore the new optional field*. It is the production default for streaming pipelines. FORWARD is for the inverse roll-out, FULL/FULL_ALL are stricter than needed, and NONE/DISABLED skip the check entirely.

---

## Q11 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the SageMaker input mode that streams S3 objects into a FIFO without downloading

Which SageMaker training input mode pre-fetches S3 objects with high concurrency and streams them into a named FIFO pipe, one reader per pipe?

- A. File mode
- B. FastFile mode
- C. Pipe mode
- D. AugmentedManifestFile

**Answer:** C

**Explanation:** Pipe mode creates a Unix FIFO per epoch, pre-fetches from S3, and streams bytes into the pipe for one reader. FastFile uses FUSE for POSIX semantics with random access; File mode downloads the entire dataset before training; AugmentedManifestFile is a JSONL manifest pattern for image+label pairs (typically over Pipe).

---

## Q12 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick the modern AWS-blessed mode for a custom PyTorch training script

A team trains a custom PyTorch model on a 2 TB Parquet dataset in S3. The script projects 30 of 200 columns per epoch. The team wants the simplest mode that supports POSIX random access without downloading the whole dataset. Which mode?

- A. File mode
- B. FastFile mode
- C. Pipe mode with `PipeModeDataset`
- D. AugmentedManifestFile

**Answer:** B

**Explanation:** FastFile mode FUSE-mounts the S3 prefix, exposes POSIX semantics, supports random access (best for sequential reads but tolerates random), and starts training in seconds. AWS now recommends FastFile over Pipe for new custom-script jobs; Pipe remains for SageMaker built-ins with RecordIO-protobuf. File mode would waste hours downloading 2 TB before training starts.

---

## Q13 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize when Pipe mode is still the right answer over FastFile

A team's existing job uses **SageMaker Linear Learner** with RecordIO-protobuf shards on S3 and Pipe mode. A new MLE asks whether to migrate to FastFile. What is the AWS-recommended answer?

- A. Always migrate — Pipe mode is deprecated.
- B. Stay on Pipe mode; Pipe + RecordIO-protobuf is the documented fast path for SageMaker built-in algorithms.
- C. Migrate to File mode for the smallest EBS volume.
- D. Migrate to EFS for cross-AZ resilience.

**Answer:** B

**Explanation:** The FastFile-replaces-Pipe framing applies to *new custom-script* jobs, not to working Pipe+RecordIO-protobuf pipelines feeding SageMaker built-ins (Linear Learner, K-Means, PCA, FM, NTM, Object2Vec). Pipe is not deprecated; AWS still documents it as the recommended path for those built-ins.

---

## Q14 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use `ShardedByS3Key` correctly for distributed training

For a distributed SageMaker training job with 4 instances reading a 1 TB S3 dataset, what setting prevents each instance from downloading the full dataset?

- A. `S3DataDistributionType=FullyReplicated`
- B. `S3DataDistributionType=ShardedByS3Key`
- C. Use Pipe mode (the setting does not exist)
- D. Set `VolumeSizeInGB=250` on the training job

**Answer:** B

**Explanation:** `ShardedByS3Key` distributes S3 objects across training instances so each instance sees a disjoint subset. `FullyReplicated` (the default) makes every instance download the entire dataset. Adjusting EBS size does not change the data-distribution pattern. The AWS-blessed combo for distributed built-in training is `ShardedByS3Key + Pipe mode + RecordIO-protobuf`.

---

## Q15 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish AugmentedManifestFile from regular S3 prefix sources

A team is training **SageMaker Object Detection** on JPEG images paired with bounding-box annotations. Which input mode bundles each image with its label as one zipped stream record?

- A. File mode with a flat prefix
- B. FastFile mode (it auto-pairs images with labels)
- C. AugmentedManifestFile (JSONL manifest of `{source-ref, annotations}` records, consumed via Pipe mode)
- D. EFS mount with one file per (image, label) pair

**Answer:** C

**Explanation:** AugmentedManifestFile points to a JSONL manifest where each line carries `source-ref` (image S3 URI) plus its annotation; SageMaker zips image bytes and label into a Pipe stream. FastFile does not support manifests, and File mode does not auto-pair. EFS would work in principle but is not the AWS-documented pattern for Object Detection.

---

## Q16 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick a storage class for a hot training dataset

A team's daily SageMaker job re-reads a 1 TB feature dataset every day. Which S3 storage class minimizes total cost without adding restore latency?

- A. S3 Glacier Flexible Retrieval
- B. S3 Glacier Deep Archive
- C. S3 Standard
- D. S3 Glacier Instant Retrieval

**Answer:** C

**Explanation:** Daily access defeats Glacier classes' minimum-storage-duration rules and adds either restore latency or per-GB retrieval fees. Glacier Instant Retrieval is for *infrequent* (monthly-ish) access with millisecond reads; daily training reads make S3 Standard the cheapest option after retrieval fees are counted. Deep Archive's 12–48 hour restore makes it incompatible with a daily SLA.

---

## Q17 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply S3 lifecycle policies to age training data into cold tiers

A team archives raw training data for a 7-year regulatory retention with annual auditor access. Which configuration is correct?

- A. S3 Standard with Object Lock Governance and Versioning Off
- B. S3 Glacier Deep Archive with Object Lock Compliance mode and Versioning On
- C. S3 One Zone-IA with daily replication to another region
- D. S3 Express One Zone with SSE-KMS

**Answer:** B

**Explanation:** 7-year regulatory archives with rare access map to Glacier Deep Archive (cheapest, 12–48 hour restore acceptable for annual audits). Object Lock Compliance mode enforces WORM such that not even the root user can delete, satisfying FINRA/SEC Rule 17a-4/HIPAA. Object Lock requires versioning. Governance mode is weaker (can be overridden) and Express One Zone is for hot low-latency data.

---

## Q18 — Domain 1: Data Preparation for Machine Learning
**Objective:** Solve a KMS-throttling and cost problem on a SageMaker training job

A distributed SageMaker training job reads 100,000 small Parquet files from a KMS-encrypted bucket. The KMS bill jumped to $2,400/month and the job is hitting `ThrottlingException` on KMS Decrypt calls. What single change fixes both problems?

- A. Switch the bucket to SSE-S3 encryption.
- B. Enable S3 Bucket Keys on the bucket so the data key is cached at the bucket level and KMS Decrypt request volume drops by up to 99%.
- C. Switch the bucket to SSE-C with a customer-managed key file.
- D. Migrate to S3 Express One Zone (which uses no KMS).

**Answer:** B

**Explanation:** S3 Bucket Keys cache a short-lived AES key at the bucket level so S3 does not call KMS once per object; AWS reports up to 99% KMS request reduction. Dropping to SSE-S3 would lose customer-managed-key audit guarantees. SSE-C requires the client to send keys with each request and is operationally painful. Express One Zone supports only SSE-S3 anyway and cannot be used for SageMaker outputs requiring SSE-KMS.

---

## Q19 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the S3 prefix scaling limit and the standard mitigation

A distributed training job runs on 32 instances all reading from `s3://bucket/imagenet/train/`. Throughput plateaus and S3 returns `SlowDown` (503) errors. Which mitigation is structurally correct?

- A. Spread training data across many prefixes (hash-based sub-directories) so the 5,500 GET/s per-prefix limit applies in parallel.
- B. Switch to SSE-KMS encryption to bypass throttling.
- C. Enable S3 Transfer Acceleration.
- D. Move all data into a single 1 TB Parquet file.

**Answer:** A

**Explanation:** S3 supports up to 5,500 GET/s per prefix; 32 instances hammering one prefix throttle that single bucket of capacity. Spreading objects across many prefixes (or hashed sub-directories) parallelizes the limit. Transfer Acceleration is for cross-region uploads from the public internet, not internal training reads. KMS does not affect prefix throttling, and one mega-file destroys parallelism.

---

## Q20 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose S3 Express One Zone correctly for hot training data

When is **S3 Express One Zone** (directory buckets) the right ingest substrate for a SageMaker training job?

- A. Multi-AZ 7-year audit archive of training data
- B. Latency-sensitive hot training data where instances can be co-located in the same AZ and SSE-KMS is not required
- C. Cross-region replicated feature store offline tier
- D. Long-term archive at the lowest possible cost

**Answer:** B

**Explanation:** Directory buckets deliver single-digit-ms first-byte latency and 10× higher request rate at ~10× the per-GB Standard price. The trade-offs are single-AZ (no cross-AZ replication) and SSE-S3 only (no SSE-KMS for SageMaker output). They are wrong for archives, multi-AZ durability, or KMS-mandated workloads.

---

## Q21 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify S3 Tables versus S3 Vectors usage

A team needs an ACID, schema-evolving training table queried by both Athena and Spark, with AWS managing compaction and snapshot cleanup. Which S3 surface is the AWS-preferred answer?

- A. S3 Standard general-purpose bucket with Iceberg metadata in a separate prefix
- B. S3 Tables (Iceberg-native bucket type with managed compaction and snapshot retention)
- C. S3 Vectors
- D. S3 Express One Zone

**Answer:** B

**Explanation:** S3 Tables is the purpose-built Iceberg substrate with managed compaction, snapshot expiry, and orphan file cleanup — AWS reports 3× query and 10× throughput over unmanaged Iceberg on Standard. S3 Vectors is a storage-first vector store for cold embeddings. Express One Zone is for hot single-AZ latency. Hand-rolled Iceberg on Standard works but loses the managed-compaction win.

---

## Q22 — Domain 1: Data Preparation for Machine Learning
**Objective:** Avoid an on-prem-to-S3 networking mis-step

An on-premises ETL job needs private network access to S3 over Direct Connect or VPN. Which VPC endpoint type is required for S3 traffic to use the private path?

- A. S3 **Gateway** endpoint, because gateway endpoints work from any source.
- B. S3 **Interface** endpoint (powered by AWS PrivateLink), because gateway endpoints are reachable only from within the VPC route tables and not from on-prem networks.
- C. NAT Gateway only.
- D. Internet Gateway with public bucket access.

**Answer:** B

**Explanation:** S3 gateway endpoints are route-table-attached and are not reachable from on-prem over Direct Connect or VPN — they only serve traffic originating in the VPC. S3 interface endpoints (PrivateLink) present a regional private IP that on-prem routes can target. The gateway-vs-interface distinction is one of the most common networking traps on the exam.

---

## Q23 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick FSx for Lustre deployment type for a multi-week experimentation phase

A team runs distributed deep learning on a 10 TB dataset for six weeks with daily retrains. Hardware-failure resilience matters. Which FSx for Lustre option fits?

- A. Scratch 2 SSD with no S3 link
- B. Persistent 2 SSD with a Data Repository Association to S3
- C. FSx for OpenZFS with NFS mount
- D. EFS General Purpose

**Answer:** B

**Explanation:** Persistent 2 SSD replicates within the AZ, auto-replaces failed servers, and is the right choice for multi-week training. Pairing with a Data Repository Association makes S3 the source of truth and Lustre the hot cache. Scratch loses data on failure (good for one-shot bursts). OpenZFS is not the SageMaker-native HPC ML choice; EFS is multi-AZ but cannot hit Lustre throughput.

---

## Q24 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall the FSx for Lustre single-AZ constraint

A SageMaker training cluster spans subnets in three AZs to chase Spot capacity. The team mounts an FSx for Lustre Persistent 2 file system. Why do some instances fail to mount?

- A. FSx for Lustre is single-AZ; only instances in the file system's AZ can mount.
- B. FSx for Lustre requires SSE-KMS encryption disabled for mounts to succeed.
- C. The mount target requires a public IP on each EC2 instance.
- D. FSx for Lustre supports only Pipe mode.

**Answer:** A

**Explanation:** FSx for Lustre lives in a single AZ to avoid cross-AZ data-transfer cost and latency. The training cluster's subnets must match that AZ exactly. For multi-AZ resilience, teams rely on the S3 DRA to rehydrate the file system in a different AZ if needed. Encryption, public IPs, and Pipe mode are unrelated.

---

## Q25 — Domain 1: Data Preparation for Machine Learning
**Objective:** Reason about FSx for Lustre throughput math under exam pressure

A team needs ~64 GB/s aggregate throughput for a 30 TB training dataset on FSx for Lustre Persistent 2 SSD. Which sizing satisfies the requirement at lowest cost while keeping aggregate throughput on target?

- A. 30 TiB at 1000 MB/s/TiB → 30 GB/s
- B. 64 TiB at 1000 MB/s/TiB → 64 GB/s
- C. 128 TiB at 500 MB/s/TiB → 64 GB/s
- D. 4.8 TiB at 1000 MB/s/TiB → 4.8 GB/s

**Answer:** B

**Explanation:** Aggregate throughput = capacity × tier. 64 TiB × 1000 MB/s/TiB = 64 GB/s and is the closest fit for 30 TB of actual data without over-provisioning capacity. Option C also hits 64 GB/s but doubles capacity (and storage cost) for the same throughput. Option A under-provisions, and option D is far short.

---

## Q26 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the FSx for NetApp ONTAP exam trap

A bank has 80 TB of training data on an on-prem NetApp cluster. A solution architect proposes: "use FSx for NetApp ONTAP in AWS, replicate from on-prem via SnapMirror, then mount the ONTAP volume directly as a SageMaker training input." What is wrong with this proposal?

- A. Nothing — this is the canonical pattern.
- B. SageMaker's `FileSystemDataSource.FileSystemType` accepts only `EFS` and `FSxLustre`; FSx for NetApp ONTAP cannot be mounted directly as a SageMaker training input. The bridge is to stage via DataSync to S3 and read from S3 with File/FastFile/Pipe mode.
- C. ONTAP is multi-cloud only and cannot run on AWS.
- D. SnapMirror is not supported on FSx for NetApp ONTAP.

**Answer:** B

**Explanation:** Although the exam guide names FSx for NetApp ONTAP in Task 1.1, the SageMaker training-job API does not accept it as a `FileSystemType` — only EFS and FSxLustre are valid enums. The correct architecture is to lift-and-shift to FSx ONTAP, then stage via DataSync (NFS-to-S3) to an S3 bucket, then point SageMaker training at S3.

---

## Q27 — Domain 1: Data Preparation for Machine Learning
**Objective:** Compare EFS, FSx for Lustre, and EBS for ML training scenarios

A hyperparameter tuning job runs 40 parallel trials, each reading a small shared baseline dataset and writing trial-specific checkpoints that must be visible to a result-aggregation job. Which storage best fits?

- A. S3 + FastFile mode for the baseline read; EFS for the shared writable checkpoint directory.
- B. FSx for Lustre Scratch 2 only.
- C. EBS gp3 only (per-instance).
- D. S3 Glacier Instant Retrieval for checkpoints.

**Answer:** A

**Explanation:** EFS provides multi-AZ POSIX semantics with concurrent multi-client write access — perfect for shared HPO checkpoints. FastFile mode lazily reads the baseline data from S3 without download cost. FSx Lustre is single-AZ and the 1.2 TiB minimum is wasteful for small baselines. EBS is per-instance and cannot be shared across trial workers. Glacier is for archive, not active checkpoints.

---

## Q28 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the hidden cost of File mode on a large dataset

A team uses S3 + File mode to train on a 5 TB dataset across a 4-node `ml.p4d.24xlarge` cluster ($131/hr cluster cost). What is the predictable hidden cost they want to avoid?

- A. Per-GB S3 storage fees for the duration of training
- B. ~3.5 hours of GPU idle time during the upfront sync, billing ~$459 of cluster compute before the first epoch
- C. CloudTrail data-event charges for every GET
- D. KMS Decrypt charges on EBS volumes

**Answer:** B

**Explanation:** File mode downloads the full sharded dataset to each instance's EBS before training starts; with 5 TB sharded across 4 nodes at ~100 MB/s per instance, the download burns ~3.5 hours of cluster billing at $131/hr ≈ $459. FastFile or FSx Lustre avoid that idle cost. CloudTrail data events apply to FastFile per-GET, not File mode bulk sync.

---

## Q29 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick between FastFile and FSx for Lustre on a small-file workload

A vision training job reads millions of <10 MB image files in random shuffle order across 16 GPUs. The team tried FastFile and saw per-epoch time stretch by 50% with `SlowDown` errors. What is the structurally correct next step?

- A. Increase EBS volume size on each instance.
- B. Move to FSx for Lustre Persistent with an S3 DRA — Lustre handles millions of small files at parallel-filesystem throughput, while FastFile's per-object GET overhead destroys small-file throughput.
- C. Switch to S3 Glacier Instant Retrieval.
- D. Enable Bucket Keys.

**Answer:** B

**Explanation:** FastFile excels at sequential reads over large files but struggles with millions of small files because each read is a per-object S3 GET. The AWS-recommended path for many-small-files distributed deep learning is FSx for Lustre, which delivers ~2× speedup or more on small-file ResNet-style epochs. EBS, Glacier, and Bucket Keys do not address the per-object overhead.

---

## Q30 — Domain 1: Data Preparation for Machine Learning
**Objective:** Compare KDS On-Demand modes and pick a cost-saving option

A clickstream pipeline runs at a steady 50 MB/s with hourly spikes to 200 MB/s and has 25 EFO consumers (real-time scoring, audit, archival, etc.). Which Kinesis Data Streams capacity option is cheapest while supporting low-latency multi-consumer fan-out?

- A. Provisioned with 50 shards and 25 EFO consumers (each adding per-shard-hour and per-GB delivered)
- B. On-Demand Standard
- C. On-Demand Advantage (committed throughput floor with free EFO and EFO consumer limit raised to 50)
- D. Firehose Direct PUT only

**Answer:** C

**Explanation:** KDS On-Demand Advantage (November 2025) targets exactly this shape — consistent throughput with spikes and many EFO consumers. EFO is included free instead of per-shard-hour, and the EFO consumer cap rises from 20 to 50. Provisioned with 25 EFO consumers stacks per-consumer-shard-hour fees. Firehose lacks replay and multi-consumer fan-out.

---

## Q31 — Domain 1: Data Preparation for Machine Learning
**Objective:** Compute KDS shard requirements for a sustained workload

A producer sustains 12 MB/s of writes into a KDS Provisioned stream. The team plans no enhanced fan-out. What is the minimum shard count and the typical fix when one shard becomes "hot"?

- A. 4 shards; enable adaptive capacity
- B. 12 shards; redesign the partition key to a high-cardinality value such as `userId` if traffic is concentrated on one key
- C. 50 shards; switch to Pipe mode
- D. 1 shard; rely on EFO

**Answer:** B

**Explanation:** Each shard supports 1 MB/s of writes, so a 12 MB/s sustained workload needs at least 12 shards. The "hot shard" symptom (one shard at 950 KB/s while others idle) is almost always a low-cardinality partition key; the fix is to use a high-cardinality key like `userId` or `transactionId`. Adaptive capacity is a DynamoDB feature, not KDS.

---

## Q32 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish EFO from shared fan-out latency and protocol

Which statement about Kinesis Data Streams fan-out is **correct**?

- A. Shared fan-out uses push (SubscribeToShard HTTP/2) with ~70 ms latency; EFO uses pull (GetRecords) with ~200 ms latency.
- B. Enhanced fan-out gives each consumer a dedicated 2 MB/s pipe per shard via the `SubscribeToShard` HTTP/2 push API with ~70 ms latency; shared fan-out shares a single 2 MB/s budget per shard across all consumers using polled GetRecords (~200 ms).
- C. Both are pull-based and have identical latency.
- D. EFO removes the 2 MB/s per-shard read budget entirely.

**Answer:** B

**Explanation:** EFO is push-based via `SubscribeToShard` HTTP/2 streaming with ~70 ms end-to-end latency and a dedicated 2 MB/s per-consumer pipe per shard. Shared fan-out is pull-based via GetRecords polling at ~200 ms, sharing the 2 MB/s per shard across all consumers. Reversing the protocols (option A) is a classic trap.

---

## Q33 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall where KCL stores consumer checkpoints

The Kinesis Client Library (KCL) persists each consumer's "last processed sequence number" to which AWS service?

- A. S3
- B. DynamoDB
- C. Inside the Kinesis stream itself
- D. Glue Data Catalog

**Answer:** B

**Explanation:** KCL checkpoints per-shard cursors to DynamoDB so a crashed worker resumes where it left off. Common wrong answers are S3 (that's Flink's checkpoint store) and "inside the stream" (that's Kafka with `__consumer_offsets`).

---

## Q34 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply the Firehose buffering floor to a latency-sensitive ML scenario

A fraud team needs a sub-second feature update from a card-swipe stream into the SageMaker Feature Store online store. A teammate proposes Amazon Data Firehose → S3 → Feature Store sync. Why is this wrong?

- A. Firehose does not support S3 destinations.
- B. Firehose buffers for at least 60 seconds (S3 destination), making sub-second latency impossible; use KDS + Lambda or KDS + MSAF instead for sub-second feature updates.
- C. Feature Store cannot receive features from Firehose at all.
- D. S3 cannot store feature records.

**Answer:** B

**Explanation:** Firehose's S3 destination has a minimum buffer interval of 60 seconds (max 900 s), so end-to-end latency is at least one minute regardless of how the marketing copy reads. For sub-second updates, the canonical pattern is KDS + Lambda (or KDS + MSAF) writing directly to the online store via `PutRecord`. Firehose is correct for *minutes-fresh* offline-store landings.

---

## Q35 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply Firehose's JSON-to-Parquet conversion correctly

A team wants streaming JSON click events landed in S3 as Parquet, partitioned by `event_type`, queryable from Athena with no consumer code. Which two Firehose features are required? **(Select TWO)**

- A. Record format conversion using the AWS Glue Data Catalog schema (JSON → Parquet, +$0.018/GB)
- B. Dynamic partitioning configured at stream creation time using a low-cardinality key like `event_type`
- C. Pipe mode
- D. Provisioned shards
- E. AugmentedManifestFile

**Answer:** A, B

**Explanation:** Firehose format conversion pulls the schema from Glue Data Catalog and writes Parquet directly. Dynamic partitioning templatizes the S3 prefix with record fields like `event_type=login/year=...`. Both must be enabled together for the "land JSON as queryable partitioned Parquet" pattern. Dynamic partitioning cannot be added later — it must be enabled at stream creation. Pipe mode, shards, and AugmentedManifestFile are unrelated to Firehose.

---

## Q36 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the Firehose dynamic-partitioning small-files trap

A team configures Firehose dynamic partitioning by `user_id` for a B2C app with 5 million daily active users. Athena query performance collapses and S3 LIST costs spike. What is the root cause?

- A. Partitioning by a high-cardinality column (5M values) produces millions of tiny files that never fill the buffer.
- B. Glue Schema Registry rejected the schema.
- C. KDS On-Demand cannot feed Firehose.
- D. Firehose lacks an S3 destination.

**Answer:** A

**Explanation:** Dynamic partition cardinality must be bounded and small — `event_type`, `region`, `tenant_id` work; `user_id`, `session_id`, `transaction_id` do not. With 5M partitions, most buffers never reach the 128 MB or 900 s threshold and Firehose writes millions of sub-KB files, exploding both LIST cost and per-file Athena overhead.

---

## Q37 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose MSAF for stateful streaming aggregation

A team needs a rolling 1-hour count of failed logins per user, with exactly-once semantics and sub-second latency. Which AWS-native service is the right answer?

- A. Lambda with KDS event source mapping
- B. Glue Crawler
- C. Amazon Managed Service for Apache Flink (MSAF) using the DataStream API on a KDS source
- D. Firehose with Lambda transform

**Answer:** C

**Explanation:** Stateful event-time windowed aggregations with exactly-once semantics are MSAF (Flink) territory. Lambda is stateless and at-least-once. Firehose has no windowing. Glue Crawlers infer schemas — not streaming aggregations.

---

## Q38 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall the MSAF KPU billing unit

What does one **Kinesis Processing Unit (KPU)** include?

- A. 1 vCPU + 4 GB RAM + 50 GB durable application storage, billed per KPU-hour
- B. 1 shard of write capacity + 2 MB/s read
- C. 1 SageMaker training instance hour
- D. 1 GB of Firehose ingestion

**Answer:** A

**Explanation:** A KPU = 1 vCPU + 4 GB RAM + 50 GB application storage at ~$0.11/hr in us-east-1. MSAF Studio notebooks bill per KPU-hour while running; a "small" production app uses 2–4 KPUs minimum ($160–$320/month). Shard math is KDS; the others are unrelated services.

---

## Q39 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish MSK Provisioned and MSK Serverless

A bank migrates an on-prem Kafka workload with Debezium CDC connectors and Kafka Streams apps; sustained throughput is 80 MB/s with spikes to 200 MB/s and 30-day topic retention. Which AWS service?

- A. MSK Serverless (limited to ~200 MB/s and certain admin APIs missing)
- B. MSK Provisioned (Standard or Express brokers) with MSK Connect + Debezium plugin
- C. KDS On-Demand (no Kafka API compatibility)
- D. Firehose (no replay)

**Answer:** B

**Explanation:** Workloads that use open-source Kafka ecosystem features (Kafka Streams, Debezium, MirrorMaker, custom plugins) plus sustained > 200 MB/s and long retention need MSK Provisioned. MSK Serverless caps around 200 MB/s and lacks some admin features. KDS does not speak the Kafka wire protocol. Firehose has no replay.

---

## Q40 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the Feature Store two-sided write pattern

To eliminate training/serving skew between an online and offline feature store, what is the AWS-recommended pattern for streaming features?

- A. Have the producer write only to the offline store; sync nightly to the online store via Glue.
- B. Use the *same* compute step (Flink or Lambda) to write to the online store via `PutRecord` and to land raw/computed records via Firehose → S3 / offline store, ensuring byte-identical features in both lanes.
- C. Maintain two independent pipelines with different transforms.
- D. Use Firehose to deliver directly to a DynamoDB online store.

**Answer:** B

**Explanation:** Training/serving skew is the silent killer when offline and online features diverge. The fix is a single compute step that writes to both stores from the same stream — Feature Store auto-syncs from online to offline, but for high-volume streams writing offline directly via Firehose is more efficient and equally consistent provided the same transform feeds both sides.

---

## Q41 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the right Glue Crawler `UpdateBehavior` symptom

A new column appears in source files but does not show up in Athena. The Crawler logs confirm the column was detected. Which Crawler setting most likely caused this?

- A. `RecrawlPolicy=CRAWL_EVERYTHING`
- B. `SchemaChangePolicy.UpdateBehavior=LOG` (the Crawler logs the diff but does not update the Catalog)
- C. `DeleteBehavior=DEPRECATE_IN_DATABASE`
- D. `RecrawlPolicy=CRAWL_NEW_FOLDERS_ONLY` with the column in an existing folder

**Answer:** B

**Explanation:** `UpdateBehavior=LOG` tells the Crawler to log schema diffs without updating the Catalog table. To propagate schema changes, use `UpdateBehavior=UPDATE_IN_DATABASE` (the default). `DeleteBehavior` controls partition cleanup. `CRAWL_NEW_FOLDERS_ONLY` is fine for new columns in already-known folders because the column appears inside files Glue still reads.

---

## Q42 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify Crawler anti-pattern for Iceberg tables

A team uses an hourly Glue Crawler against an Iceberg table. The bill is high and schema changes from Spark writes are sometimes overwritten by the Crawler. What is the AWS-recommended pattern?

- A. Keep the Crawler hourly; this is the canonical Iceberg integration.
- B. Drop the Crawler — Iceberg manifests carry the schema inline and the producing job already registers the table; AWS recommends `CREATE TABLE ... USING ICEBERG` with explicit DDL.
- C. Switch to `CRAWL_EVERYTHING` to refresh more aggressively.
- D. Move the Iceberg table to OpenSearch.

**Answer:** B

**Explanation:** For Iceberg, Hudi, and Delta tables, the engine self-registers schema through its own manifests/transaction log. Running a Glue Crawler on top is a documented anti-pattern that wastes DPU-hours (10-min minimum charge per crawl ≈ $5,400/month for 50 sources hourly) and can overwrite the producing job's schema decisions.

---

## Q43 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall the Glue Schema Registry compatibility for old data + new fields

A regulated stream must support both old consumers reading new data and new consumers reading all historical data, going back to the first schema version. Which compatibility mode?

- A. NONE
- B. BACKWARD
- C. FORWARD
- D. FULL_ALL

**Answer:** D

**Explanation:** FULL_ALL enforces both BACKWARD and FORWARD compatibility against *all* prior schema versions, not just the most recent one. BACKWARD/BACKWARD_ALL allow only "new consumer reads old data"; FORWARD allows the opposite. NONE skips checks entirely. The "audit-traceable evolution against full history" pattern is FULL_ALL.

---

## Q44 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize Athena's $/TB-scanned cost model and the highest-ROI cost lever

An Athena dashboard scans 15 TB of unpartitioned CSV per query at $5/TB. What is the highest-ROI two-step fix?

- A. Enable Athena Query Result Reuse only
- B. Convert the table to Snappy-Parquet partitioned by the most common filter column (e.g., date); per-query scan typically drops 99%+
- C. Switch to Athena Provisioned Capacity at $0.30/DPU-hour 24/7
- D. Move the data to Glacier Deep Archive

**Answer:** B

**Explanation:** Partition pruning + columnar conversion is the canonical Athena cost lever — published customer cases show $45,000/month dropping to ~$150/month from this single change. Result Reuse caches identical queries but cannot save you from a full-scan baseline. Provisioned Capacity bills 24/7 and is wasteful below ~40% utilization. Glacier breaks the dashboard.

---

## Q45 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use Athena CTAS to convert raw to columnar

A pipeline writes hourly JSON into S3. A data scientist wants Athena queries at minimum scan cost and minimal operational overhead. Which is the canonical AWS pattern?

- A. Run a SageMaker Processing job nightly to convert JSON to CSV
- B. Athena `CREATE TABLE AS SELECT` with `format='PARQUET'`, `parquet_compression='SNAPPY'`, `partitioned_by=ARRAY['dt']`, then `INSERT INTO` on subsequent runs; register via Glue Data Catalog
- C. Glue 5.0 streaming job with custom Spark UDFs
- D. EMR Trino interactive queries directly on the JSON

**Answer:** B

**Explanation:** CTAS is Athena's canonical ETL primitive — one SQL statement reads JSON, writes Snappy-Parquet partitioned by `dt`, and registers the new table in the Catalog automatically. `INSERT INTO` extends it for incremental loads. The other options work but add cost or operational burden when CTAS suffices.

---

## Q46 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the Athena format that supports ACID MERGE and time travel

A team needs a training table queried from both Athena and Spark, supporting ACID `MERGE INTO` for daily CDC upserts plus `FOR TIMESTAMP AS OF` time travel. Which table format does Athena support for all of these?

- A. CSV
- B. Parquet (raw)
- C. Apache Iceberg
- D. Delta Lake (Athena's only support is read-only)

**Answer:** C

**Explanation:** Athena engine v3 supports Iceberg natively with `CTAS`, `INSERT`, `UPDATE`, `DELETE`, `MERGE INTO`, and time travel via `FOR VERSION AS OF` / `FOR TIMESTAMP AS OF`. Hudi and Delta are read-only on Athena; Parquet on its own has no ACID semantics. CSV is non-validated and offers no ACID at all.

---

## Q47 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply Lake Formation column- and row-level filters

A security team requires that a data analyst (a) can read only rows where `region='EU'` and (b) cannot see the `ssn` column. Which two Lake Formation primitives satisfy this with least operational overhead? **(Select TWO)**

- A. A row-filter expression `region = 'EU'` in a Lake Formation data filter applied to the table.
- B. A column include/exclude list (excluding `ssn`) on the same data filter.
- C. An IAM bucket policy denying `s3:GetObject` on partitions where `region <> 'EU'`.
- D. S3 Object Lock Compliance on the `ssn` partition.
- E. KMS key deny statement scoped to the analyst's IAM principal.

**Answer:** A, B

**Explanation:** Lake Formation data filters combine a row predicate and a column include/exclude list, applied via `GRANT SELECT ON TABLE t USING DATA FILTER f`. IAM cannot filter rows or columns inside a Parquet file. The grant takes effect only after `IAMAllowedPrincipals` is revoked, since the legacy principal otherwise overrides Lake Formation. KMS and Object Lock operate on full objects, not columns or rows.

---

## Q48 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the `IAMAllowedPrincipals` antipattern

An engineer applies a Lake Formation column-level grant excluding `ssn`, but the analyst can still see the column when querying through Athena. What is the most likely cause?

- A. Athena engine v3 does not enforce Lake Formation grants.
- B. `IAMAllowedPrincipals` is still granted `Super` on the table, which overrides Lake Formation column-level grants.
- C. The Glue Crawler has not run today.
- D. The bucket policy is missing.

**Answer:** B

**Explanation:** New AWS accounts grant a virtual principal called `IAMAllowedPrincipals` `Super` on Catalog databases and tables for legacy compatibility. As long as that grant exists, Lake Formation grants are ignored. The fix is `REVOKE Super FROM 'IAMAllowedPrincipals' ON TABLE ...`. Athena engine v3 enforces LF; Crawler status is unrelated.

---

## Q49 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall Lake Formation Hybrid Access Mode

A team is gradually moving from IAM-based access to Lake Formation governance, but cannot afford to break existing IAM-driven pipelines overnight. Which feature allows both models to coexist per-database?

- A. Lake Formation Hybrid Access Mode
- B. Glue Data Quality DQDL
- C. Athena Provisioned Capacity
- D. Cross-account v3 RAM share

**Answer:** A

**Explanation:** Hybrid Access Mode (2023) lets a table support both Lake Formation grants (for newly onboarded principals) and IAM-based access (for legacy consumers) simultaneously, enabling incremental migration without breaking running jobs. The other options serve different purposes.

---

## Q50 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize that direct S3 access bypasses Lake Formation

After granting column-level access through Lake Formation, an engineer can still read the masked columns by downloading Parquet files directly from S3. Why, and how do you fix it?

- A. Lake Formation does not encrypt or mask the underlying Parquet bytes; it enforces grants only through registered engines (Athena, Spectrum, EMR, Glue, SageMaker Lakehouse). Revoke direct `s3:GetObject` IAM permissions on the bucket and require principals to access through Lake Formation–vended credentials.
- B. Add a KMS deny statement on the S3 bucket.
- C. Move the data to Glacier Deep Archive.
- D. Disable Glue Catalog.

**Answer:** A

**Explanation:** Lake Formation grants are enforced inside query engines, not on the bytes. A principal with raw `s3:GetObject` on the underlying bucket reads the Parquet directly and bypasses column/row filters. Best practice: register the S3 location with Lake Formation and remove IAM `s3:GetObject` for analytical principals.

---

## Q51 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use Glue Data Quality DQDL at the right pipeline stage

A team wants to block the training pipeline from consuming batches with missing `customer_id` or out-of-range `amount_cents`. Where should the rules run?

- A. SageMaker Model Monitor data-quality job at inference time
- B. Glue Data Quality `EvaluateDataQuality` transform inside the ingest Glue job, routing failures to quarantine and emitting `glue.data.quality.rules.failed` to CloudWatch to gate the SageMaker Pipelines training step
- C. Athena CTAS with a `WHERE` clause
- D. DynamoDB conditional writes

**Answer:** B

**Explanation:** Glue Data Quality runs DQDL rules (`Completeness "customer_id" = 1.0`, `ColumnValues "amount_cents" between 0 and 10000000`) inside an ingest job. CloudWatch metric `glue.data.quality.rules.failed` gates downstream Pipelines. Model Monitor watches inference traffic, not training inputs. Athena `WHERE` filters silently rather than alerting; DynamoDB writes are unrelated.

---

## Q52 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize Glue 5.0's default-timeout change

A Glue 5.0 streaming job that previously ran indefinitely under Glue 3.0 now terminates after 8 hours unless reconfigured. What changed?

- A. Glue 5.0 reduced the default job timeout from 48 hours to 8 hours.
- B. Glue 5.0 removed streaming-job support.
- C. Glue 5.0 only supports Python 2.
- D. Glue 5.0 requires manual catalog updates.

**Answer:** A

**Explanation:** Glue 5.0 dropped the default `Timeout` from the legacy 48-hour value to 8 hours. Long-running streaming jobs must explicitly set `Timeout` (or pin to a higher value at job creation). The other options are false.

---

## Q53 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the JDBC bookmark requirement

A Glue job uses a JDBC bookmark to incrementally ingest only new rows from an RDS table. The bookmark silently fails to advance. Which precondition is most likely violated?

- A. The job is missing a `glue:JobBookmark` IAM action.
- B. The source table must have a **monotonically increasing key** (e.g., autoincrement `id` or `updated_at` timestamp) that Glue can compare against the last-known bookmark value.
- C. The data must be Parquet to support bookmarks.
- D. Bookmarks require Spark 2.4 or older.

**Answer:** B

**Explanation:** Glue JDBC bookmarks require a monotonic key column to track "last processed value." Tables without such a column (or with values that don't strictly increase) cause bookmark logic to silently fail or reprocess. The IAM action is `glue:Get*` plus the role's regular permissions; format and Spark version are unrelated.

---

## Q54 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick the EMR deployment model for a bursty Spark batch workload

A startup runs a Spark feature pipeline four times daily, has no ops engineer, and wants zero bill between runs. Which EMR deployment model?

- A. EMR on EC2 with Spot task fleets and managed scaling
- B. EMR Serverless with on-demand capacity and no pre-initialized warm pool
- C. EMR on EKS with a self-managed Spark operator
- D. EMR on EC2 with multi-master HA

**Answer:** B

**Explanation:** EMR Serverless's per-second billing of just-used vCPU/memory matches a bursty workload — no cluster between runs, no idle bill. With no pre-init pool the cold start is 60–120 s, acceptable for batch. EMR on EC2 is cheaper only above ~70% utilization; EMR on EKS adds Kubernetes ops complexity not needed here.

---

## Q55 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize EMR on EKS for shared-GPU multi-tenancy

An ML platform team has standardized on Kubernetes and wants Spark ETL pods to share the same GPU node pool as SageMaker training pods. Which EMR mode fits?

- A. EMR Serverless
- B. EMR on EC2
- C. EMR on EKS with virtual clusters per namespace
- D. Glue 5.0

**Answer:** C

**Explanation:** EMR on EKS turns each EKS namespace into a virtual cluster and submits Spark jobs as Kubernetes CRDs. Spark pods coexist with SageMaker / microservice pods on the same nodes. EMR Serverless is Spark/Hive-only with no GPU sharing; EMR on EC2 runs its own dedicated EC2 cluster; Glue does not run on K8s.

---

## Q56 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply Spot posture and instance-fleet allocation to EMR-on-EC2

Which two configurations are AWS-recommended for cost-resilient EMR-on-EC2 with Spot? **(Select TWO)**

- A. Master and Core nodes On-Demand; Task nodes Spot.
- B. Use Instance Fleets (not uniform Instance Groups) for the Task tier with 10+ instance types across 3+ AZs.
- C. Set Master to Spot to maximize savings.
- D. Use uniform Instance Groups with a single instance type per group for predictable Spot behavior.
- E. Use `lowest-price` allocation strategy on Task fleets.

**Answer:** A, B

**Explanation:** Master loss kills the cluster (Master always On-Demand). Core nodes host HDFS replicas (also On-Demand for HDFS-resident clusters). Task nodes are stateless and ideal for Spot. Instance Fleets with `price-capacity-optimized` (not `lowest-price`) across 10+ types and 3+ AZs is the AWS-recommended diversification strategy — uniform Groups are single-type per group and offer no diversification.

---

## Q57 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply the EMR 6.x YARN node-labels fix

After migrating from EMR 5.x to EMR 6.x, Spark jobs randomly fail when task-node Spot instances are reclaimed. What configuration restores Spot resilience?

- A. Enable `yarn.node-labels.enabled=true` and set `yarn.node-labels.am.default-node-label-expression=CORE` to pin the Spark Application Master to On-Demand Core nodes.
- B. Move all task nodes to On-Demand.
- C. Set `spark.executor.instances=1`.
- D. Disable HDFS replication.

**Answer:** A

**Explanation:** YARN node labels were on by default in EMR 5.19+ and disabled by default in EMR 6.x. Without the AM-pin-to-CORE setting, the Spark Application Master can land on a Spot task node; when that node is reclaimed, the whole application dies. Enabling node labels and pinning AM to CORE is the documented fix.

---

## Q58 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish EMRFS from HDFS for durable outputs

A pipeline writes final feature outputs to `hdfs:///features/v17/` because "HDFS is faster than S3." Two days later the cluster auto-terminates and the next training job fails with "path not found." What should have happened?

- A. Outputs should have been written to **EMRFS (S3)** via `s3://bucket/features/v17/`. HDFS lifetime is bound to the cluster; terminating the cluster wipes it. S3 decouples storage from compute and lets SageMaker, Athena, and Glue Catalog all consume the same features.
- B. The team should have disabled auto-termination forever.
- C. HDFS replication factor 5 would have saved the data.
- D. The team should have used Pipe mode to write to HDFS.

**Answer:** A

**Explanation:** HDFS on EMR is ephemeral by design — best for shuffle/spill, never for durable outputs. EMRFS writes through to S3, which survives cluster termination and is the canonical source for downstream training jobs. Replication factor cannot save data after cluster termination.

---

## Q59 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick the SageMaker Pipelines step type for big-data Spark preprocessing

A SageMaker Pipeline must preprocess 4 TB of Parquet to 800 GB of Iceberg-formatted features in S3, runs nightly, requires Iceberg 1.5.x, and must not require the ML team to manage standing infrastructure. Which step type?

- A. `EMRStep` against a long-running EMR-on-EC2 cluster
- B. `EMRServerlessStep` pointed at an EMR Serverless Application
- C. `ProcessingStep` with `PySparkProcessor`
- D. `LambdaStep`

**Answer:** B

**Explanation:** `EMRServerlessStep` is the AWS-blessed combo for scheduled big-data Spark inside a SageMaker Pipeline without owning a cluster. `EMRStep` requires referencing an existing cluster (or provisioning a transient one with full configuration). `PySparkProcessor` is best for small/medium preprocessing inside SageMaker; at this scale Serverless with Shuffle-Optimized disks wins. Lambda has a 15-minute hard limit.

---

## Q60 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify DynamoDB's per-partition hard ceiling

A DynamoDB table is provisioned at 200,000 RCU. Average load is 40,000 RPS spread across keys, but during a flash sale one `merchant_id` receives 8,000 RPS while others receive <50. The team sees `ProvisionedThroughputExceededException` on that merchant's items. What is the correct fix?

- A. Enable adaptive capacity (it already is, on On-Demand and Provisioned).
- B. Raise total RCU to 400,000.
- C. Redesign the partition key for higher cardinality — e.g., add a write-shard suffix (`merchant_id#0..99`) or pick a more granular key — because each physical partition is capped at 3,000 RCU regardless of total table capacity.
- D. Switch to Aurora pgvector.

**Answer:** C

**Explanation:** Each DynamoDB partition is limited to 3,000 RCU / 1,000 WCU / 10 GB. A hot key concentrates traffic on one partition; no amount of total-table capacity overcomes the per-partition ceiling. Adaptive capacity mitigates skew up to the limit but cannot exceed it. The structural fix is high-cardinality partition keys or write-sharding.

---

## Q61 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall the SageMaker Feature Store online tier substrate

A scenario says "single-digit-millisecond feature lookups for inference." Where do those features live?

- A. S3 Standard with FastFile mode
- B. DynamoDB (which is also what backs the SageMaker Feature Store online tier)
- C. Redshift Serverless
- D. Glacier Instant Retrieval

**Answer:** B

**Explanation:** DynamoDB's 2–10 ms point-lookup latency makes it the canonical online feature store, and SageMaker Feature Store's online tier is DynamoDB managed by SageMaker. S3 is 50–200 ms (too slow for online inference). Redshift is for analytical queries. Glacier Instant Retrieval is for infrequent storage retrieval.

---

## Q62 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply DAX correctly versus ElastiCache for ML caching

Which caching scenario is best served by **ElastiCache Redis** rather than DynamoDB DAX?

- A. Reference catalog reads keyed by item ID with near-100% hit rate, all backed by DynamoDB
- B. Feature cache backed by mixed sources (DynamoDB + RDS + computed values) with per-key TTL and sorted-set top-K features
- C. Strongly-consistent reads against DynamoDB
- D. Microsecond reads on DynamoDB-only data

**Answer:** B

**Explanation:** DAX is a DynamoDB-specific write-through cache and supports only eventually-consistent reads on cached data. ElastiCache is the general-purpose answer when cache contents come from heterogeneous sources, when per-key TTL is needed, or when Redis-native data structures (sorted sets, streams, HyperLogLog) are required. For DynamoDB-only reference caching, DAX is fine.

---

## Q63 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize Aurora zero-ETL constraints

A bank proposes Aurora PostgreSQL (us-east-1) zero-ETL to a Redshift cluster (us-west-2) for near-real-time analytics. Why does this proposal fail?

- A. Aurora PostgreSQL is not a supported zero-ETL source.
- B. Aurora zero-ETL to Redshift is **same-Region only**; cross-Region requires DMS or Aurora Global Database staging.
- C. Aurora zero-ETL requires Aurora Limitless as the source.
- D. The Redshift cluster must be Provisioned, never Serverless.

**Answer:** B

**Explanation:** A documented hard limitation of Aurora zero-ETL to Redshift is that source and target must be in the same Region. Aurora PostgreSQL is supported (since 2024). Aurora Limitless is *not* supported as a zero-ETL source. The target may be Redshift Provisioned or Serverless.

---

## Q64 — Domain 1: Data Preparation for Machine Learning
**Objective:** Differentiate Multi-AZ standby from a read replica

A team plans to offload heavy feature-extraction queries to a "Multi-AZ standby" of their RDS PostgreSQL primary to avoid impacting OLTP. What is wrong with this plan?

- A. Multi-AZ standby is for failover only and is not readable; offload queries to a **read replica** (a separate construct, up to 5 per source for non-Aurora RDS) or an **Aurora Replica** for Aurora.
- B. Multi-AZ standby costs more than read replicas.
- C. Multi-AZ standby supports only Oracle.
- D. Multi-AZ standby requires Direct Connect.

**Answer:** A

**Explanation:** RDS Multi-AZ standby is a synchronous failover target — not a readable replica. To split read traffic from OLTP you provision read replicas (or Aurora Replicas, up to 15 per cluster). Confusing the two is one of the most common RDS exam traps.

---

## Q65 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use Redshift ML correctly for analyst-driven scoring

A BI analyst needs to score 200M customers nightly with a churn model using SQL only. What is the AWS-native canonical path?

- A. Redshift ML `CREATE MODEL churn TARGET churned ...` (trains via SageMaker Autopilot behind the scenes) followed by `SELECT predict_churn(...) FROM customers` in SQL
- B. SageMaker real-time endpoint deployed by the analyst from a Jupyter notebook
- C. EMR Spark MLlib job orchestrated by Step Functions
- D. Bedrock Knowledge Base over the customer table

**Answer:** A

**Explanation:** Redshift ML `CREATE MODEL` trains via SageMaker Autopilot under the hood and compiles a local Redshift function for inference. The analyst writes SQL, never Python. SageMaker endpoints require IAM and ops expertise; EMR/Step Functions are far heavier; Bedrock KB is for RAG over text, not structured scoring.

---

## Q66 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the Redshift ML BYOM 370-second timeout

A Redshift ML BYOM model invokes a SageMaker endpoint for nightly batch scoring. Intermittent failures appear on the largest batches. What is the canonical fix?

- A. Increase the Redshift cluster size.
- B. Lower `MAX_BATCH_ROWS` on the Redshift ML model definition so each invocation completes within the 370-second timeout that Redshift enforces on remote endpoint calls; optionally scale the SageMaker endpoint to handle more requests in parallel.
- C. Move the model to a Bedrock external model.
- D. Re-train with `AUTO ON`.

**Answer:** B

**Explanation:** Redshift ML BYOM batches 50,000–220,000 rows per call by default and times out at 370 seconds. Large or slow endpoints exceed that ceiling. Lowering `MAX_BATCH_ROWS` reduces per-call latency below the timeout; scaling the endpoint absorbs more concurrent calls. Cluster size and training mode are unrelated to the timeout.

---

## Q67 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose OpenSearch HNSW parameters for vector search

A team builds a RAG application with 1,536-dimensional Bedrock Titan embeddings on OpenSearch with FAISS HNSW. Which parameter set is the production-grade default for higher recall at indexing time?

- A. `m=8, ef_construction=64, ef_search=10`
- B. `m=16, ef_construction=200, ef_search=100`
- C. `m=64, ef_construction=1024, ef_search=1024`
- D. `m=2, ef_construction=2, ef_search=2`

**Answer:** B

**Explanation:** `m=16, ef_construction=200, ef_search=100` is the widely cited production starting point for FAISS HNSW. Lower values sacrifice recall; very high values hurt build time, query latency, and memory footprint with diminishing returns. Tune from this baseline by measuring NDCG@10 on a labeled query set.

---

## Q68 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall the OpenSearch vector dimension limit

A team wants to index 16,384-dimensional embeddings from a custom transformer in an OpenSearch `knn_vector` field. What happens?

- A. It works fine — there is no dimension limit.
- B. Indexing fails — `knn_vector` fields are capped at 10,000 floats per vector. The team must use a different engine or reduce dimensionality (PCA, autoencoder, smaller model).
- C. It works only with the Lucene engine.
- D. It requires OpenSearch Serverless.

**Answer:** B

**Explanation:** OpenSearch's `knn_vector` field type is capped at 10,000 floats per vector regardless of engine (FAISS/NMSLIB/Lucene). Standard embedding models — Bedrock Titan (1024/1536), Cohere (1024), OpenAI text-embedding-3-large (3072) — fit comfortably. Beyond 10,000 dims, switch vector store or reduce dimensionality.

---

## Q69 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the zero-ETL replacement for DynamoDB-to-OpenSearch CDC

A product catalog lives in DynamoDB; an OpenSearch index must reflect updates within seconds for product search and k-NN reranking. The team is on the prior DynamoDB Streams → Lambda → OpenSearch reindex pattern. Which 2024 feature simplifies this?

- A. DynamoDB → OpenSearch zero-ETL integration (March 2024 GA), which auto-indexes DynamoDB items into an OpenSearch domain or Serverless collection without Lambda.
- B. DynamoDB Streams → Firehose → OpenSearch (Firehose has no OpenSearch destination)
- C. DynamoDB Global Tables → OpenSearch
- D. Aurora zero-ETL to OpenSearch

**Answer:** A

**Explanation:** The March 2024 GA of DynamoDB → OpenSearch zero-ETL eliminates the prior Streams + Lambda pattern. Firehose *does* have an OpenSearch destination but that path requires routing through a different stream; the cleanest replacement for a DynamoDB-as-source pipeline is the native zero-ETL integration. Aurora zero-ETL targets Redshift and SageMaker Lakehouse, not OpenSearch.

---

## Q70 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose a cost-optimized vector store for a small RAG knowledge base

A Bedrock Knowledge Base on OpenSearch Serverless holds 280,000 chunks and serves 40 queries/day. The bill is $700/month for the vector store. The team can tolerate a 10–15 second cold start. Which migration target cuts the vector-store bill by ~10× without breaking the KB?

- A. Amazon Aurora Serverless v2 with the `pgvector` extension — scales to 0 ACU when idle, supports `cosine`/`l2`/`inner_product` similarity, and is a supported Bedrock Knowledge Base vector store.
- B. OpenSearch Service Provisioned with `r6g.large.search` nodes (more expensive than Serverless).
- C. ElastiCache Redis with the `vss` module (not a Bedrock KB target).
- D. DynamoDB with cosine similarity in a Lambda (not a Bedrock KB target).

**Answer:** A

**Explanation:** Aurora Serverless v2 + `pgvector` is the AWS-supported Bedrock KB target for cost-sensitive RAG with <1M vectors. The OCU floor on OpenSearch Serverless bills $700/month even at zero queries; Aurora Serverless v2 scales to 0 ACU when idle, dropping the line to roughly $40–70/month. Provisioned OpenSearch is more expensive. ElastiCache and DynamoDB are not Bedrock KB targets.
## Q71 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose the right AWS Glue job runtime for a workload

A data engineer must apply a Hugging Face sentence-transformer model to every row of a 10-million-row product catalog stored in S3. The team is comfortable with pandas and scikit-learn but not Spark, and the workload is fundamentally a map-style per-row Python function. Which AWS Glue runtime is the best fit?

- A. Glue Spark (`glueetl`) with G.2X workers
- B. Glue Spark Streaming (`gluestreaming`) with G.025X workers
- C. Glue Python shell (`pythonshell`) at 1 DPU
- D. Glue Ray (`glueray`) with Z.2X workers

**Answer:** D
**Explanation:** Ray on Glue (GA June 2024) is specifically positioned for distributed Python — map-style Python over rows, parallel HPO, distributed inference — without writing Spark. Z.2X is the only worker type for Ray, with a 2-worker / 4-DPU minimum. Python shell (C) is single-node and cannot scale to 10M rows. Spark (A) works but the chapter explicitly says Ray wins when "I have a Python function and I need to fan it out" describes the problem. Streaming (B) is wrong — the source is batch S3, not Kinesis/MSK.

---

## Q72 — Domain 1: Data Preparation for Machine Learning
**Objective:** Right-size DPUs and pick worker types on Glue

A nightly Glue Spark job is configured with 20 × G.4X workers and runs for 45 minutes. The Spark UI shows that 3 of the 20 executors do 95% of the work and most others sit idle. The team also wants ~34% cost savings. Which configuration change is most appropriate?

- A. Enable Flex execution with the existing G.4X workers
- B. Switch to G.1X workers, enable Auto Scaling with `MaxWorkers=20`, and enable Flex
- C. Switch to G.1X workers, enable Auto Scaling, and keep Standard execution
- D. Upgrade to G.16X workers in us-west-1 to get more memory per executor

**Answer:** C
**Explanation:** Flex is incompatible with G.4X and larger workers AND incompatible with Auto Scaling — so B is wrong by validation. A is also wrong: Flex only supports G.1X and G.2X. C is correct: Auto Scaling fixes the over-provisioned-static-executor problem (AWS reports an 8.71 → 1.48 DPU-hour benchmark, ~83% reduction) without violating Flex constraints. D is wrong: G.16X is not available in us-west-1 (it's restricted to ~7 regions including us-east-1/2, us-west-2, eu-west-1, eu-central-1, eu-south-2, ap-northeast-1).

---

## Q73 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply Glue Flex execution for cost savings

A data engineer wants to use Glue Flex execution to cut costs on a nightly backfill job. Which configuration combination is valid?

- A. G.4X workers, Auto Scaling enabled, Flex execution class
- B. G.1X workers, Auto Scaling enabled, Flex execution class
- C. G.2X workers, Auto Scaling disabled, Flex execution class
- D. G.025X streaming workers, Auto Scaling disabled, Flex execution class

**Answer:** C
**Explanation:** Flex is supported only on G.1X and G.2X workers, batch Spark only, and is incompatible with Auto Scaling. Only C meets all three constraints. A fails because Flex doesn't support G.4X+. B fails because Flex is incompatible with Auto Scaling. D fails because G.025X is streaming-only, and Flex is batch-only.

---

## Q74 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use Glue job bookmarks correctly with JDBC sources

A Glue ETL job reads a JDBC table `orders` whose primary key is a UUID. Job bookmarks are enabled. Each run silently inserts the same rows twice or skips arbitrary windows of data. What is the root cause and the recommended fix?

- A. Bookmarks are broken in Glue 5.0; downgrade to Glue 4.0
- B. The bookmark key must be sequentially increasing or decreasing; UUIDs are non-monotonic — add an `updated_at TIMESTAMP` column and set it as the bookmark key
- C. Set `--max-concurrent-runs 5` so the bookmark advances more reliably
- D. Reset the bookmark before every run with `aws glue reset-job-bookmark`

**Answer:** B
**Explanation:** JDBC bookmarks track the maximum value of the bookmark key column seen in the previous run. The key must be monotonic (sequentially increasing or decreasing with no gaps). UUIDs and hash PKs are forever wrong for JDBC bookmarks — the chapter calls this out as the canonical exam trap. A is fabricated. C makes it worse (concurrent runs see the same bookmark state). D defeats the purpose of bookmarks (you'd reprocess everything every run).

---

## Q75 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize Glue 5.0 default timeout behavior

A team migrates a Glue 4.0 job that has reliably run for 12 hours nightly. After upgrading to Glue 5.0, the very first run in production fails at exactly 8 hours. What changed, and what is the fix?

- A. Glue 5.0 lowered the default `Timeout` from 2,880 minutes to 480 minutes; explicitly set `Timeout = 2880` (or higher) on the job
- B. Glue 5.0 reduced max DPU per worker; switch from G.2X to G.4X
- C. Spark 3.5.4 in Glue 5.0 has a hard 8-hour query limit; rewrite the job in Ray
- D. Glue 5.0 disables bookmarks by default; re-enable bookmarks on the job

**Answer:** A
**Explanation:** The chapter highlights this exact migration trap: Glue 5.0+ lowered the default Job timeout from 2,880 minutes (48 hr) to 480 minutes (8 hr). Long-running jobs that fit under the old 48-hr default now die at 8 hr. The one-line fix is to override the `Timeout` parameter explicitly. None of B, C, or D describe a real Glue 5.0 behavior.

---

## Q76 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose between DynamicFrame and DataFrame in Glue PySpark

A Glue Spark job ingests messy JSON event data where field types vary across rows (some events have `payload.amount` as a string, others as a long). Which approach is most appropriate?

- A. Read with `from_catalog()` as a DataFrame and call `df.cast()` on the column
- B. Read as a DynamicFrame, apply `ResolveChoice`, then convert via `toDF()` for the heavy transforms, then `fromDF()` to write
- C. Read as a DynamicFrame and never convert; DataFrames cannot handle nested JSON
- D. Use Glue Studio's visual ETL with no code

**Answer:** B
**Explanation:** This is the canonical Glue Spark pattern: DynamicFrame for source ingestion (lets Glue resolve choices on schema-drifting JSON), then `toDF()` for the heavy transform (uses Catalyst), then `fromDF()` to write back through Glue so Catalog updates and bookmarks work. A is wrong — a DataFrame enforces one type per column and fails on schema drift before you can cast. C is wrong: DataFrames handle nested JSON fine via Spark SQL. D doesn't solve the type-conflict problem.

---

## Q77 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the cost lever for partition-aware Glue Spark jobs

A Glue Spark job reads a Catalog-registered Parquet table that is partitioned by `year/month`. The team only needs May 2026 data, but the job currently reads the whole table and the bill is 100× what it should be. Which single change has the biggest cost impact?

- A. Switch from Glue 4.0 to Glue 5.0 for the 32% perf-cheaper benchmark
- B. Increase the number of workers from 10 to 50 so the scan finishes faster
- C. Add `push_down_predicate="year='2026' AND month='05'"` to the `create_dynamic_frame.from_catalog` call
- D. Switch to FastFile input mode on the consuming training job

**Answer:** C
**Explanation:** The chapter calls predicate pushdown "the single most impactful cost lever in Glue Spark." Wrong partition filters mean 100× the DPU-hours; pushing them down server-side prunes partitions before any data is scanned. A gives ~32% improvement, not 100×. B makes the bill worse (more workers reading the same wasted data). D is for training input, not the Glue job.

---

## Q78 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose between Glue workflows and Step Functions

A team needs to orchestrate a DAG of three Glue jobs plus one SageMaker Training job and one Lambda step, with cross-account access and a human approval gate. Which orchestrator is the right choice?

- A. Glue workflows — they are free and they handle SageMaker steps natively
- B. AWS Step Functions — first-class `Task` state for any AWS service, cross-account support, human approval via Callback task
- C. Glue triggers with conditional fan-in/fan-out
- D. EventBridge Pipes

**Answer:** B
**Explanation:** Glue workflows are free and visual but are Glue-only and have basic retry/error handling. Step Functions has first-class Task states for non-Glue services (Lambda, SageMaker, ECS), cross-account/cross-region support, and human-approval flows via Callback tasks. The chapter's rule of thumb: "Orchestrate only Glue jobs and crawlers, minimise cost" → Glue workflow. "Orchestrate Glue + Lambda + SageMaker training + manual approval" → Step Functions.

---

## Q79 — Domain 1: Data Preparation for Machine Learning
**Objective:** Diagnose VPC misconfiguration on Glue connections

A new Glue Spark job in a private VPC subnet hangs on its very first run and times out after 30 minutes with no useful logs. The IAM role on the job is correct, and credentials in Secrets Manager are valid. What is the most likely root cause?

- A. Glue 5.0 doesn't support VPC connections
- B. The subnet has no NAT Gateway and no S3 / Glue / Logs VPC endpoints, so the worker can't fetch its own script from S3
- C. The job is using G.025X workers which don't support VPC
- D. The IAM role is missing `glue:CreateJob`

**Answer:** B
**Explanation:** The chapter describes this as the #1 Glue networking failure mode: the job sits forever trying to fetch its own script. A VPC-attached Glue worker needs a NAT Gateway or Interface/Gateway endpoints for S3, glue, logs, sts, secretsmanager, and kms. A and C are fabricated; D is wrong because the job already started (so it can call CreateJob), it just can't reach S3 for the script.

---

## Q80 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose between Glue Studio visual ETL and PySpark scripts

A data analyst with no Spark experience needs to clean three Glue Catalog tables and produce a daily Parquet export. The platform team also requires that all production jobs be reviewed via pull request, unit-tested with `pytest`, and deployed via CDK. Which authoring surface is recommended?

- A. Glue Studio visual ETL only — it auto-generates the PySpark anyway
- B. PySpark script only — the analyst should learn Spark
- C. Glue Studio visual ETL for the first iteration, then export the generated PySpark, check it into Git, and own it as code in CI/CD
- D. AWS Glue DataBrew — it's the no-code option

**Answer:** C
**Explanation:** The chapter explicitly addresses this seam: Studio is great for prototyping by a non-Spark author, but production-grade pipelines almost always graduate to code mode (script in Git, PR review, unit tests with `aws-glue-libs` Docker, CDK deploy). Visual ETL is one-way — once you switch to script mode you can't return — so the workflow is "prototype visually, export script, own script." A misses the platform team's PR/test requirement. B ignores the analyst's skill set. D — DataBrew — is for no-code data prep but has no Spark, no bookmarks, and can't satisfy "petabyte ETL with predicate pushdown" workloads.

---

## Q81 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish GlueJobStep vs PySparkProcessor in SageMaker Pipelines

A data platform team owns an existing Glue job `customer_features_v3` that runs nightly with bookmarks and Auto Scaling. The ML team needs to invoke that job from a SageMaker Pipeline. Which step should they use?

- A. `ProcessingStep` with `PySparkProcessor` — it gives a single control plane
- B. `GlueJobStep` — invokes the existing Glue job by name/ARN
- C. `LambdaStep` that calls `boto3.client('glue').start_job_run()`
- D. `TrainingStep` with the Spark container

**Answer:** B
**Explanation:** `GlueJobStep` is purpose-built to invoke an existing Glue job inside a Pipeline. Pros: Glue manages the cluster, you keep your existing IAM/Catalog/bookmarks/Auto Scaling. The chapter's decision table maps "existing Glue job, owned by the data platform team" → `GlueJobStep`; "new Spark step, ML team owns end-to-end" → `PySparkProcessor`. A creates a duplicate Spark codebase. C works but loses native Pipeline lineage. D is for training jobs, not ETL.

---

## Q82 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize bookmark anti-patterns

(Select TWO) Which of the following will silently break Glue job bookmarks?

- A. Changing the source S3 path without changing `transformation_ctx`
- B. Setting `--max-concurrent-runs 5` on a bookmarked job
- C. Calling `job.commit()` at the end of the script
- D. Setting `Enable` as the bookmark mode
- E. Adding `push_down_predicate` to the source read

**Answer:** A, B
**Explanation:** A: the chapter spells out the change-path-without-changing-ctx war story — the old bookmark says "I processed up to time T in src_events" and the new path has no objects matching that timestamp, so Glue silently processes zero rows. B: concurrent runs see the same bookmark state at start, both process the same objects, and the later commit overwrites the earlier one — duplicates on one slice, missed processing on another. C is the correct way to advance the bookmark. D is the correct mode for incremental. E is independent of bookmarks (a separate cost lever).

---

## Q83 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall Glue Interactive Sessions cost behavior

A data scientist opens a Glue Interactive Session in SageMaker Studio at 10 DPU and forgets about it overnight (8 hours idle). The default idle timeout is 2,880 minutes. Approximately what does this cost?

- A. Free — Interactive Sessions don't bill until you execute code
- B. About $0.04 — billed only for the seconds of executed Python
- C. About $35 — billed at $0.44/DPU-hour for wall-clock session life
- D. About $440 — billed at the Provisioned-DPU rate

**Answer:** C
**Explanation:** The chapter calls this out directly: Interactive Sessions are billed at $0.44/DPU-hour for wall-clock session life, not just code execution. 10 DPU × 8 hr × $0.44 = $35.20. The default idle timeout is 2,880 minutes (8 hours), so the session sat the full duration. Mitigation: set `%idle_timeout 30` at session start. A is wrong by mechanism; B describes a different product; D is the wrong rate.

---

## Q84 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose between DataBrew and Glue Spark by persona

A compliance officer with no programming background must produce a monthly report listing all PII columns in a 200 GB claims dataset and produce a masked version for analytics. There is no Spark cluster and no data-engineering budget. Which AWS service is the right answer?

- A. AWS Glue Spark — fast, scalable, schema-aware
- B. AWS Glue DataBrew — Profile Job with PII statistics + Recipe Job with `CRYPTOGRAPHIC_HASH` and `MASK_DELIMITER`
- C. Amazon EMR Serverless — full Spark feature parity
- D. SageMaker Data Wrangler — visual ML data prep

**Answer:** B
**Explanation:** The persona discriminator is decisive: "business analyst / compliance officer / no code / PII compliance" → DataBrew. The chapter walks this exact Monday-morning compliance scenario: Profile Job (with PII statistics on) for the inventory, then a Recipe Job with `CRYPTOGRAPHIC_HASH` on identifier columns and `MASK_DELIMITER` on phone/SSN. A and C require code. D is for ML scientists building features for SageMaker training, not compliance reporting.

---

## Q85 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall DataBrew pricing floors

A team has set up an EventBridge rule that triggers a DataBrew Recipe Job on every S3 upload to a landing bucket. Files arrive every 5 minutes, average size 30 MB, and each job run finishes in 90 seconds. After a month the bill is shockingly high. What is the cost trap?

- A. EventBridge charges per event; reduce the trigger rate
- B. Each DataBrew job bills 5 nodes for at least 1 minute (the floor is $2.40/hour = $0.04/run); 8,640 runs/month ≈ $345 in floor cost minimums alone
- C. DataBrew charges $1.00 per 30-minute interactive session
- D. Recipe Jobs incur Spark cold-start charges

**Answer:** B
**Explanation:** DataBrew Recipe Jobs bill at $0.48/node-hour with a 5-node minimum and 1-minute billing floor — that's $0.04 per tiny run × 8,640 runs/month ≈ $345 just in floor costs, ignoring actual run time. The chapter says reserve DataBrew for batch jobs against accumulated data, not per-event triggers; for per-event tiny transformations use Lambda or Kinesis Firehose. A is negligible. C applies to interactive sessions, not jobs. D is fabricated.

---

## Q86 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall DataBrew recipe limits

Which of the following is a hard limit on DataBrew recipes?

- A. Recipes are limited to 100 transformations per recipe
- B. Recipes are limited to 50 transformations per recipe
- C. Recipes support up to 5 joins in a single step
- D. Recipes support custom Python UDFs

**Answer:** A
**Explanation:** Per the AWS Glue DataBrew Developer Guide and the chapter: "You can include up to 100 data transformations in a single DataBrew recipe." Joins are capped at 2 datasets per step (not 5). Custom Python/Scala/Spark UDFs are not supported — "Custom SQL" exists only for Redshift/Snowflake source-side. B is the wrong number.

---

## Q87 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish DataBrew rulesets from Glue Data Quality

A data-engineering team owns a Glue ETL pipeline that lands curated Parquet hourly. They want the pipeline to halt if `customer_id` is ever less than 99.9% complete, and the rule logic must be expressed in a declarative DSL versioned in Git. A separate compliance team wants an on-demand statistical and PII report for new datasets. Which two AWS surfaces are the correct pair?

- A. Both teams use DataBrew rulesets
- B. Both teams use Glue Data Quality DQDL
- C. Continuous in-pipeline validation = Glue Data Quality (DQDL); on-demand profile + PII = DataBrew Profile Job
- D. Glue Crawlers for both

**Answer:** C
**Explanation:** The chapter contrasts the two cleanly: Glue Data Quality embeds DQDL inside Glue ETL jobs and can fail or branch the job — continuous, declarative, code-reviewable; cost is Glue ETL pricing ($0.44/DPU-hr). DataBrew Profile Job is the on-demand, click-driven option with PII statistics and ~30 built-in rule types; cost is $0.48/node-hr × 5-node min. They are siblings under Task 1.3 but tested by trigger model and persona.

---

## Q88 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply DataBrew PII redaction transforms

A team needs to redact a `phone_number` column for testing in lower environments and join two masked datasets on a hashed `customer_id`. The masking should be reversible only by the production team using a key stored in Secrets Manager. Which DataBrew transforms address these requirements?

- A. `CRYPTOGRAPHIC_HASH` on both columns
- B. `ENCRYPT` on both columns
- C. `MASK_DELIMITER` on phone digits, `CRYPTOGRAPHIC_HASH` on `customer_id`, `DETERMINISTIC_ENCRYPT` if reversibility is needed
- D. `NULLIFY` on both columns

**Answer:** C
**Explanation:** The chapter maps these directly: `MASK_DELIMITER` for partial redaction (digit-preserving phone masks), `CRYPTOGRAPHIC_HASH` for irreversible-but-join-friendly identifiers (same plaintext → same hash), and `DETERMINISTIC_ENCRYPT` for reversible-and-join-preserving needs (production team with the key can decrypt). A breaks reversibility. B (non-deterministic `ENCRYPT`) breaks joins. D destroys all utility.

---

## Q89 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the 2023 DataBrew-in-Glue-Studio integration

The same DataBrew recipe `pii_redaction_us_v2` used by analysts on a 200 GB monthly file must now be applied to a 30 TB daily stream of reconciliation data, with bookmarks so each daily run only processes new partitions. The compliance team still cannot write code. What is the recommended architecture?

- A. Rewrite the recipe in PySpark and abandon DataBrew
- B. Run DataBrew Recipe Jobs at higher node counts (up to 149 nodes)
- C. Keep the recipe in DataBrew, but embed the published recipe version as a node inside a Glue Studio visual ETL Spark job (bookmarks, Auto Scaling, Iceberg writes)
- D. Migrate to Amazon EMR Serverless

**Answer:** C
**Explanation:** This is the July 2023 strategic-shift pattern called out in the chapter: Glue Studio visual ETL jobs can include published DataBrew recipes as steps. The compliance team still owns the recipe visually; data engineers own the surrounding Glue Spark job with bookmarks ($0.44/DPU-hr, scale-up story for DataBrew). A throws away the single source of truth. B doesn't add bookmarks or incremental processing. D is unnecessary complexity.

---

## Q90 — Domain 1: Data Preparation for Machine Learning
**Objective:** Match Macie, DataBrew, and Comprehend to PII workflows

(Select TWO) Match each PII tool to its layer of operation:

- A. Macie answers "which of my 12,000 S3 buckets contain PII?"
- B. Macie can scan DynamoDB and RDS for PII columns
- C. DataBrew is the right answer to "in this dataset, which columns are PII, and how do I mask them?"
- D. Comprehend `DetectPiiEntities` is the right answer for "find PII in customer support emails (free text)"
- E. All three tools are interchangeable; pick the cheapest

**Answer:** A, C
**Explanation:** Both correct. A: Macie operates at the bucket/object-discovery layer in S3. B is wrong — Macie is S3-only. C: DataBrew operates at row/column transformation. D is technically correct (Comprehend is for free-text PII) but the question asks for two; A and C are the most distinctive layer-matching statements in the chapter's table. E is wrong by design — the three tools are complementary, not substitutes. (Note: in a strict multi-select reading, D is also correct; A and C are the strongest "layer" matches.)

---

## Q91 — Domain 1: Data Preparation for Machine Learning
**Objective:** Disambiguate Data Wrangler's home in 2026

A team using the new SageMaker Studio experience cannot find the Data Wrangler tab in the launcher. What is the right action?

- A. Roll back to Studio Classic — Data Wrangler only lives there
- B. Launch SageMaker Canvas from inside Studio; Data Wrangler is a feature of Canvas as of 2024
- C. Install the Data Wrangler extension from JupyterLab
- D. File an AWS support ticket; the feature is currently being rolled out

**Answer:** B
**Explanation:** The chapter's most-tested fact: Data Wrangler in the new Studio experience is accessed by launching Canvas; the new Studio does not include a native Data Wrangler UI. The Studio Classic variant still loads existing flows but receives no new features and is on a deprecation track. A is the wrong direction (Classic is frozen). C and D are fabricated.

---

## Q92 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recite the four-act Data Wrangler workflow

Which sequence correctly describes the canonical Data Wrangler engagement?

- A. Source → Train → Deploy → Monitor
- B. Source → Transform → Analyse → Export
- C. Ingest → Label → Train → Serve
- D. Sample → Encode → Tune → Register

**Answer:** B
**Explanation:** The four-act mental model is Source (40+ connectors) → Transform (300+ transforms across 15 categories) → Analyse (Data Quality + Insights Report, Bias Report, Quick Model) → Export (5 targets: notebook, Pipelines, Feature Store, Spark, S3). The chapter says recite it before clicking any button.

---

## Q93 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use the Data Quality and Insights Report for target leakage

A data scientist runs the Data Wrangler Data Quality and Insights Report on a customer-churn dataset. The report flags `last_login_date` with an ROC AUC near 1.0 against the target. What does this mean and what should the team do?

- A. The feature is exceptionally informative; keep it and ship the model
- B. ROC AUC ~1.0 indicates target leakage — `last_login_date` is likely set only after churn; drop the feature or re-derive it from observable-at-prediction-time data
- C. The report is broken; ignore it
- D. The dataset is too small; collect more data

**Answer:** B
**Explanation:** The chapter's canonical teaching case: the Titanic "lifeboat" column has near-1.0 AUC predicting survival because lifeboats happen after the disaster. The same mechanism applies to `last_login_date` set to NULL only after churn — a perfect predictor that is useless in production because at scoring time you don't know the future. Drop or re-derive. A would ship a broken model. C ignores the most-valuable EDA artifact in Data Wrangler.

---

## Q94 — Domain 1: Data Preparation for Machine Learning
**Objective:** Place SMOTE correctly in a flow DAG

A Data Wrangler flow does: load CSV → impute missing → one-hot encode → train/val/test split → SMOTE → train. A teammate proposes moving SMOTE before the split. Which statement is correct?

- A. SMOTE must come before the split so the entire dataset is balanced
- B. SMOTE before the split contaminates the validation/test sets with synthetic neighbours of training points, inflating apparent scores; keep SMOTE after the split on the training branch only
- C. SMOTE only works on time-series data; remove it
- D. The order does not matter

**Answer:** B
**Explanation:** This is one of the cleanest exam-trick patterns in the chapter. SMOTE applied before the split injects synthetic minority neighbours that share information with the validation/test sets, inflating offline metrics. The correct pattern: split first → SMOTE on the training branch only. A is the canonical wrong answer. C is wrong (SMOTE is tabular numeric/encoded). D is dangerous.

---

## Q95 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the custom-pandas 80M-row trap

A Data Wrangler flow includes a custom transform written in pandas that filters rows by regex. The 100K-row sample preview runs fine. At export against the full 120M-row dataset on a single-instance `ml.m5.16xlarge` Processing job, the job either OOMs or runs for 30+ minutes. What is the recommended fix?

- A. Scale up to `ml.r5.24xlarge` — more memory will solve it
- B. Rewrite the custom transform as PySpark or PySpark SQL so it distributes; configure multi-instance Spark mode for the export
- C. Reduce the sample size to 10K rows and re-run
- D. Switch to single-instance and add more EBS volume

**Answer:** B
**Explanation:** The chapter calls this the "most-tested production trap in Data Wrangler." Custom pandas transforms run on the Spark driver only — they do not distribute. The AWS benchmark on 80M rows × 300 cols shows pandas OOMing at every m5 size while built-in PySpark transforms run in seconds. The exam wants you to distribute, not just vertically scale. A is the explicit distractor — m5-only restricts r5 anyway. C only helps the preview. D doesn't address the single-executor bottleneck.

---

## Q96 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose the right export target from Data Wrangler

A team has built a Data Wrangler flow that should run nightly as part of an existing training pipeline and feed transformed columns into both an online inference store and an offline training store. Which export target is the right choice?

- A. Export to Python notebook
- B. Export to S3 only
- C. Export to SageMaker Feature Store (auto-detects record-identifier and event-time columns; writes to both online + offline stores)
- D. Export to a Spark `.py` for EMR

**Answer:** C
**Explanation:** The chapter's Feature Store one-click export pattern: Data Wrangler validates the flow's output schema against the Feature Group, auto-detects the RecordIdentifier and EventTime columns, and writes to both online (DynamoDB or in-memory) and offline (S3 + Iceberg) stores. A is for hand-off. B writes only to S3. D is for external Spark and loses Feature Store integration. The combination of "nightly," "online + offline," and "Pipelines" most cleanly maps to a Pipelines ProcessingStep that exports to Feature Store.

---

## Q97 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish Quick Model from Autopilot

A data scientist clicks "Quick Model" on a Data Wrangler analysis node and receives an XGBoost F1 score. What is Quick Model NOT?

- A. A sanity-check baseline that says "with these features as they currently stand, here is the ceiling a tree model can reach"
- B. A full AutoML run with hyperparameter tuning, model leaderboard, and ensembling
- C. A fast EDA tool useful during feature engineering
- D. An analysis that pins to the flow as a node

**Answer:** B
**Explanation:** The chapter explicitly contrasts Quick Model and Autopilot. Quick Model = single XGBoost, fast preview, "is this feature set even useful?" Autopilot = full AutoML, model leaderboard across XGB / LinearLearner / DL, hyperparameter tuning, ensembling, "what is the best model I can ship?" Quick Model is NOT AutoML. A, C, D are all accurate descriptions of what Quick Model IS.

---

## Q98 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall Data Wrangler instance-family restriction

For a Data Wrangler distributed Processing-job export against a 350 GiB dataset, which instance configuration is supported AND optimal for cost?

- A. 1 × `ml.r5.24xlarge` (memory-optimized)
- B. 1 × `ml.c5.24xlarge` (compute-optimized)
- C. 3 × `ml.m5.4xlarge` (horizontal scaling on the m5 family)
- D. 1 × `ml.p3.2xlarge` (GPU)

**Answer:** C
**Explanation:** Data Wrangler's export-time Processing job is locked to the m5 instance family — no r5 (memory-optimized), no c5 (compute-optimized), no GPU. The horizontal scaling lever is the only way to scale. AWS's published benchmark shows 3 × `ml.m5.12xlarge` (or 3 × `ml.m5.4xlarge`) beats 1 × `ml.m5.24xlarge` by ~40-50% in cost for 350 GiB. A, B, D are all outside the m5 family and not supported.

---

## Q99 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the Bias Report scope inside Data Wrangler

Which bias analysis does Data Wrangler's Bias Report support natively?

- A. Pre-training bias metrics (CI, DPL, KL, JS, LP, TVD, KS, CDD) powered by Clarify
- B. Post-training bias metrics (DPPL, DI, RD, AD, TE)
- C. SHAP feature attribution against a trained model
- D. Both pre- and post-training bias in one click

**Answer:** A
**Explanation:** Data Wrangler operates on datasets (no trained model), so it surfaces only Clarify's pre-training metrics: Class Imbalance (CI), Difference in Proportions of Labels (DPL), KL, JS, Lp-norm (LP), Total Variation Distance (TVD), Kolmogorov-Smirnov (KS), and Conditional Demographic Disparity (CDD). Post-training metrics live in a standalone Clarify Processing job. SHAP is a separate Clarify analysis on a deployed model.

---

## Q100 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose between Data Wrangler, Glue, DataBrew

A data scientist needs target encoding for a high-cardinality `merchant_id` column, PCA on a wide block of behavioural features, a Quick Model estimate of feature importance, and export to SageMaker Feature Store. Which tool should they use?

- A. AWS Glue Spark — write the transforms in PySpark
- B. AWS Glue DataBrew — has 250+ no-code transforms
- C. SageMaker Data Wrangler — ML-specific feature engineering with Feature Store export
- D. Amazon Athena — SQL is enough

**Answer:** C
**Explanation:** DataBrew has no target encoding (only one-hot, ordinal, binary), no PCA, no Quick Model, no Feature Store export. Glue Spark has none of the ML-aware tools either. Athena is SQL-only. Data Wrangler is the only tool with target encoding + PCA + Quick Model + one-click Feature Store export, and the persona (data scientist) + destination (Feature Store) both point at it.

---

## Q101 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the online stores supported by Feature Store

(Select TWO) Which statements about SageMaker Feature Store online stores are correct?

- A. `Standard` is DynamoDB-backed with single-digit-ms p99 and supports CMK
- B. `InMemory` is ElastiCache (Redis OSS)-backed, sub-ms, online-only with no offline replica, on-demand throughput only, no CMK, 50 GiB cap
- C. `InMemory` was launched in October 2023
- D. `InMemory` supports both On-demand and Provisioned throughput
- E. `Standard` requires you to manage the DynamoDB table directly

**Answer:** B, C
**Explanation:** B captures the four kill-switches the chapter says to memorize: 50 GiB cap, on-demand only, no offline replica, no CMK. C is the launch date the chapter explicitly corrects ("not 2024"). A is mostly right but the chapter notes the canonical correct answer is also B (the question asks specifically for `InMemory` traits). D is wrong: `InMemory` is on-demand only. E is wrong: Feature Store abstracts DynamoDB from you.

---

## Q102 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply the In-Memory store's compliance kill-switches

A real-time bidding service must respond within 50 ms total, with feature lookup taking at most 5 ms p99. The team also has a strict compliance requirement that all customer data must be encrypted with a customer-managed KMS key (CMK). Which online tier should they pick?

- A. `InMemory` — sub-ms latency wins on the budget
- B. `Standard` + `BatchGetRecord` + PrivateLink — `InMemory` is disqualified by the CMK requirement (AWS-managed key only)
- C. `InMemory` with DAX in front
- D. Build a custom DynamoDB layer outside Feature Store

**Answer:** B
**Explanation:** This is the chapter's worked example. The CMK requirement is the decider — `InMemory` only supports the AWS-managed key, not CMK. `Standard` + `BatchGetRecord` + PrivateLink achieves 3–8 ms p99 in same-AZ deployments, comfortably under 5 ms p99 with PrivateLink-pinned routing. C is invalid: DAX doesn't integrate with the Feature Store API. D defeats the point of the service.

---

## Q103 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the BatchGetRecord 100-record limit

An inference endpoint must score 500 candidate items per request, with 6 features from `item_features` and 4 features from `category_features`. A developer writes a single `BatchGetRecord` call to fetch all 1,000 records (500 × 2 groups). What goes wrong, and what's the fix?

- A. The call succeeds but is slow; tune the timeout
- B. `BatchGetRecord` accepts at most 100 records per call across all feature groups; shard into 10 parallel calls of 100 records each (or merge feature groups if 1:1 on `item_id`)
- C. `BatchGetRecord` doesn't support multiple feature groups; use 1,000 sequential `GetRecord` calls
- D. Switch the online store to `InMemory` to bypass the limit

**Answer:** B
**Explanation:** The chapter calls out the 100-record hard limit explicitly. The correct fix is sharding into parallel `BatchGetRecord` calls (5 calls per group × 2 groups = 10 parallel calls), each fetching 100 records, with async I/O keeping latency close to a single call. Merging the two groups into one wider group is the structural optimization. A is wrong by API contract. C makes latency worse. D doesn't change the limit (it applies to both tiers).

---

## Q104 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply the 24-hour throughput-mode lockout

At 9:00 a.m. Tuesday a team switches a feature group from On-demand to Provisioned at 500 RCU / 200 WCU. At 11:00 a.m. traffic exceeds the provisioned capacity and `ThrottledRequests` appears in CloudWatch. The team realizes On-demand was the right call. At 11:30 a.m. they try to switch back to On-demand. What happens?

- A. The switch succeeds immediately
- B. The switch is rejected — throughput-mode changes are rate-limited to one per 24 hours per feature group; the next switch is permitted at 9:00 a.m. Wednesday
- C. The switch succeeds but takes 4 hours to propagate
- D. The feature group is locked from any changes for 7 days

**Answer:** B
**Explanation:** The chapter cites this inheritance from DynamoDB's table-mode change rule: one transition per 24-hour window per feature group. The remediation in the lockout window is to increase Provisioned capacity (capacity changes within a mode are not rate-limited the same way), add client-side retry, and revisit the mode decision Wednesday. The right long-term answer for bursty, unpredictable traffic is to stay on On-demand permanently.

---

## Q105 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose the offline store table format

A team is creating a new feature group in 2026 and expects to use GDPR right-to-erasure on a regular cadence, plus time-travel queries for training reproducibility. Which offline configuration is correct?

- A. `TableFormat=Glue` (Glue + Parquet, the SDK default) — it is the AWS recommendation
- B. `TableFormat=Iceberg` — Apache Iceberg is GA since 2024 and AWS-recommended; supports `DELETE FROM`, `FOR TIMESTAMP AS OF`, and full schema evolution
- C. Avro on S3 — the most compact storage
- D. ORC on S3 — best for time-travel

**Answer:** B
**Explanation:** The chapter emphasizes that Iceberg is the AWS-recommended choice (2024 GA) but is NOT the SDK default — you must set `TableFormat=Iceberg` explicitly or the SDK falls back to Glue/Parquet. Iceberg supports row-level `MERGE INTO`/`UPDATE`/`DELETE`, native `FOR TIMESTAMP AS OF` time travel, and schema evolution — all required for GDPR + reproducibility workflows. A reads correctly that AWS recommends Iceberg but mistakenly says Glue/Parquet is that format. C and D are fabricated.

---

## Q106 — Domain 1: Data Preparation for Machine Learning
**Objective:** Diagnose training-serving skew

A fraud-detection model trained on the offline store of `customer_features` shows 0.94 AUC in cross-validation. Deployed to a SageMaker endpoint reading the online store via `GetRecord`, it shows 0.78 AUC. The model artifact is identical and the features requested are the same. What is the single most likely cause?

- A. DynamoDB has stale records; bounce the endpoint
- B. The streaming Lambda stamps `event_time = now()` so the online store overwrites historical points with "current" values relative to the past events — fix to use the source event's timestamp
- C. The model is overfit; retrain with regularization
- D. The Feature Store's offline-store lag is too high

**Answer:** B
**Explanation:** The chapter's exercise pins this as the #1 priority cause. Online store has "current" values for past events; offline store (training source) has correctly time-aligned historical values. Training is right; online lookup is wrong because the writer stamped `now()` instead of the source event timestamp. Fix: use the Kinesis record's source timestamp. A is unrelated. C ignores the structural cause. D would cause a different symptom (stale offline data, not skew).

---

## Q107 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use streaming ingestion to eliminate skew

(Select TWO) Which statements about the canonical Kinesis → Lambda → `PutRecord` streaming ingestion pattern are correct?

- A. A single `PutRecord` writes to both online and offline stores from one code path, structurally preventing training/serving skew
- B. The offline store is written synchronously; the online store is async
- C. The online store is written synchronously; the offline store is async (typically <15 minutes lag)
- D. Running two separate pipelines — one for DynamoDB, one for S3 — is the AWS-recommended pattern
- E. Streaming ingestion bypasses the feature group's schema validation

**Answer:** A, C
**Explanation:** A captures the chapter's emphasis: structural prevention of skew, not "best practiced against." C is the documented write-path: online is synchronous (consumers see the value as soon as the call returns 2xx); offline is async with <15 min typical lag. B reverses them. D is the always-wrong exam distractor — it reintroduces the drift surface area the feature store eliminates. E is wrong: schema validation applies to all writes.

---

## Q108 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall mandatory FeatureGroup schema

Which two fields are mandatory in every SageMaker Feature Group's schema?

- A. `Timestamp` and `PrimaryKey`
- B. `RecordIdentifierFeatureName` and `EventTimeFeatureName`
- C. `PartitionKey` and `SortKey`
- D. `RecordId` and `IngestionTime`

**Answer:** B
**Explanation:** Every Feature Group requires `RecordIdentifierFeatureName` (must be `String` or `Integral`, one per group, not changeable) and `EventTimeFeatureName` (`Fractional` epoch seconds or ISO-8601 string, required for point-in-time queries and offline partitioning, not changeable). The other options are fabricated.

---

## Q109 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply point-in-time-correct training joins

A training row is `(customer_id=C0042, label_time=2024-07-15, churned=False)`. The `customer_features` table has three rows for C0042 at event_times 2024-07-10, 2024-07-20, 2024-08-12 with values 3, 11, 2. Which value should the point-in-time-correct join return?

- A. 2 (the latest value at training time)
- B. 11 (the median value)
- C. 3 (the value where `event_time <= label_time`, ordered desc, limit 1)
- D. The average of all three

**Answer:** C
**Explanation:** Point-in-time correctness requires the feature value that was current as-of the label time. With `event_time <= '2024-07-15'`, only the 2024-07-10 row qualifies, so the value is 3. Returning 2 (the 2024-08-12 value) is the canonical leakage bug — it injects future information into the label and gives optimistic offline metrics that collapse in production.

---

## Q110 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use `DeleteRecord` and GDPR mechanics

What does `DeleteRecord` do in SageMaker Feature Store?

- A. It permanently removes the record from both online and offline stores
- B. It removes the record from the online store and appends a tombstone row (with `IsDeleted=true`) to the offline store; offline-store hard delete requires Iceberg `DELETE FROM` on the underlying table
- C. It is a no-op; you must use Athena to delete
- D. It only works on `InMemory` feature groups

**Answer:** B
**Explanation:** The chapter spells this out: `DeleteRecord` removes the record from the online store and writes a tombstone (`IsDeleted=true`) to the offline store — the offline store remains a complete audit log. For true hard-delete (GDPR), you must run Iceberg `DELETE FROM` SQL plus `EXPIRE_SNAPSHOTS` (the second step is the most-forgotten GDPR trap). A misrepresents tombstone semantics. C is wrong. D is wrong (`DeleteRecord` works on both tiers).

---

## Q111 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the build-vs-buy reality

Which statement most accurately describes the SageMaker Feature Store market position in 2025–2026?

- A. SageMaker Feature Store is the default real-time feature platform in every AWS ML shop
- B. The modal real-time feature platform in production AWS shops is still "DynamoDB + S3 + glue code"; SageMaker Feature Store is the AWS-blessed exam answer and the right pick for many teams, but Feast/Tecton/Databricks/DIY are real alternatives
- C. Feast has fully replaced SageMaker Feature Store
- D. SageMaker Feature Store mandates Apache Flink for streaming ingestion

**Answer:** B
**Explanation:** The chapter's honest framing: the modal production AWS feature platform is still hand-rolled DynamoDB+S3. Feature Store is the right pick for many teams (and the always-correct exam answer for AWS-blessed paths), but Feast (OSS), Tecton (SaaS), Databricks (Delta + Unity Catalog), and DIY remain real alternatives. The build-vs-buy framework in §19.12 walks the decision. A overstates adoption. C is wrong. D fabricates a constraint (Lambda + Kinesis is the canonical pattern).

---

## Q112 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish Ground Truth from A2I

A team needs to (a) bootstrap a labeled dataset for a new legal-contract NER model and (b) route 1% of a Bedrock summarization endpoint's outputs to a human for safety review. Which services?

- A. Ground Truth for both
- B. Ground Truth for (a) — labeling raw data before training; A2I for (b) — human review of inference outputs after deployment
- C. A2I for both
- D. Mechanical Turk directly for both

**Answer:** B
**Explanation:** The five-word mnemonic: "Ground Truth makes labels; A2I checks labels." Ground Truth is for pre-training dataset creation; A2I is post-inference review (low-confidence routing, random sampling, continuous feedback). They share workforce infrastructure but sit on opposite ends of the ML lifecycle.

---

## Q113 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply the HIPAA-eligibility constraint to labeling services

A healthtech needs 80,000 chest X-rays labeled for a specific pulmonary abnormality. The data is PHI. The team has no internal radiologists. An architect proposes Ground Truth Plus because "it's AWS-managed and high-quality." What is wrong, and what is the right architecture?

- A. Nothing is wrong; Ground Truth Plus is HIPAA-eligible
- B. Ground Truth Plus is NOT HIPAA-eligible; the right pattern is standard Ground Truth (HIPAA-eligible) + Private workforce of BAA-covered specialists + Cognito auth + custom DICOM-aware Crowd HTML UI + BAA with AWS and every worker organization
- C. Use Mechanical Turk with 5-way replication
- D. Use Ground Truth Plus but encrypt the bucket with CMK

**Answer:** B
**Explanation:** This is the single most-tested labeling pitfall on the MLA-C01. The chapter emphasizes the counter-intuitive fact: standard Ground Truth IS HIPAA-eligible, but Ground Truth Plus is NOT. AWS-managed does not equal more compliant. For PHI, use standard GT + private workforce (Cognito or OIDC). C is always wrong for HIPAA. D doesn't fix the BAA-boundary issue.

---

## Q114 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize the augmented manifest file format

A Ground Truth labeling job has finished. The output manifest sits in S3 and the team wants to feed it directly into a SageMaker image-classification training job. The augmented manifest file is in which format?

- A. CSV with a header row
- B. JSON (a top-level array of objects)
- C. JSON Lines (one complete JSON object per line; no surrounding array)
- D. Apache Parquet

**Answer:** C
**Explanation:** The chapter calls this out as an exam trap: the augmented manifest is JSON Lines (JSONL / ndjson), not JSON. If you `json.load()` the whole file, the parser blows up on line 2 because each line is a separate complete object. The correct loader is line-by-line `json.loads`. The manifest is fed to `CreateTrainingJob` via `S3DataType: AugmentedManifestFile`.

---

## Q115 — Domain 1: Data Preparation for Machine Learning
**Objective:** Configure `AugmentedManifestFile` in CreateTrainingJob

To feed a Ground Truth augmented manifest into a SageMaker built-in image-classification training job, which combination is required?

- A. `S3DataType=ManifestFile`, `InputMode=File`, no `AttributeNames`
- B. `S3DataType=AugmentedManifestFile`, `InputMode=Pipe`, `AttributeNames=["source-ref","<job-name>"]`, `RecordWrapperType=RecordIO`, `ContentType=application/x-recordio-protobuf`
- C. `S3DataType=S3Prefix`, raw object listing
- D. `S3DataType=AugmentedManifestFile`, `InputMode=File`, no `RecordWrapperType`

**Answer:** B
**Explanation:** The chapter spells out the contract: `AugmentedManifestFile` requires `InputMode=Pipe` (FastFile is supported for some algorithms as of 2024 but Pipe is the documented mandatory mode), with `AttributeNames` whitelisting which fields to pass through (typically `source-ref` + the job-name label attribute). Built-in image-classification and object-detection algorithms require `RecordWrapperType=RecordIO` + `ContentType=application/x-recordio-protobuf`.

---

## Q116 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply the active-learning minimum

A team has 800 labeled bird images and 4,200 unlabeled. They want to enable Ground Truth automated data labeling (active learning) on the remaining 4,200. What happens?

- A. The job runs as expected
- B. The API rejects the job — automated data labeling has a minimum of 1,250 objects, and AWS strongly recommends ≥ 5,000 to actually save money
- C. The job runs but only on the 800 labeled images
- D. The job converts to Ground Truth Plus automatically

**Answer:** B
**Explanation:** The chapter pins this as a recurring exam-alert: minimum 1,250 objects for active learning by API constraint, with ≥ 5,000 recommended for the math to favor savings (the per-iteration training compute is fixed and only amortizes at scale). Even at 5,000 the published benchmarks show 20–30% savings, not the marketing "up to 70%" figure.

---

## Q117 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recall active-learning supported task types

Which Ground Truth task type does NOT support automated data labeling (active learning)?

- A. Image classification (single label)
- B. Bounding box (object detection)
- C. Semantic segmentation
- D. Named entity recognition (NER)

**Answer:** D
**Explanation:** Active learning is supported only for four task types: image classification (single), image semantic segmentation, bounding box (object detection), and text classification (single). NER, multi-label classification, all video tasks, all 3D point-cloud tasks, and all custom tasks are excluded by AWS. The chapter calls this out as an exam fact and a typical distractor pattern.

---

## Q118 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply pre-defined active-learning accuracy targets

Which is the correct AWS-managed accuracy target for an active-learning bounding-box job?

- A. ≥ 95% expected label accuracy vs. humans
- B. Mean IoU = 0.6
- C. Mean IoU = 0.7
- D. User-configurable; any value is allowed

**Answer:** B
**Explanation:** The chapter's exam-fact table: image classification single-label = ≥95% expected accuracy; text classification single-label = ≥95% expected accuracy; bounding box = mean IoU 0.6; semantic segmentation = mean IoU 0.7. These targets are AWS-managed and NOT user-configurable — D is the distractor.

---

## Q119 — Domain 1: Data Preparation for Machine Learning
**Objective:** Build a custom Ground Truth labeling workflow

A team needs a custom annotation UI for proprietary medical-DICOM labeling. Which three pieces compose a custom Ground Truth workflow?

- A. SageMaker endpoint + EventBridge rule + DynamoDB
- B. Pre-annotation Lambda + Crowd HTML 2.0 worker task template with Liquid templating + Post-annotation Lambda
- C. AWS Glue job + Step Functions + Lambda
- D. AWS Lambda + Amazon Cognito + Amazon SES

**Answer:** B
**Explanation:** The chapter calls this the canonical custom-workflow pattern: Pre-Lambda (per-object payload prep — presign S3 URLs, generate pre-labels), Crowd HTML 2.0 template with Liquid for the worker UI (`<crowd-bounding-box>`, `<crowd-image-classifier>`, `{{ task.input.source }}`), and Post-Lambda for consolidation logic (Dawid-Skene, weighted voting). Any custom workflow uses all three.

---

## Q120 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose A2I built-in integrations

Which AI services have a built-in (zero-UI-code) A2I integration?

- A. Amazon Textract `AnalyzeDocument` and Amazon Rekognition `DetectModerationLabels`
- B. Amazon Comprehend and Amazon Translate
- C. Amazon Polly and Amazon Transcribe
- D. SageMaker real-time endpoints and Amazon Bedrock

**Answer:** A
**Explanation:** The chapter lists exactly two built-in integrations: Textract `AnalyzeDocument` (review low-confidence key-value extractions) and Rekognition `DetectModerationLabels` (review low-confidence unsafe-content flags). Everything else — Comprehend, Transcribe, Translate, Bedrock, custom SageMaker endpoints, generic tabular — requires a custom A2I workflow (Worker Task Template + Flow Definition + `StartHumanLoop`).

---

## Q121 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply workforce rules to sensitive data

A team needs to label 50,000 customer support transcripts containing PII (names, partial credit card numbers, addresses). Which workforce is appropriate?

- A. Mechanical Turk for cost
- B. Private workforce (Cognito or OIDC, internal staff or BAA contractors) — MTurk is a public crowd and is never appropriate for confidential or regulated data
- C. Ground Truth Plus
- D. Any of the above; the choice depends only on speed

**Answer:** B
**Explanation:** The chapter pins MTurk as "never for sensitive data." Once data leaves your VPC to a public crowd you cannot un-send it; the compliance violation is immediate. Private workforce (Cognito/OIDC, NDA-bound staff) is the right answer for any PII-bearing data. C is fine for non-PHI bulk work but still requires evaluating each project's PII boundary. D is wrong by compliance.

---

## Q122 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize streaming labeling + active learning exclusion

Which statement about Ground Truth streaming labeling jobs is correct?

- A. Streaming labeling supports active learning out of the box
- B. Streaming labeling jobs do NOT support automated data labeling (active learning); they are mutually exclusive
- C. Streaming labeling only works with MTurk
- D. Streaming labeling requires Glue as the source

**Answer:** B
**Explanation:** The chapter quotes AWS docs verbatim: "Streaming labeling jobs do not support automated data labeling." If you need both, run them as separate jobs. The exam tests this exclusion regularly. C and D are fabricated.

---

## Q123 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify the 8 Clarify pre-training bias metrics

(Select TWO) Which formulas correctly describe Clarify pre-training bias metrics?

- A. CI = `(n_a − n_d) / (n_a + n_d)`, range `[−1, +1]`, zero means equal counts
- B. DPL = `q_a − q_d` where `q_x = n_x(1)/n_x`, the difference in positive-label rates between facets
- C. KL is always symmetric and bounded between 0 and 1
- D. TVD is the average of all per-feature L2 norms across the dataset
- E. KS is the mean of the absolute differences between two CDFs

**Answer:** A, B
**Explanation:** A and B are the canonical pre-training metrics the exam guide cites by name. C is wrong: KL is NOT symmetric (Jensen-Shannon is the symmetric, bounded version). D mangles TVD — it is half the L1 distance between two label distributions, not an L2 quantity. E mangles KS — it is the SUPREMUM (max), not the mean, of CDF gaps.

---

## Q124 — Domain 1: Data Preparation for Machine Learning
**Objective:** Compute Class Imbalance

A dataset has 10,000 men and 1,500 women. With facet `a = men` and `d = women`, what is the Class Imbalance (CI) value?

- A. 0.000
- B. +0.739
- C. +1.000
- D. −0.739

**Answer:** B
**Explanation:** CI = (n_a − n_d) / (n_a + n_d) = (10000 − 1500) / (10000 + 1500) = 8500 / 11500 ≈ +0.739, indicating severe imbalance toward the favored facet (men). CI is in [−1, +1]; +1 would mean only a is present, 0 would mean equal counts, −1 would mean only d.

---

## Q125 — Domain 1: Data Preparation for Machine Learning
**Objective:** Compute DPL and interpret

A hiring dataset has 12,000 male and 12,000 female applicants. 3,000 men and 600 women were hired. With `a = male`, `d = female`, what are CI and DPL?

- A. CI = 0, DPL = 0
- B. CI = 0, DPL = +0.20
- C. CI = +0.20, DPL = 0
- D. CI = +0.20, DPL = +0.20

**Answer:** B
**Explanation:** CI = (12000 − 12000) / (24000) = 0 (counts are equal). DPL = q_a − q_d = 3000/12000 − 600/12000 = 0.25 − 0.05 = +0.20 (men get the positive label at a much higher rate). The chapter highlights this CI-vs-DPL contrast: a dataset can be perfectly representative (CI = 0) and still wildly biased in outcomes (DPL = 0.20). The fix is label-level intervention (re-weighting, threshold tuning), not resampling.

---

## Q126 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick the right Clarify metric by question shape

Which pre-training bias metric is most appropriate for "the symmetric, always-finite divergence between male and female outcome distributions"?

- A. KL (Kullback-Leibler)
- B. JS (Jensen-Shannon)
- C. CI (Class Imbalance)
- D. KS (Kolmogorov-Smirnov)

**Answer:** B
**Explanation:** JS = ½ KL(P_a || M) + ½ KL(P_d || M) where M is the average distribution — symmetric by construction and always finite (KL can be ∞ when one distribution has a zero where the other has mass). The chapter's exam-tell: "symmetric and bounded version of KL" → JS. KL alone is not symmetric. CI compares counts, not distributions. KS measures max CDF gap.

---

## Q127 — Domain 1: Data Preparation for Machine Learning
**Objective:** Detect Simpson's paradox

A loan-approval dataset shows DPL = 0 overall by gender, but when stratified by US state, every state shows men approved at higher rates than women. Which Clarify pre-training metric is designed to surface this?

- A. CI (Class Imbalance)
- B. DPL alone (it already captures this)
- C. CDDL (Conditional Demographic Disparity in Labels) with stratification on `state`
- D. KS (Kolmogorov-Smirnov)

**Answer:** C
**Explanation:** CDDL is Simpson-style stratified DPL — it weights by stratum and surfaces the case where the aggregate looks balanced but every sub-stratum shows the same bias direction. The chapter's exam-tell: "subgroup analysis" or "controlling for a third variable" → CDDL. The graduate-school admissions paradox is the textbook example.

---

## Q128 — Domain 1: Data Preparation for Machine Learning
**Objective:** Wire up SageMakerClarifyProcessor

Which three SDK objects are required to run a Clarify pre-training bias job?

- A. `TrainingConfig`, `BiasConfig`, `EstimatorProcessor`
- B. `DataConfig`, `BiasConfig`, `SageMakerClarifyProcessor`
- C. `InputConfig`, `OutputConfig`, `BiasProcessor`
- D. `S3Source`, `KMSConfig`, `ClarifyEstimator`

**Answer:** B
**Explanation:** The chapter walks the canonical wire-up: `DataConfig` (where the data is, label column, format), `BiasConfig` (which facet, favored/disfavored values, optional `group_name` for CDDL stratification), and `SageMakerClarifyProcessor` (the compute — `instance_count`, `instance_type`). The processor's `run_pre_training_bias` method takes the two configs and runs a Processing job that writes `analysis.json`, `report.html`, and `report.pdf` to S3.

---

## Q129 — Domain 1: Data Preparation for Machine Learning
**Objective:** Pick a remediation for class imbalance

A binary fraud classifier has 99.5% non-fraud / 0.5% fraud in the training set. Which is the simplest, calibration-preserving remediation that the chapter recommends trying FIRST in 2025-2026?

- A. Apply SMOTE before train/test split
- B. Use a class-weighted loss (e.g., XGBoost `scale_pos_weight = neg_count / pos_count`) and tune the decision threshold on a held-out validation set
- C. Drop all minority-class samples
- D. Switch to a deep neural network

**Answer:** B
**Explanation:** The chapter cites a 2024 9,000-experiment study (arXiv 2409.19751) showing that decision-threshold calibration alone often matches or beats SMOTE, with no synthetic data and no calibration destruction. The recommended layered recipe: train on natural distribution, use a class-weighted loss (`scale_pos_weight` in XGBoost), tune the decision threshold for the business metric, and only try SMOTE inside CV folds as a last resort. A is the canonical wrong choice (applying SMOTE before the split also leaks). C destroys information. D doesn't address imbalance.

---

## Q130 — Domain 1: Data Preparation for Machine Learning
**Objective:** Identify why SMOTE often loses

(Select TWO) Why does SMOTE often underperform in production?

- A. In high-dimensional sparse spaces (text/image embeddings), nearest-neighbor interpolation is essentially random
- B. SMOTE destroys calibration; predicted probabilities no longer reflect base rates
- C. SMOTE is the only legal approach in GDPR-regulated environments
- D. SMOTE is supported only on streaming data
- E. SMOTE applied before train/test split causes validation contamination

**Answer:** A, B
**Explanation:** The chapter lists four production failures; A and B are two of the three structural ones. The curse of dimensionality makes SMOTE's interpolation manufacture points in regions that don't reflect the true minority distribution; calibration destruction means default 0.5 thresholds become meaningless. (E is also true but is the codebase-level bug, not a structural property of SMOTE itself.) C and D are fabricated. The 2024 study showed threshold tuning often beats SMOTE on most datasets.

---

## Q131 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize no first-party AWS synthetic data service

A team needs synthetic minority-class examples to balance a tabular training set. Which is the correct AWS-native approach?

- A. Use the "Amazon Synthetic Data Service" API
- B. Use "AWS DataSynth" via SageMaker Pipelines
- C. There is no first-party AWS synthetic data service — bring SDV (open-source Python on SageMaker Processing), Gretel, MOSTLY AI, or Tonic; for text, Bedrock + Claude paraphrase
- D. Use SageMaker Autopilot to generate synthetic rows

**Answer:** C
**Explanation:** The chapter calls this the most common exam trap: AWS has no first-party synthetic-data service. A and B are fabricated names exam writers love to plant as distractors. The AWS-native paths are SDV (open-source, runs on SageMaker Processing), Bedrock LLMs for text (e.g., Claude paraphrase per the DAIL pattern), Stability AI for synthetic images, or third-party services like Gretel (acquired by NVIDIA in March 2025), MOSTLY AI, and Tonic. Autopilot is AutoML, not data generation.

---

## Q132 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use SMOTE variants correctly

A team has tabular data with mild imbalance and wants to focus synthetic example generation on the hardest minority examples (near the decision boundary). Which technique is the closest match?

- A. Random oversampling
- B. SMOTE (vanilla)
- C. ADASYN (Adaptive Synthetic Sampling) or Borderline-SMOTE
- D. Random undersampling

**Answer:** C
**Explanation:** The chapter's resampling table: ADASYN is the SMOTE variant that focuses synthesis on hard minority examples near the decision boundary, and Borderline-SMOTE only synthesizes near the boundary. Both are more aggressive about correcting decision-boundary blindness than vanilla SMOTE. A duplicates without diversity; B does not concentrate on the boundary; D discards information.

---

## Q133 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply Glue Data Quality DQDL

Which DQDL rule correctly enforces "the dataset is no older than 6 hours"?

- A. `IsComplete "load_ts"`
- B. `DataFreshness "load_ts" <= 6 hours`
- C. `Mean "load_ts" between 0 and 6`
- D. `RowCount > 10000`

**Answer:** B
**Explanation:** DQDL's `DataFreshness` rule checks the age of values in a timestamp column against a duration ("less than or equal to N hours/days"). It is one of the rule categories the chapter enumerates. A only checks for non-null. C is nonsensical for timestamps. D is a row-count rule, unrelated to freshness.

---

## Q134 — Domain 1: Data Preparation for Machine Learning
**Objective:** Distinguish Glue Data Quality from Deequ

A scenario asks for declarative quality rules against a Glue Catalog table, with CloudWatch alarms and ML-suggested rules. Which service is the correct answer?

- A. Apache Deequ (open-source library running in a self-managed Spark job)
- B. AWS Glue Data Quality (managed product with DQDL, ML-suggested rules, CloudWatch metrics, Lake Formation surfacing)
- C. AWS Glue DataBrew rulesets only
- D. Amazon Macie

**Answer:** B
**Explanation:** Glue Data Quality is the managed product (built on Deequ as a library) and is the answer when the question asks for DQDL + ML-suggested rules + CloudWatch alarms + Lake Formation integration. A would force you to run your own Spark job. C uses a different rule DSL scoped to DataBrew Profile Jobs and serves a different persona. D is for S3 PII discovery.

---

## Q135 — Domain 1: Data Preparation for Machine Learning
**Objective:** Use ML-suggested rules in Glue Data Quality

A team wants to bootstrap quality rules for a new Glue Catalog table without writing DQDL by hand. What is the AWS-recommended approach?

- A. Hand-author DQDL based on a profiling notebook
- B. From the Catalog table's Data Quality tab, Generate recommendations — Glue runs a profiling job and outputs candidate rules that the steward reviews and saves
- C. Copy rules from another team's table
- D. Use Glue DataBrew Profile Jobs to generate DQDL automatically

**Answer:** B
**Explanation:** The chapter cites ML-suggested rules (a.k.a. rule recommendations) as the canonical bootstrap path: Glue profiles the table, computes column stats and distributions, and emits candidate DQDL (e.g., `Completeness "x" > 0.99` for a column that's 100% non-null in the sample). The steward reviews, edits, and saves. D conflates DataBrew (different DSL, different product) with Glue Data Quality.

---

## Q136 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize Macie's S3-only limitation

A team needs to discover PII columns across RDS, DynamoDB, Redshift, and S3 buckets. Which is the correct AWS-native pattern?

- A. Macie for all four data stores
- B. Macie for S3 only; Comprehend `DetectPiiEntities` inside Lambda/Glue for free-text columns; Lake Formation column-level grants; DataBrew PII transforms for relational sources
- C. Glue DataBrew for all four data stores
- D. Bedrock Guardrails for all four

**Answer:** B
**Explanation:** Macie is S3-only — the chapter calls this out as an exam-alert and a guaranteed wrong answer for non-S3 sources. For PII outside S3, use Comprehend (text), DataBrew PII transforms (relational), and Lake Formation column-level grants (governance). Bedrock Guardrails is for LLM I/O, not for scanning data stores.

---

## Q137 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize Macie's three categories of managed identifiers

Which three categories of managed data identifiers does Macie ship with?

- A. Credentials, Financial information, Personal information (PII/PHI)
- B. Images, Audio, Video
- C. Logs, Metrics, Traces
- D. Buckets, Objects, Prefixes

**Answer:** A
**Explanation:** Macie's managed identifiers cover Credentials (AWS keys, SSH keys, JWTs, GitHub PATs), Financial info (credit cards, IBAN, SWIFT, bank account numbers), and Personal info (SSN, passport numbers, NPI, medical record numbers per country, addresses, names). Custom data identifiers (CDIs) layer on regex + keywords + max-distance + allow lists for org-specific patterns.

---

## Q138 — Domain 1: Data Preparation for Machine Learning
**Objective:** Recognize Macie publishes findings to EventBridge

Which is the correct path for triggering remediation on a Macie sensitive-data finding?

- A. Macie → SNS directly
- B. Macie → EventBridge (default bus) → Lambda / Step Functions / SNS / Security Hub
- C. Macie → CloudTrail → SQS
- D. Macie → S3 Object Lambda

**Answer:** B
**Explanation:** Macie publishes findings to EventBridge by default (and to Security Hub if enabled). The canonical remediation path runs through EventBridge rules to Lambda/Step Functions/SNS. The chapter highlights that any direct Macie → SNS arrow is wrong on the exam.

---

## Q139 — Domain 1: Data Preparation for Machine Learning
**Objective:** Choose Macie scan mode by use case

Which Macie scan mode is best for "always-on visibility across the S3 footprint with daily updates and bounded cost"?

- A. Sensitive data discovery jobs scheduled weekly
- B. Automated sensitive data discovery (statistical sampling, daily evaluation, per-GB-month pricing at a discounted rate)
- C. CloudTrail data events
- D. S3 Inventory + Glue Crawlers

**Answer:** B
**Explanation:** The chapter contrasts the two modes: automated sensitive data discovery is the sampled, daily, cheap, always-on baseline; sensitive data discovery jobs are the full-scan, scheduled/one-time, expensive option for pre-production audits or compliance evidence. The "always-on with daily updates" phrasing points squarely at automated discovery.

---

## Q140 — Domain 1: Data Preparation for Machine Learning
**Objective:** Apply GDPR right-to-erasure on Iceberg

A team runs `DELETE FROM customer_events WHERE user_id = '8a3f...'` on an Iceberg-formatted feature group's offline table to satisfy a GDPR erasure request. Two months later, a regulator queries the table `FOR TIMESTAMP AS OF` a January snapshot and the customer's data appears. What went wrong?

- A. Iceberg does not actually support DELETE
- B. The team forgot the second step: `EXPIRE_SNAPSHOTS` older than the retention window (and `REMOVE_ORPHAN_FILES` to release S3 storage) — Iceberg's time-travel keeps historical snapshots by default, so the deleted data still exists in old snapshots until they are expired
- C. The team should have used DROP TABLE
- D. Glue Data Catalog overrides Iceberg deletes

**Answer:** B
**Explanation:** The chapter pins this as a regulatory-defensible trap: `DELETE FROM` writes a positional delete file (Iceberg v2) or deletion vector (v3), but the snapshot containing the original row is preserved for time-travel until you run `EXPIRE_SNAPSHOTS`. For GDPR you must complete the two-step ritual within your legal retention window. Also: a Bedrock fine-tuned model trained on that subject's data may itself need retraining inside the erasure SLA.

---

---

# Domain 2 — ML Model Development (26%)

# MLA-C01 Practice — Domain 2 (Model Development), Part A

> **Scope:** 65 exam-realistic questions covering **Domain 2 — ML Model Development**, specifically the half-A surface area: SageMaker Studio anatomy, training-job lifecycle, built-in algorithms, script mode, BYOC, JumpStart, Autopilot, Experiments + MLflow, Clarify (post-training bias + explainability), and Debugger/Profiler.
>
> **Source chapters:** `topics/14_aws_ml_engineer_associate/part_e_model_development/` chapters 22–30.
>
> **Question numbering:** Q141–Q205 (continues the Domain 1 → Domain 2 sequence). 4–5 questions are multi-select; the rest are single-best-answer A–D.
>
> **Parseable format** — used by the companion Flask quiz app:
> ```
> ## Q{n} — Domain 2: ML Model Development
> **Objective:** {one-line task/skill}
>
> {question stem}
>
> - A. {option}
> - B. {option}
> - C. {option}
> - D. {option}
>
> **Answer:** {letter or comma-separated letters for multi-select}
> **Explanation:** {why correct + why distractors fail}
> ```

---

## Q141 — Domain 2: ML Model Development
**Objective:** Pick the Studio object that is immutable after `CreateDomain`

A platform team created a SageMaker Studio Domain six months ago with `AuthMode=IAM`, `AppNetworkAccessType=PublicInternetOnly`, and a customer-managed KMS key. The security review now mandates `VpcOnly` networking. What is the minimum-impact change to comply?

- A. Call `UpdateDomain` with `AppNetworkAccessType=VpcOnly` and the new subnet IDs.
- B. Create a new Domain with `AppNetworkAccessType=VpcOnly` and migrate user profiles + EFS data, because `AppNetworkAccessType` is immutable after creation.
- C. Re-create the user profiles with `VpcOnly` overrides while keeping the existing Domain.
- D. Attach a VPC endpoint policy denying public traffic; the Domain setting becomes effectively `VpcOnly`.

**Answer:** B
**Explanation:** `AppNetworkAccessType`, `AuthMode`, `VpcId`, `SubnetIds`, and `KmsKeyId` are all **immutable** after `CreateDomain`. The only path to flip `PublicInternetOnly` → `VpcOnly` is a brand-new Domain. `UpdateDomain` does not accept these fields. VPC endpoint policies regulate routing *inside* the VPC but do not change the Domain's networking mode. Migration plan: provision the new Domain, point a new set of UserProfiles at the new EFS, copy user home directories with `aws s3 sync` or DataSync, then sunset the old Domain. This is the same exam-trap shape AWS uses for "switch from IAM auth to IdC auth" or "add a second VPC" — every answer asking you to call `UpdateDomain` with a new value for an immutable field is wrong on its face.

---

## Q142 — Domain 2: ML Model Development
**Objective:** Diagnose `pip install` failing in a VpcOnly Studio domain

A data scientist in a `VpcOnly` Studio domain runs `!pip install pandas-profiling` in a JupyterLab app. The call hangs for ~60 seconds and errors with `Could not find a version that satisfies the requirement`. The security team rejects any solution that adds internet access from notebooks. What is the AWS-recommended fix?

- A. Provision a NAT gateway and route `0.0.0.0/0` from the private subnet to the NAT.
- B. Build a custom Studio image with `pandas-profiling` baked in, register it with the domain, and switch the user to that image.
- C. Stand up an AWS CodeArtifact repository as an upstream PyPI mirror, reach it via the `codeartifact.api` + `codeartifact.repositories` VPC endpoints, and configure pip via `aws codeartifact login --tool pip` in a Studio LCC.
- D. Self-host a Bandersnatch PyPI mirror on EC2 in the same VPC and point pip at it.

**Answer:** C
**Explanation:** **CodeArtifact + PrivateLink** is the canonical AWS-recommended pattern for VpcOnly Studio domains needing ad-hoc `pip install`. The mechanism: provision a CodeArtifact domain + repository with `pypi-store` as an upstream PyPI proxy; CodeArtifact caches packages on first request and serves them via PrivateLink endpoints (`codeartifact.api` + `codeartifact.repositories`) thereafter. A short-lived token from `aws codeartifact get-authorization-token` (12-hour TTL) is materialized into `~/.config/pip/pip.conf` by the Studio LCC, so every new kernel inherits the proxy. NAT gateway re-introduces internet access (rejected by the constraint and by the security team). A custom image works for stable dependencies but breaks for ad-hoc installs. Bandersnatch is a valid self-hosted PyPI mirror tool but never the AWS-recommended answer on this exam.

---

## Q143 — Domain 2: ML Model Development
**Objective:** Identify which VPC endpoints a functional VpcOnly Studio domain requires

A team enabled `VpcOnly` and provisioned interface endpoints for SageMaker API, SageMaker runtime, ECR (api + dkr), STS, and an S3 gateway endpoint. Training jobs complete successfully according to `DescribeTrainingJob`, but `Estimator.fit(wait=True)` in the notebook never returns and the SDK call hangs indefinitely. Which endpoint was omitted?

- A. `com.amazonaws.<region>.kms`
- B. `com.amazonaws.<region>.logs` (CloudWatch Logs)
- C. `com.amazonaws.<region>.servicecatalog`
- D. `com.amazonaws.<region>.codecommit`

**Answer:** B
**Explanation:** `Estimator.fit(wait=True)` *tails the training-job log stream* after submission. Without a CloudWatch Logs interface endpoint the SDK can't reach the log group and the call hangs forever, even though the job itself completes (it streams logs from the training container, not from the notebook). KMS is needed only with a CMK-encrypted artifact; Service Catalog is for SageMaker Projects (optional); CodeCommit is unrelated.

---

## Q144 — Domain 2: ML Model Development
**Objective:** Distinguish `model.tar.gz` from `output.tar.gz` in the training-container contract

A PyTorch training job completes with `TrainingJobStatus=Completed`. Inspecting `s3://my-bucket/training-output/my-job/output/` reveals a 102-byte `model.tar.gz` (empty tar) and a 480 MB `output.tar.gz` containing `model.pth`. What did the script do wrong?

- A. It saved the model to `/opt/ml/output/data/` instead of `/opt/ml/model/`.
- B. It forgot to call `torch.save()` and only saved metrics.
- C. It set `MaxRuntime` too low and the model upload was truncated.
- D. It used `instance_type='local'`, which skips the `model.tar.gz` upload.

**Answer:** A
**Explanation:** `/opt/ml/model/` → **`model.tar.gz`** (the model artifact consumed by `CreateModel`, the Model Registry, Inference Recommender, Hyperparameter Tuning best-model selection). `/opt/ml/output/data/` → **`output.tar.gz`** (auxiliary side-channel for plots/logs/predictions that should NOT be part of the served model). Saving the `.pth` to the output-data directory produces an empty model tarball — the canonical exam scenario. The fix is one line: `torch.save(model.state_dict(), os.path.join(os.environ['SM_MODEL_DIR'], 'model.pth'))`. The trap variant: `/opt/ml/output/` (no `/data` suffix) gets a `failure` file written to it if the job exits non-zero, but does NOT get uploaded as `output.tar.gz` — only `/opt/ml/output/data/` does.

---

## Q145 — Domain 2: ML Model Development
**Objective:** Apply the `MaxWaitTime` ≥ `MaxRuntime` invariant for Managed Spot training

A teammate submits `CreateTrainingJob` with `EnableManagedSpotTraining=true`, `MaxRuntimeInSeconds=10800` (3 h), `MaxWaitTimeInSeconds=7200` (2 h). The API returns a `ValidationException`. What is the correct fix for a 3-hour training run that should tolerate up to 1 extra hour of Spot capacity wait?

- A. `MaxRuntime=10800`, `MaxWaitTime=14400` (4 h total budget).
- B. `MaxRuntime=7200`, `MaxWaitTime=10800` — swap the values.
- C. Remove `MaxWaitTimeInSeconds` entirely; SageMaker derives it automatically.
- D. `MaxRuntime=10800`, `MaxWaitTime=5400` — half the runtime to save money.

**Answer:** A
**Explanation:** The API enforces **`MaxWaitTimeInSeconds ≥ MaxRuntimeInSeconds`** when Spot is enabled (`EnableManagedSpotTraining=true`). The relationship is `MaxWait = MaxRuntime + (how long you tolerate waiting for Spot capacity)`. For 3 h of training + 1 h of capacity tolerance, `MaxWait = 14400`. Removing the parameter is invalid when Spot is on. Halving `MaxWait` (the D option) is the textbook wrong answer that "saves money" — it guarantees the job will hit `MaxWaitTimeExceeded` before it even gets capacity. The implied second part of this story (often a follow-up question) is that **the script must also write checkpoints to `/opt/ml/checkpoints/` and resume from them on restart** — SageMaker doesn't checkpoint for you; if you forget, every Spot reclaim restarts from scratch and you pay more, not less.

---

## Q146 — Domain 2: ML Model Development
**Objective:** Recognize the script-mode `if __name__ == '__main__':` requirement

A team deploys a PyTorch model trained via script mode (`Estimator(entry_point='train.py', source_dir='./src')`). The endpoint deploys successfully but returns nonsense predictions: every response looks like the model is being re-trained on the input. The container logs show training-loop output during inference. What's the root cause?

- A. The endpoint accidentally uses the training image; switch to the inference DLC.
- B. The `train.py` script lacks an `if __name__ == '__main__':` guard, so the training code executes when SageMaker imports the script to find inference handlers (`model_fn`, `input_fn`, `predict_fn`, `output_fn`).
- C. The `model.tar.gz` is corrupt and SageMaker fell back to a random-init model.
- D. The endpoint instance type is too small and PyTorch is failing silently.

**Answer:** B
**Explanation:** SageMaker's inference container **imports** your `train.py` script via `SAGEMAKER_PROGRAM` to discover the four handler functions (`model_fn`, `input_fn`, `predict_fn`, `output_fn`). Without the `if __name__ == '__main__':` guard, every import re-executes the entire training body, including any side-effect operations on the loaded model — and the symptoms range from "endpoint silently retrains the model on the input data and returns nonsense" (your scenario) to bizarre import-time errors and "subprocess failed" with cryptic exit codes. This is the **canonical script-mode foot-gun**, and the single most important structural rule of the script-mode contract. The fix is one line: wrap the training body in `if __name__ == '__main__': train(parse_args())`.

---

## Q147 — Domain 2: ML Model Development
**Objective:** Identify the canonical built-in for sparse high-dimensional implicit-feedback recsys

A team needs to model click-through on an ad-impression dataset with 50M rows, 10M unique users × 500K unique items, and ~99.99% sparsity. They want a SageMaker built-in algorithm. Which is the right choice — and what input format does it require?

- A. XGBoost with `text/csv` input.
- B. K-NN with `recordIO-protobuf` input.
- C. Factorization Machines with `recordIO-protobuf` input (CSV is not supported).
- D. Linear Learner with `text/csv` input.

**Answer:** C
**Explanation:** Factorization Machines is *designed* for sparse high-dimensional pair data (recsys, CTR, ad targeting). **Its only accepted input format is `recordIO-protobuf`** — CSV is not supported because the sparse `(index, value)` encoding is essential at FM's scale (CSV would force a dense `10M × 500K` matrix materialization that no instance can hold). XGBoost handles dense or moderately sparse tabular but lacks FM's explicit interaction-term modeling at this sparsity. k-NN is supervised similarity lookup against a stored FAISS index — wrong shape for implicit feedback. Linear Learner has no interaction term. In a 2026 production reality: Amazon Personalize has largely displaced FM for vanilla recsys; FM survives where Personalize's API surface doesn't fit, or as a feature generator feeding a downstream XGBoost ranker. The exam, however, still tests the catalogue.

---

## Q148 — Domain 2: ML Model Development
**Objective:** Recognize the XGBoost CSV input contract

You package training data for SageMaker built-in XGBoost. The team's existing CSV has columns `[id, feature_1, feature_2, ..., feature_n, label]` with a header row, and the model fails to train with non-descriptive errors. Pick the two changes required (Select TWO).

- A. Move the `label` column to be the first column.
- B. Drop the header row.
- C. Convert the file to Parquet to bypass the header requirement.
- D. Drop the `id` column (XGBoost cannot consume non-feature columns).
- E. Switch to `application/x-recordio-protobuf` format.

**Answer:** A, B
**Explanation:** SageMaker built-in XGBoost with `text/csv` requires **label = first column** and **no header row** — both are non-negotiable for the legacy XGBoost container contract. The `id` column will be treated as a feature (a minor leak issue but not the reason for failure — drop it for clean training but the job will still run). Parquet *is* supported (on XGBoost 1.7-1+) but doesn't change the label-position requirement: Parquet expects the same label-first column ordering, just with column-typed columns. RecordIO-protobuf is **not an XGBoost input format** — that's an FM / Linear Learner / K-Means thing. Same label-first convention applies to SageMaker Linear Learner CSV too — easy to forget.

---

## Q149 — Domain 2: ML Model Development
**Objective:** Distinguish CPU-only built-in algorithms

For each scenario below, an answer paired Random Cut Forest (RCF) with an instance type. Which combination is **invalid**?

- A. RCF on `ml.c5.4xlarge` (CPU).
- B. RCF on `ml.m5.2xlarge` (CPU).
- C. RCF on `ml.p3.2xlarge` (GPU).
- D. RCF distributed across 4× `ml.c5.4xlarge`.

**Answer:** C
**Explanation:** **Random Cut Forest is CPU-only.** Pairing RCF with any GPU instance is wrong by construction. RCF *is* parallelizable across multiple CPU instances. This is one of the most-tested algorithm-vs-instance pairings on the exam.

---

## Q150 — Domain 2: ML Model Development
**Objective:** Pick the right input format for DeepAR

A retail team has 5,000 SKUs with 18 months of weekly sales history in a single CSV (one row per SKU per week). They want SageMaker DeepAR for probabilistic demand forecasting. Which statement is correct?

- A. DeepAR accepts the CSV as-is — set `ContentType=text/csv`.
- B. DeepAR requires JSON Lines or Parquet input; the CSV must be converted (e.g., one JSON-Lines record per series with `start`, `target[]`, optional `cat`, `dynamic_feat`).
- C. DeepAR requires `recordIO-protobuf` like Factorization Machines.
- D. DeepAR only supports a single time series, not many related series.

**Answer:** B
**Explanation:** DeepAR's accepted formats are **JSON Lines or Parquet — not CSV, not RecordIO-protobuf**. Each line is one series: `{"start": "2020-01-01", "target": [v1, v2, …], "cat": [...], "dynamic_feat": [[...]]}`. DeepAR's strength is global learning across *many related* series — this scenario (5,000 SKUs × 18 months × weekly) is exactly what it's built for. Required hyperparameters: `prediction_length`, `context_length` (with `prediction_length ≤ context_length` as a rule of thumb), `time_freq` (`1W` here). The `likelihood` choice must match the data — `gaussian` for continuous symmetric, `negative-binomial` for counts (which retail sales often are), `student-T` for heavy-tailed. In the 2026 reality, with Amazon Forecast closed to new customers (July 29, 2024), DeepAR + SageMaker Canvas have become the recommended migration paths.

---

## Q151 — Domain 2: ML Model Development
**Objective:** Distinguish single-instance built-in algorithms

A team plans distributed multi-instance training for a vision pipeline. For which of the following built-ins is multi-instance distribution **NOT** supported (Select TWO)?

- A. Image Classification — MXNet
- B. Semantic Segmentation
- C. Object Detection — TensorFlow (parallel only across GPUs on one instance)
- D. XGBoost
- E. Linear Learner

**Answer:** B, C
**Explanation:** **Semantic Segmentation is GPU-only, single-instance** — cannot scale across instances. **Object Detection — TensorFlow** (and Image Classification — TensorFlow) is parallel only across GPUs on a *single* instance. Image Classification — MXNet *is* multi-instance distributable. XGBoost and Linear Learner both support distributed training across instances.

---

## Q152 — Domain 2: ML Model Development
**Objective:** Recognize legacy / deprecated built-in algorithms

A team in 2026 wants to translate English support tickets into Spanish at scale. Which option is the AWS-recommended modern path for the MLA-C01 exam?

- A. SageMaker Sequence-to-Sequence (Seq2Seq) built-in, single-instance GPU training.
- B. Amazon Translate (managed) or a HuggingFace `marian-mt` fine-tune via the HuggingFace Estimator, or a Bedrock model — Seq2Seq is effectively dead in 2025+.
- C. BlazingText supervised mode with translation labels.
- D. K-NN with translation pairs as features.

**Answer:** B
**Explanation:** **Seq2Seq is effectively dead in 2026.** The modern AWS answer for translation is Amazon Translate (managed), HuggingFace via SageMaker (`marian-mt`, T5), or Bedrock (Claude/Titan). Seq2Seq is GPU-only, single-instance, and not how new translation workloads should be built. BlazingText supervised does text classification, not translation; k-NN is unrelated.

---

## Q153 — Domain 2: ML Model Development
**Objective:** Distinguish NTM vs LDA

A research team wants GPU-accelerated, distributed topic modeling on a 200 GB corpus. Which built-in algorithm should they choose?

- A. LDA — supports any size corpus and GPU clusters.
- B. NTM — supports CPU or GPU and distributed training across instances.
- C. BlazingText Word2Vec — fastest path to topics.
- D. K-Means on TF-IDF vectors — equivalent results.

**Answer:** B
**Explanation:** **NTM (Neural Topic Model)** supports CPU or GPU, distributed across instances, and is the modern AWS topic-modeling algorithm. **LDA is CPU-only and single-instance** — eliminated by the "GPU-accelerated, distributed" requirement. BlazingText does embeddings, not topic modeling. K-Means on TF-IDF can cluster docs but does not produce topic-word distributions.

---

## Q154 — Domain 2: ML Model Development
**Objective:** Recognize the k-NN vs K-Means distractor pattern

A data science team needs to predict regression outputs by averaging the targets of the 5 closest historical training examples (by Euclidean distance). Which built-in is the right choice?

- A. K-Means with `k=5`.
- B. k-NN (`predictor_type=regressor`, `k=5`).
- C. Linear Learner with 5 parallel models.
- D. PCA with 5 components.

**Answer:** B
**Explanation:** **k-NN is the supervised lazy learner** that predicts from the average / vote of the *k* closest training points. K-Means is **unsupervised clustering** — it partitions data into groups by Euclidean distance but doesn't use labels and cannot do regression. This swap is one of the most common exam distractors.

---

## Q155 — Domain 2: ML Model Development
**Objective:** Recognize the IP Insights use case

A bank's security team wants to flag suspicious login events where a user has never authenticated from a specific IP block. Auth logs are in S3 as CSV with columns `user_id, source_ip`. Which built-in is the best fit?

- A. Random Cut Forest on the IP-octet features.
- B. IP Insights, with the CSV's `(entity_id, ipv4_address)` pair format.
- C. Amazon Fraud Detector — IP Insights doesn't handle auth logs.
- D. K-Means clustering users by IP-octet vectors.

**Answer:** B
**Explanation:** **IP Insights is purpose-built for entity-IP behavioral anomaly detection** — exactly account-takeover, 2FA triggers, bot filtering. The CSV `(entity, ipv4)` pair format is the give-away. RCF is general numeric anomaly detection without the entity-IP semantics. Fraud Detector targets *transactional* fraud, not auth-log patterns.

---

## Q156 — Domain 2: ML Model Development
**Objective:** Pick the right `distribution=` strategy for PyTorch ≥ 1.13 on non-EFA GPUs

A team is training a PyTorch 2.1 model with `instance_count=4`, `instance_type='ml.g5.12xlarge'` (no EFA). They want modern, simple distributed data parallel without writing MPI configuration. Which `distribution=` value is correct?

- A. `{'mpi': {'enabled': True, 'processes_per_host': 8}}`
- B. `{'smdistributed': {'dataparallel': {'enabled': True}}}`
- C. `{'torch_distributed': {'enabled': True}}`
- D. `{'parameter_server': {'enabled': True}}`

**Answer:** C
**Explanation:** `torch_distributed` uses **`torchrun` under the hood** (modern path for PyTorch ≥ 1.13). SMDDP is only worth using on EFA-equipped instances (p3dn, p4d, p4de, p5, trn1); on g5 it provides no gain over plain NCCL. MPI is the legacy Horovod path (mostly TF). Parameter Server is legacy TF.

---

## Q157 — Domain 2: ML Model Development
**Objective:** Pick the right `distribution=` strategy for SMDDP

When is `{'smdistributed': {'dataparallel': {'enabled': True}}}` actually worth using over `torch_distributed`?

- A. Single-node training where SMDDP's AllReduce optimization beats NCCL on one host.
- B. Multi-node training on EFA-equipped instances (e.g., `ml.p4d.24xlarge`, `ml.p5.48xlarge`, `ml.trn1.32xlarge`), where SMDDP's EFA-optimized AllReduce/AllGather beats plain NCCL by 20–40%.
- C. Any TensorFlow workload regardless of hardware.
- D. CPU-only training jobs to parallelize across instances.

**Answer:** B
**Explanation:** SMDDP replaces NCCL's collectives with **EFA-optimized implementations**, paying off only on multi-node EFA-equipped GPU/Trainium clusters. On single-node training NCCL is already optimal. SMDDP is PyTorch (and HF PyTorch backend), not TensorFlow. CPU jobs don't benefit.

---

## Q158 — Domain 2: ML Model Development
**Objective:** Mitigate the `requirements.txt` cold-start tax in script mode

A team's PyTorch script-mode training jobs take ~14 minutes to start before any GPU work begins because `requirements.txt` installs FlashAttention, `bitsandbytes`, `xformers`, and other CUDA-compiled deps that recompile on every job start. At 4× `ml.p4d.24xlarge` (~$32/hr each), that is roughly $60 of pure pip-install cost per run. What is the most cost-effective mitigation?

- A. Switch from PyTorch DLC to vanilla `python:3.11` base and install everything from PyPI.
- B. Build a custom Docker image **FROM the AWS DLC base**, `pip install` the slow deps at *build* time, push to ECR, reference via `image_uri=`. Inherits DLC's toolkit, framework pins, CUDA, and SageMaker compatibility — only adds what you need.
- C. Increase the instance type to `ml.p4de.24xlarge` so `pip install` runs faster.
- D. Raise `MaxRuntimeInSeconds` so the installation time doesn't count against the budget.

**Answer:** B
**Explanation:** Extending the DLC (**Stage 3 in the four-stage production progression: raw `requirements.txt` → vendored wheels → custom DLC-derived image → baked weights**) is the AWS-recommended fix. You inherit the SageMaker training toolkit, DLC's pinned framework + CUDA + cuDNN + NCCL, the `/opt/ml/...` contract, and pre-warmed AWS-internal caching — only baking in the slow custom layer (FlashAttention, `bitsandbytes`, `xformers`). Replacing the DLC with vanilla Python (option A) abandons all of that and pushes you into full BYOC. Bigger instances (C) don't change pip's wall-clock. `MaxRuntime` (D) is unrelated — install time still counts against your budget either way; raising it just lets the doomed job run longer. The Dockerfile pattern: `FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-training:...` + `RUN pip install --no-cache-dir flash-attn==... bitsandbytes==... peft==...` + reference via `image_uri=` on the Estimator.

---

## Q159 — Domain 2: ML Model Development
**Objective:** Recognize HuggingFace Estimator vs PyTorch Estimator selection

A team wants to fine-tune Llama-2-7b-hf on customer-support transcripts. They want the path of least resistance with no CUDA toolkit drift. Which Estimator is the right default?

- A. `sagemaker.pytorch.PyTorch` with `pip install transformers accelerate peft bitsandbytes` in `requirements.txt`.
- B. `sagemaker.huggingface.HuggingFace` — the HF DLC bakes in `transformers`, `accelerate`, `peft`, `trl`, `bitsandbytes`, and matching CUDA/NCCL, pre-tested together.
- C. `sagemaker.sklearn.SKLearn` — wraps any Python script.
- D. `sagemaker.tensorflow.TensorFlow` with the `transformers` TF backend.

**Answer:** B
**Explanation:** The **HuggingFace Estimator** is the quiet 2026 default for any transformer training, fine-tuning, or RLHF on AWS. The HF DLC is pre-validated for CUDA / NCCL / `transformers` / `accelerate` / `peft` / `bitsandbytes` compatibility — eliminating the 5–10 minute cold-start tax and the drift bugs that come from rebuilding the dependency stack with `requirements.txt`. PyTorch Estimator + manual installs trades pre-tested compatibility for cold-start cost. SKLearn doesn't do GPU; TF backend is a niche path.

---

## Q160 — Domain 2: ML Model Development
**Objective:** Match BYOC training argv contract

SageMaker invokes a BYOC training container as `docker run <image> train`. Which option below correctly satisfies the entrypoint contract?

- A. `ENTRYPOINT ["/usr/bin/tini", "--", "python", "train.py"]`
- B. `ENTRYPOINT ["python", "/opt/program/train.py"]`
- C. `COPY train.py /opt/program/train` + `RUN chmod +x /opt/program/train` + `ENV PATH="/opt/program:${PATH}"` + `ENTRYPOINT ["train"]`
- D. `CMD ["bash", "-c", "python /app/train_script.py --launch"]`

**Answer:** C
**Explanation:** SageMaker's training argv is **always the literal string `train`** — not `train.py`, not `python train.py`. Put the executable on `$PATH` named `train` and set `ENTRYPOINT ["train"]`. `tini` is explicitly disallowed by AWS docs ("can't use `tini` as entry point"). Hardcoded paths to `train.py` break because SageMaker passes `train` as argv[1], not as the script name. `CMD` is overridden by SageMaker's invocation.

---

## Q161 — Domain 2: ML Model Development
**Objective:** Memorize the BYOC inference HTTP contract

A BYOC inference container is failing the SageMaker readiness check during endpoint creation. Pick the **single correct** statement about the contract.

- A. Bind to `0.0.0.0:8443`, implement `GET /healthz` (5 s deadline) and `POST /predict` (30 s deadline), pass readiness within 10 minutes.
- B. Bind to `0.0.0.0:8080`, implement `GET /ping` (2 s deadline) and `POST /invocations` (60 s deadline), pass readiness within 8 minutes.
- C. Bind to `0.0.0.0:80`, implement `GET /` (1 s deadline) and `POST /predict` (120 s deadline), pass readiness within 15 minutes.
- D. Bind to `0.0.0.0:5000`, implement `GET /status` (2 s deadline) and `POST /serve` (60 s deadline), pass readiness within 5 minutes.

**Answer:** B
**Explanation:** Memorize the four numbers and two routes: **port 8080**, **`GET /ping` (2 s)**, **`POST /invocations` (60 s)**, **8-minute startup readiness window**. Plus: **socket-accept within 250 ms**, container **must run as root** (AWS docs: "SageMaker AI expects all containers to run with root users"), must **not use `tini` as entrypoint** (it confuses the `train`/`serve` argv contract), must **not bundle NVIDIA drivers** (the host provides them via `nvidia-docker`; bundling breaks runtime injection), and must use **`ENTRYPOINT` exec form** (`["executable", "param", ...]`) so signals propagate. Shutdown is `SIGTERM` followed by `SIGKILL` after a 30-second grace period. Any answer with port 8443, `/healthz`, `/predict`, or different deadlines is a distractor — these contract numbers do not change and are tested in three or four flavors on every exam form.

---

## Q162 — Domain 2: ML Model Development
**Objective:** Recognize when Triton-on-SageMaker is the right serving choice

A team needs to serve four PyTorch model variants on a single GPU with dynamic batching, plus an ensemble that pipes the output of one model into another server-side. Which serving solution is the canonical choice?

- A. SageMaker Multi-Model Endpoint (MME) with the default Python model server.
- B. NVIDIA Triton Inference Server on SageMaker — multi-framework, multi-model-per-GPU, dynamic batching, server-side ensembles.
- C. SageMaker Serverless Inference with 6 GB memory.
- D. Four separate real-time endpoints behind an API Gateway router.

**Answer:** B
**Explanation:** **Triton on SageMaker** is the canonical answer for "multiple models on a single GPU," "dynamic batching," and "server-side ensembles." Triton's design fundamentals: **concurrent model execution** (N parallel copies of one model on one GPU), **dynamic batching** (incoming requests buffered briefly then issued as one GPU batch), **multi-framework backends in one process** (TensorRT, ONNX Runtime, PyTorch, TensorFlow, Python, OpenVINO), **ensemble models** (DAG of models with server-side dataflow). MME on GPU is *implemented* on top of Triton — there is no other way to do GPU MME on SageMaker. AWS published BERT-large benchmarks showing **up to 84% cost reduction** vs vanilla PyTorch serving (`3,192 inv/min` at `$7.36/hr` on `ml.g4dn.xlarge` vs `490 inv/min` at `$45.66/hr`). Serverless Inference is CPU-only, capped at 6 GB, and rejects >10 GB images outright. Four separate endpoints multiplies cost ~4× and gives up dynamic batching.

---

## Q163 — Domain 2: ML Model Development
**Objective:** Avoid the Triton/LMI mistake for LLM serving in 2025-26

A team is deploying Llama-3-70B as a real-time endpoint and wants the AWS-recommended container in 2025-26. Which is correct?

- A. NVIDIA Triton Inference Server on SageMaker — Triton is always the right answer for any LLM.
- B. The SageMaker LMI (Large Model Inference) container (DJL) or vLLM-based LLM serving on SageMaker — the 2025-26 LLM-serving path; not generic Triton.
- C. A custom Flask + PyTorch container on `ml.t3.medium`.
- D. SageMaker Built-in Algorithm: Seq2Seq.

**Answer:** B
**Explanation:** For **LLM serving in 2025-26**, the AWS-recommended path is **LMI/DJL or vLLM**, not generic Triton. Triton remains the right answer for *multi-framework* / *multi-model-on-one-GPU* / *server-side ensembles*, but not for LLM inference specifically. Flask on `ml.t3.medium` cannot host a 70B model. Seq2Seq is a legacy translation algorithm, not an LLM.

---

## Q164 — Domain 2: ML Model Development
**Objective:** Recognize ECR `IMMUTABLE` tag mutability as production hygiene

An audit shows that the production endpoint at `EndpointConfig` v3 was deployed with `image_uri=...:v1.2.0`, but pulling `:v1.2.0` from ECR today returns a *different* image than was deployed last quarter. The ECR repo was configured with `imageTagMutability=MUTABLE`. What's the fix?

- A. Switch to `imageTagMutability=IMMUTABLE` and adopt semver or git-SHA tags so `:v1.2.0` cannot be overwritten.
- B. Always reference `:latest` to ensure the newest image is used.
- C. Enable basic ECR scanning; this prevents tag overwrites.
- D. Move the image to S3 and reference by S3 URI instead.

**Answer:** A
**Explanation:** **Production ECR repos must be `IMMUTABLE`-tagged.** Once `:v1.2.0` is pushed, nobody can overwrite it. Combine with semver or git-SHA tags. `:latest` is the *worst* answer (mutable by definition). Scanning has nothing to do with tag mutability. SageMaker pulls images from ECR, not S3.

---

## Q165 — Domain 2: ML Model Development
**Objective:** Recognize multi-arch BYOC for Graviton

A team's Karpenter autoscaler in EKS is provisioning ARM64 (Graviton) nodes alongside x86. Their BYOC image was built only for `linux/amd64`, and inference latency on Graviton spikes 5–20×. What is the proper fix?

- A. Force Karpenter to only schedule on x86 nodes — accept the cost premium.
- B. Build a multi-arch image with `docker buildx --platform linux/amd64,linux/arm64 --push`, storing an OCI manifest list in ECR so each node's daemon picks the matching variant.
- C. Add `--platform=linux/amd64` to the SageMaker endpoint configuration.
- D. Compile the model to ONNX — ONNX is arch-agnostic at runtime.

**Answer:** B
**Explanation:** **`docker buildx` multi-arch** is the right answer. ECR stores a manifest list and the pulling node's daemon picks the right arch automatically. Without it, the amd64 image runs under QEMU emulation on ARM, with the 5-20× latency hit. Constraining Karpenter discards Graviton's 20-40% cost savings. There is no `--platform` knob on `EndpointConfig`. ONNX runtime still needs an arch-matching binary.

---

## Q166 — Domain 2: ML Model Development
**Objective:** Identify the mandatory JumpStart deploy argument for licensed models

A data scientist runs:

```python
model = JumpStartModel(model_id="meta-textgeneration-llama-3-8b-instruct", ...)
predictor = model.deploy(endpoint_name="llama3-8b")
```

The call fails with an EULA-related exception. What's missing?

- A. `accept_eula=True` on the `.deploy()` call — mandatory for licensed models (Llama, Mistral commercial, Gemma, Stable Diffusion).
- B. An IAM permission on `bedrock:InvokeModel`.
- C. A Marketplace subscription — Meta licenses Llama via AWS Marketplace.
- D. The `endpoint_config_name` parameter — JumpStart requires it explicitly.

**Answer:** A
**Explanation:** **`accept_eula=True`** is mandatory at `.deploy()` time for EULA-gated models — Llama family (Llama Community License), Mistral commercial variants, Gemma (Gemma Terms of Use), Stable Diffusion (CreativeML Open RAIL++-M). The SDK raises an explicit exception if you skip it — there is no CLI / console workaround. The flag is **per-account, per-region** — accepting in dev does not propagate to prod, so bake it into your IaC. JumpStart is *not* Bedrock — Bedrock's Claude/Titan/Nova families are not in JumpStart at all. Llama is EULA-gated but *not* Marketplace-gated; that distinction (Marketplace gating with per-hour software fees) is AI21 / Cohere / some Stability variants. `endpoint_config_name` is an optional parameter. This is the single most-tested mechanical detail in the JumpStart surface.

---

## Q167 — Domain 2: ML Model Development
**Objective:** Recognize that the EULA flag is required at fine-tune time but optional on re-deploy

A team has already fine-tuned Llama-3-8B via `JumpStartEstimator.fit(..., accept_eula=True)`. They now want to redeploy the *fine-tuned* `model.tar.gz` artifact later via a separate `JumpStartModel(...)`. Which statement is correct?

- A. `accept_eula=True` is mandatory on every subsequent `.deploy()` of the fine-tuned artifact — per AWS contract.
- B. After fine-tuning the weights are no longer the original Meta weights, so `accept_eula=True` is **no longer programmatically required** at deploy time for the fine-tuned artifact (the upstream license still applies legally — accepted once at training).
- C. `accept_eula=True` is never required for JumpStart; it's a no-op.
- D. The fine-tuned model must be re-registered with `accept_eula=True` in the Model Registry first.

**Answer:** B
**Explanation:** Per AWS docs: after fine-tuning, the weights are no longer the original licensed Meta weights, so the SDK doesn't require the flag on re-deploy. The upstream license still applies legally (you accepted it once at training). This is one of the most-tested JumpStart subtleties.

---

## Q168 — Domain 2: ML Model Development
**Objective:** Pick JumpStart vs Bedrock based on constraints

For each scenario below, which is the AWS-canonical 2025-26 answer? "Build a public-facing chat assistant that calls Claude 3.5 Sonnet with the fewest infrastructure choices, paying per token only."

- A. JumpStart deploy of Anthropic Claude as a SageMaker real-time endpoint.
- B. Amazon Bedrock with Claude — no infrastructure, pay per token, zero ops.
- C. BYOC with custom Anthropic SDK.
- D. SageMaker Inference Components hosting Claude weights.

**Answer:** B
**Explanation:** **Anthropic Claude is Bedrock-only.** It is not in the JumpStart catalog. Bedrock is the AWS-canonical "managed, pay-per-token, no infra" path. Bedrock is the *default* for FM workloads; JumpStart only when you have a justifying constraint (open weights, VPC isolation, high steady throughput, fine-tune control).

---

## Q169 — Domain 2: ML Model Development
**Objective:** Recognize JumpStart Marketplace pricing surprise

A team deploys an AI21 Jamba 1.5 model from JumpStart on `ml.g5.12xlarge` (~$7.09/hr SageMaker on-demand) and expects the bill to be ~$5,200/month at 24×7. The actual bill comes in at ~$9,000/month. What is the most likely cause?

- A. SageMaker autoscaling silently provisioned extra instances.
- B. The AI21 model is sold through AWS Marketplace and incurs an **additional per-hour software fee** on top of the SageMaker instance hours.
- C. Egress data transfer to the internet from the endpoint.
- D. CloudWatch Logs ingestion of inference traffic.

**Answer:** B
**Explanation:** Proprietary providers in JumpStart — **AI21, Cohere, some Stability variants** — route through AWS Marketplace, which adds a vendor software fee on top of SageMaker instance hours. Open-weight models (Llama, Mistral, Falcon, Phi, Gemma) never incur this surcharge. Always check whether the model card shows a "Subscribe in AWS Marketplace" gate.

---

## Q170 — Domain 2: ML Model Development
**Objective:** Recognize Autopilot V1 vs V2 API

A Python snippet calls `CreateAutoMLJob` (V1 API) with `ProblemType='ImageClassification'`. The call returns a validation error. What is wrong and how do you fix it?

- A. V1 is tabular-only. Switch to **`CreateAutoMLJobV2`** with `AutoMLProblemTypeConfig.ImageClassificationJobConfig`.
- B. The IAM role lacks `s3:GetObject` on the input bucket.
- C. Image classification requires `Mode='ENSEMBLING'` explicitly.
- D. `ProblemType` was deprecated in V1 — pass `TargetAttributeName` only.

**Answer:** A
**Explanation:** **`CreateAutoMLJob` V1 supports only tabular** (regression, binary, multiclass classification). For image classification, text classification, time-series forecasting, or LLM fine-tuning, you must use **V2**, which routes problem-type config into `AutoMLProblemTypeConfig.<ProblemType>JobConfig` blocks.

---

## Q171 — Domain 2: ML Model Development
**Objective:** Distinguish Autopilot Ensembling vs HPO algorithm pools

In Autopilot tabular mode, which algorithm appears **only** in Ensembling mode (AutoGluon pool) and not in HPO mode?

- A. XGBoost
- B. Linear Learner (the SageMaker built-in)
- C. LightGBM
- D. Multi-layer perceptron (MLP) neural network

**Answer:** C
**Explanation:** **Ensembling mode (AutoGluon)** runs: LightGBM, CatBoost, XGBoost, Random Forest, ExtraTrees, scikit-learn Linear Models, NN-torch, NN-fastai. **HPO mode** has only three: Linear Learner (the SageMaker built-in), XGBoost, and an MLP. LightGBM / CatBoost only live in Ensembling. A common exam trap: questions offer "Linear Learner in Ensembling mode" — wrong; Ensembling's "Linear Models" plural = scikit-learn LR/logistic.

---

## Q172 — Domain 2: ML Model Development
**Objective:** Recognize the three Auto-mode fallback triggers

For a 50 MB tabular CSV in a VPC-locked S3 bucket where the bucket policy restricts access to a VPC endpoint, Autopilot is invoked with `Mode='AUTO'`. Which mode actually runs?

- A. Ensembling — dataset is well under the 100 MB cutoff.
- B. HPO — Autopilot's reader can't see the bucket from outside the VPC, so it falls back to HPO.
- C. The job fails with a validation error.
- D. Auto creates a heterogeneous cluster combining both modes.

**Answer:** B
**Explanation:** Auto mode reads the dataset size to decide. If it *can't* read the size, it falls back to HPO. The **three fallback triggers**: VPC-locked bucket, `S3DataType=ManifestFile`, or `S3Uri` prefix with >1000 items. The practical fix: always set `Mode` explicitly. This is one of the most-tested Autopilot edge cases.

---

## Q173 — Domain 2: ML Model Development
**Objective:** Recognize `AutoMLStep` as Ensembling-only

A platform team wants to integrate Autopilot into a SageMaker Pipeline using `AutoMLStep` and specifically requests HPO mode because the dataset is 1.5 GB. What is the constraint?

- A. `AutoMLStep` accepts both Ensembling and HPO — set `Mode='HYPERPARAMETER_TUNING'`.
- B. **`AutoMLStep` is ENSEMBLING-only.** Mitigations: (i) switch to Ensembling and accept its <100 MB sweet spot — risky here; or (ii) fall back to custom Lambda + Processing steps that poll the AutoML job.
- C. `AutoMLStep` was deprecated; use `ProcessingStep` for AutoML.
- D. `AutoMLStep` requires `image/jpeg` content type.

**Answer:** B
**Explanation:** **`AutoMLStep` is ENSEMBLING-only.** It was launched alongside Ensembling mode in November 2022 and does not accept `Mode='HYPERPARAMETER_TUNING'`. For the 1.5 GB dataset, two valid mitigations: (i) accept Ensembling's mid-band performance (Ensembling tops out at best speed on <100 MB datasets but does still work above that), or (ii) fall back to a custom Lambda + Processing step that polls the AutoML job via `DescribeAutoMLJobV2` and gates downstream `ModelStep` on its status. The instinct to set `Mode='HYPERPARAMETER_TUNING'` and expect the pipeline-native step to handle it is wrong by design. This is a sharp design-review trap that the exam reuses verbatim.

---

## Q174 — Domain 2: ML Model Development
**Objective:** Identify Autopilot's auto-deploy cost gotcha

A junior engineer enables `ModelDeployConfig.AutoGenerateEndpointName=True` on an Autopilot demo, then goes on vacation for three weeks. The default endpoint runs on `ml.m5.xlarge` (~$0.23/hr in us-east-1). Approximately what does the bill look like, and what is the mitigation?

- A. ~$10 — the demo endpoint auto-stops after the job completes; nothing to mitigate.
- B. ~$170/month-rate, so ~$120 over 3 weeks; mitigation: call `DeleteEndpoint`. Production guardrails: never enable auto-deploy in interactive experiments, add a SageMaker training-spend Budget + EventBridge alarm, and codify a `DeleteEndpoint` runbook.
- C. The endpoint is free for the first 30 days — no bill.
- D. The endpoint auto-scales to zero when idle — no bill.

**Answer:** B
**Explanation:** **Auto-deployed endpoints run 24/7 until you `DeleteEndpoint`.** `ml.m5.xlarge` ≈ $0.23/hr ≈ **$170/month**. The single most-common Autopilot cost-surprise. Mitigations: never auto-deploy interactive experiments, set a SageMaker spend Budget, write the DeleteEndpoint runbook.

---

## Q175 — Domain 2: ML Model Development
**Objective:** Pick the right Autopilot objective metric for severely imbalanced binary classification

A fraud-detection team has a 99/1 imbalanced binary dataset where false negatives are very costly. The default Autopilot objective for binary classification is `F1`. Which override is most appropriate?

- A. `Accuracy` — captures overall correctness.
- B. `Precision` — minimizes false positives.
- C. `Recall` or `BalancedAccuracy` — captures the cost of false negatives and handles class imbalance.
- D. `MSE` — works for any classification task.

**Answer:** C
**Explanation:** For **rare-event detection where FN is costly**, `Recall` (catch as many true positives as possible) or `BalancedAccuracy` (which has built-in imbalance handling) is the right override. `Accuracy` is misleading on 99/1 imbalance (always predict majority → 99% accuracy). `Precision` minimizes FP — the *opposite* of what's needed. `MSE` is a regression metric.

---

## Q176 — Domain 2: ML Model Development
**Objective:** Identify Autopilot's per-mode sample-weight support

An imbalanced binary classifier is being trained via Autopilot with `SampleWeightAttributeName='weight'` set. The team chose `Mode='HYPERPARAMETER_TUNING'` because the dataset is 1.2 GB. After training, the model behaves as if the weight column was never used. Why?

- A. The weight column had nulls and was silently dropped.
- B. HPO mode silently ignores `SampleWeightAttributeName`; only Ensembling consumes sample weights. Either move to Ensembling (small-data limit) or pre-balance the data with explicit class weights.
- C. Sample weights only apply to regression problems, not classification.
- D. The `BalancedAccuracy` metric overrides sample weights.

**Answer:** B
**Explanation:** **Only Ensembling mode honors `SampleWeightAttributeName`**; HPO mode silently ignores it. Additionally, even in Ensembling, `BalancedAccuracy` and `InferenceLatency` ignore sample weights. This is the silent-failure exam trap.

---

## Q177 — Domain 2: ML Model Development
**Objective:** Distinguish Autopilot's four output artifacts

For a tabular Autopilot job, which file lets a downstream team **reproduce and modify** each candidate pipeline (preprocessors, algorithms, HP grids)?

- A. `SageMakerAutopilotDataExplorationNotebook.ipynb`
- B. `SageMakerAutopilotCandidateDefinitionNotebook.ipynb`
- C. `analysis.json` from the Clarify processing job
- D. `model.tar.gz` for the best candidate

**Answer:** B
**Explanation:** The **Candidate Definition notebook** contains the exact Python code for each candidate pipeline — preprocessors as sklearn Pipelines, algorithm + hyperparameter grid, training-job invocations. This is the reproducibility-and-customization handoff. Data Exploration shows EDA; `analysis.json` is the Clarify report; `model.tar.gz` is the binary artifact. Note: the Candidate notebook is emitted **only for tabular problem types**, not for image / text / TS / LLM-FT.

---

## Q178 — Domain 2: ML Model Development
**Objective:** Recognize Studio Classic → Canvas rebrand

An analyst in 2026 wants a no-code AutoML experience in the unified SageMaker Studio. Where does the Autopilot UI live now?

- A. Studio Classic — the only place the Autopilot UI still works.
- B. **SageMaker Canvas** — the Autopilot UI migrated to Canvas as part of the unified Studio rollout. The `CreateAutoMLJobV2` API is unchanged behind both UIs.
- C. AWS Glue Studio.
- D. SageMaker Ground Truth.

**Answer:** B
**Explanation:** Beginning Nov 30, 2023, the Autopilot UI for no-code AutoML lives in **Canvas**, not in the Studio Classic Experiments tab. Studio Classic still has the legacy UI for backward compatibility. The underlying API (`CreateAutoMLJobV2`) is unchanged.

---

## Q179 — Domain 2: ML Model Development
**Objective:** Map experiment-tracking vocabulary to MLflow vs Experiments Classic

A data scientist sees the string `"TrialComponent"` in a CloudTrail entry. Which tracking system produced it?

- A. MLflow on SageMaker.
- B. SageMaker Experiments Classic — the term `TrialComponent` is a Classic-only object; MLflow has no equivalent (a Run holds params/metrics/artifacts directly).
- C. SageMaker Model Registry.
- D. SageMaker Clarify.

**Answer:** B
**Explanation:** **`TrialComponent` is Experiments Classic only.** MLflow uses Experiment → Run → (params, metrics, artifacts, LoggedModel). The two systems are wire-incompatible. If a string `TrialComponent` appears anywhere — in boto3, in CloudTrail, in a Studio URL — you're looking at Experiments Classic, not MLflow.

---

## Q180 — Domain 2: ML Model Development
**Objective:** Recognize the `experiment_config=` auto-tracking pattern in Experiments Classic

A team wants every `Estimator.fit()` call to automatically organize the resulting Trial Component under a specific Experiment + Run in the Studio Classic UI, without writing any logging code inside `train.py`. What's the minimum config?

- A. Wrap `train.py` in `with mlflow.start_run():`.
- B. Pass `experiment_config={'ExperimentName': ..., 'TrialName': ..., 'TrialComponentDisplayName': ...}` to `Estimator.fit()`.
- C. Call `CreateExperimentTracker` from boto3 before `.fit()`.
- D. Set environment variable `SAGEMAKER_EXPERIMENT_NAME` in the container.

**Answer:** B
**Explanation:** Pass `experiment_config=` to `.fit()` — Studio Classic then shows the job under `<ExperimentName> → <TrialName> → <TrialComponentDisplayName>`. No code change in `train.py`. The MLflow option is for the MLflow path. There is no `CreateExperimentTracker` API. The env-var pattern is not how Experiments Classic works.

---

## Q181 — Domain 2: ML Model Development
**Objective:** Recognize CloudTrail audit events for managed MLflow

An auditor asks for a complete record of every MLflow data-plane action (logged metric, logged param, created run) executed against the managed tracking server in the last 90 days. Where do those events live?

- A. CloudWatch Logs under `/aws/sagemaker/Experiments`.
- B. **CloudTrail** as events with the `Mlflow*` prefix (e.g., `MlflowCreateExperiment`, `MlflowLogMetric`, `MlflowLogModel`, `MlflowCreateModelVersion`).
- C. S3 server-access logs on the artifact bucket.
- D. Amazon Personalize event logs.

**Answer:** B
**Explanation:** CloudTrail logs both control-plane (`CreateMlflowTrackingServer`, `StopMlflowTrackingServer`, etc.) and **data-plane** MLflow operations under the **`Mlflow` prefix** — `MlflowCreateRun`, `MlflowLogMetric`, `MlflowLogParam`, `MlflowLogBatch`, `MlflowLogModel`. This is the complete audit trail required for SOC 2 / FedRAMP / model-risk management.

---

## Q182 — Domain 2: ML Model Development
**Objective:** Stop the MLflow tracking server during off-hours

A small team uses the managed MLflow tracking server only during business hours (provisioned, not serverless). They want to minimize cost between Friday evening and Monday morning while preserving all runs and registered models. What is the right approach?

- A. `DeleteMlflowTrackingServer` on Friday + `CreateMlflowTrackingServer` on Monday — quickest startup.
- B. `StopMlflowTrackingServer` on Friday + `StartMlflowTrackingServer` on Monday — compute meter stops, S3 artifacts and backend metadata persist across stop/start.
- C. Set the tracking-server size to `Small` permanently — no further savings possible.
- D. Move the artifact store to S3 Glacier Deep Archive.

**Answer:** B
**Explanation:** **Stop preserves data; Delete removes it.** A Stopped server stops the per-hour compute meter (S3 storage still bills) and resumes in 1–5 minutes when the first morning call comes in. This is the canonical EventBridge + Lambda cron pattern. Glacier on the artifact store would break MLflow's ability to read artifacts back.

---

## Q183 — Domain 2: ML Model Development
**Objective:** Identify the correct IAM action namespace for MLflow on SageMaker

You're writing an IAM policy for a data scientist who needs to create experiments and log metrics on a managed MLflow tracking server. Which set of actions is correctly namespaced?

- A. `mlflow:CreateExperiment`, `mlflow:LogMetric`, `mlflow:CreateRun` — vanilla MLflow actions.
- B. **`sagemaker-mlflow:CreateExperiment`, `sagemaker-mlflow:LogMetric`, `sagemaker-mlflow:CreateRun`** — data plane uses the `sagemaker-mlflow` prefix.
- C. `sagemaker:Mlflow*` — control and data plane share one service prefix.
- D. `aws-mlflow:Log*` — third-party plugin actions.

**Answer:** B
**Explanation:** Control plane = `sagemaker:CreateMlflowTrackingServer` etc. **Data plane = `sagemaker-mlflow:` (with hyphen)** for every MLflow REST verb. If any answer choice grants `mlflow:LogMetric` or `mlflow:*`, that answer is wrong. Memorize the two-namespace split.

---

## Q184 — Domain 2: ML Model Development
**Objective:** Recognize serverless MLflow as the 2025-26 default

A small team in 2026 wants experiment tracking with the absolute minimum operational overhead and the minimum cost — they don't want to provision anything or pay a per-hour tracking-server fee. What's the AWS-canonical answer?

- A. Self-host MLflow on EC2 to avoid AWS fees entirely.
- B. **Serverless MLflow on SageMaker AI** (GA Dec 2025) — no per-hour compute charge for the tracking layer; pay only for the S3 artifact store and actual training compute.
- C. Provisioned MLflow tracking server, Small size.
- D. SageMaker Experiments Classic — only $0/month tracking option pre-2025.

**Answer:** B
**Explanation:** As of **December 2025**, serverless MLflow on SageMaker is GA, and the tracking layer itself has **no compute charge**. Pre-Dec 2025 the provisioned Small server cost ~$460/month. The Pipelines integration also auto-creates a default MLflow App on demand if none exists.

---

## Q185 — Domain 2: ML Model Development
**Objective:** Recognize the EEOC four-fifths rule encoded as Disparate Impact

A lending model produces predictions across a protected facet (`race`). The post-training **Disparate Impact (DI)** value reported by Clarify is 0.72. Which statement is correct?

- A. DI = 0.72 means the model is unbiased; no-bias is at DI = 0.
- B. DI = 0.72 **violates the EEOC four-fifths rule** (the no-bias band is `[0.80, 1.25]`). The disadvantaged group's selection rate is 72% of the advantaged group's, below the 80% floor.
- C. DI > 0.5 is always acceptable for lending under ECOA.
- D. DI is undefined when one group has zero positive predictions.

**Answer:** B
**Explanation:** **DI is a ratio with no-bias value = 1.0**, NOT 0. The **EEOC four-fifths rule** (from the 1978 *Uniform Guidelines on Employee Selection Procedures*) says the disadvantaged group's selection rate must be at least 80% of the advantaged group's — i.e., **DI must lie in `[0.80, 1.25]`** (the symmetric upper bound is `1/0.8`; a "reverse" disparity can also be litigated). DI = 0.72 violates the rule. The same DI formula is referenced in ECOA fair-lending review, ADEA, and the NYC Local Law 144 "impact ratio" definition. A common exam trap: an answer choice claiming "DI = 0 is no bias" — wrong on its face, since DI = 0 means the disadvantaged group received zero positive outcomes (the worst possible bias). Memorize: **no-bias DI = 1.0**, legal threshold band = **[0.80, 1.25]**.

---

## Q186 — Domain 2: ML Model Development
**Objective:** Identify the four label-free post-training bias metrics

A production endpoint captures inputs and predictions via Model Monitor data capture, but ground-truth repayment labels arrive 90 days later. The compliance team wants a daily fairness alarm without waiting for labels. Which post-training Clarify metrics can the daily job compute against the data-capture log? (Select TWO)

- A. DPPL (Difference in Positive Proportions in Predicted Labels)
- B. DCAcc (Difference in Conditional Acceptance)
- C. DI (Disparate Impact)
- D. RD (Recall Difference)
- E. TE (Treatment Equality)

**Answer:** A, C
**Explanation:** Of the 13 post-training bias metrics, the **four label-free ones — DPPL, DI, FT, CDDPL** — can be computed on predicted labels alone. Every other metric (DCAcc, DCR, DAR, DRR, RD, SD, AD, TE, GE) needs ground truth (TP/FP/TN/FN per facet). Mnemonic: **"Predicted-only is DDFC"** (DPPL, DI, FT, CDDPL). DPPL is the workhorse of the Bias Drift Monitor specifically because of this — the Monitor's cron job can recompute it on yesterday's inference log without waiting for ground-truth backfill. DI plus its EEOC four-fifths rule and CDDPL (the Simpson's-paradox guard) are the two most-cited fairness metrics in real-world bank model-risk reviews; FT is rarer in production because nearest-neighbor search is expensive but is the only metric that approximates the counterfactual. Once labels arrive (here, after 90 days), the team can layer in DCAcc / DAR / RD / AD for the deeper calibration / precision / recall / accuracy view.

---

## Q187 — Domain 2: ML Model Development
**Objective:** Distinguish DCAcc vs DAR (calibration vs precision)

A model's "approve" predictions are computed across a facet. Per-facet ratio `(observed positives in facet) / (predicted positives in facet)` differs significantly between groups. Which Clarify metric measures this directly?

- A. DAR — precision difference: `precision_a - precision_d`.
- B. **DCAcc — `c_a - c_d` where `c_i = n_i(1) / n'_i(1)`** (observed vs predicted positives, i.e., calibration of acceptance rates).
- C. DRR — precision difference for rejections.
- D. RD — recall difference.

**Answer:** B
**Explanation:** **DCAcc** measures the calibration of acceptance rates conditional on facet. "Conditional" in the prompt is the discriminator. DAR is a different metric — precision (`TP / (TP + FP)`) compared across facets. Don't confuse them: DCAcc is "do my acceptances match observed positives?"; DAR is "are my positive predictions correct?"

---

## Q188 — Domain 2: ML Model Development
**Objective:** Recognize counterfactual fliptest (FT)

A bank's model risk officer wants to know whether two near-twin applicants — identical on every modeled feature except race — would receive different decisions. Which Clarify metric is the right tool?

- A. DAR — precision difference per facet.
- B. CDDPL — stratified DPPL by subgroup.
- C. **FT — Counterfactual Fliptest** — for each member of facet `d`, find the *k* nearest neighbors in facet `a`, compare predictions, count flips.
- D. RD — recall difference.

**Answer:** C
**Explanation:** **FT (Counterfactual Fliptest)** is the only Clarify metric that approximates the counterfactual "what if this person had been in the other facet?". It nearest-neighbor-matches across facets and counts prediction differences. The other metrics are marginal/summary statistics that can be confounded by genuine population-level feature differences.

---

## Q189 — Domain 2: ML Model Development
**Objective:** Pick the Clarify execution shell for per-request reason codes

A regulated lender must return a SHAP-based reason code with **every** loan-decision response under FCRA. Latency budget is 800 ms; the model itself runs in 50 ms. Which Clarify mode is the right architecture?

- A. Processing job (offline batch) on the data-capture log — explanations computed offline.
- B. **Online ExplainerConfig** on `EndpointConfig`: `ClarifyExplainerConfig` with `ShapBaseline`, returns SHAP attributions inline in the `InvokeEndpoint` response.
- C. Model Monitor `CreateModelExplainabilityJobDefinition` cron job.
- D. SageMaker FMEval batch evaluation.

**Answer:** B
**Explanation:** **FCRA requires the reason in the same response as the decision.** Online ExplainerConfig is the only mode that returns SHAP attributions inline with predictions. Offline batch is for pre-deployment reports; Model Monitor is for drift detection on captured logs; FMEval is for LLMs.

---

## Q190 — Domain 2: ML Model Development
**Objective:** Compute Online ExplainerConfig latency overhead

A team enables online Clarify SHAP with `NumberOfSamples=100` on an endpoint where the base model latency is 5 ms. The strict SLO is 200 ms p99. What does the latency math show, and what is the correct architectural recommendation?

- A. ~505 ms per request — blows the SLO 2.5×. Recommendation: don't use online SHAP; switch to **offline batch SHAP on the data-capture log**, or aggressively lower `NumberOfSamples` (e.g., 25) **and** add `EnableExplanations` JMESPath gating to skip the easy 90% of cases.
- B. ~205 ms — narrowly fits the SLO; ship as-is.
- C. ~5 ms — Clarify runs out-of-band and adds no latency.
- D. ~50 ms — Clarify caches SHAP values per prediction.

**Answer:** A
**Explanation:** Online Clarify adds **≈ `NumberOfSamples + 1` extra model invocations per request** (one real, N perturbed for Kernel SHAP). At `NumberOfSamples=100` and 5 ms base latency, that's `101 × 5 ms ≈ 505 ms` — well outside a 200 ms SLO. Mitigation knobs, in order of leverage: (1) **`EnableExplanations` JMESPath gating** — explain only the ~10% of requests near a decision boundary or with adverse outcomes (e.g., `prediction_score < 0.85`), the single highest-leverage knob; (2) **lower `NumberOfSamples`** — 25 may be acceptable for low-dimensional models with degraded precision; (3) move to async endpoints for batch decisioning where 500 ms latency is fine; (4) move the SHAP computation entirely offline, running on the data-capture log nightly. The exam loves this pattern: "5 ms model, 200 ms SLO, need SHAP on every request" — answer: cannot do online; use offline batch.

---

## Q191 — Domain 2: ML Model Development
**Objective:** Identify the SHAP baseline mis-configuration trap

A team enables Clarify offline SHAP and omits both `ShapBaseline` and `ShapBaselineUri` in `SHAPConfig`. The job completes successfully but SHAP attributions look unstable across runs and senior reviewers find them misleading. What happened?

- A. The data contained nulls; nulls are skipped silently by Clarify.
- B. **Clarify auto-generates a single-row baseline of column medians (numerical) and modes (categorical)**, which biases attributions toward median deviations and is the documented pitfall. Fix: pass an explicit baseline of 50–200 representative rows, stratified by the protected facet.
- C. The training-set shuffled seed differed across runs.
- D. Kernel SHAP is non-deterministic and cannot be stabilized.

**Answer:** B
**Explanation:** **Without an explicit baseline, Clarify silently uses median/mode** — the documented misconfiguration pitfall. The fix is to pass a representative sample of training data as the baseline. Kernel SHAP can be made deterministic via `Seed`. Nulls aren't the cause here.

---

## Q192 — Domain 2: ML Model Development
**Objective:** Identify how Clarify Online Explainability is enabled

A team wants to add SHAP explanations to a running production endpoint. Which approach is correct?

- A. Toggle a flag on the live endpoint with `UpdateEndpoint` and `EnableExplainability=true`.
- B. **Create a new `EndpointConfig` with `ExplainerConfig.ClarifyExplainerConfig`** (specifying `ShapBaselineConfig`, `NumberOfSamples`, optional `EnableExplanations` JMESPath), then `UpdateEndpoint` to roll the new config in.
- C. Attach an SNS topic to the endpoint and SHAP values appear automatically.
- D. Modify the inference container's `model_fn` to compute SHAP per request.

**Answer:** B
**Explanation:** **Online explainability is configured on `EndpointConfig`, not on the endpoint itself.** You can't toggle a flag in place. Create a new EndpointConfig with `ClarifyExplainerConfig`, then `UpdateEndpoint`. SNS is unrelated. Modifying `model_fn` would force you to re-implement SHAP yourself outside the Clarify framework.

---

## Q193 — Domain 2: ML Model Development
**Objective:** Distinguish FMEval from classical Clarify SHAP/bias

A team is comparing Llama-3-8B (JumpStart) against Claude (Bedrock) on a yes/no question-answering benchmark. Which AWS surface should they use?

- A. Classical Clarify post-training bias (DPPL, DI) with model artifacts.
- B. **SageMaker Clarify FMEval** (GA April 2024) — Question Answering task, BoolQ dataset, exact-match / F1 / quasi-exact-match metrics; works against JumpStart and Bedrock model runners.
- C. SageMaker Model Monitor data-quality baseline.
- D. SageMaker Debugger `Overfit` rule.

**Answer:** B
**Explanation:** **FMEval is for LLMs**, distinct from the SHAP/bias classical Clarify path. Four task types (open-ended generation, summarization, QA, classification), built-in datasets (BoolQ for QA yes/no, TriviaQA / NaturalQuestions for QA, TREX for factual knowledge, CrowS-Pairs for stereotyping, RealToxicityPrompts for toxicity), and pluggable ModelRunners that talk to Bedrock / SageMaker / JumpStart / etc.

---

## Q194 — Domain 2: ML Model Development
**Objective:** Map FMEval dimensions to built-in datasets

For each FMEval task and dimension, which dataset is the canonical built-in? (Select all that apply — three correct)

- A. Factual knowledge → TREX
- B. Adversarial toxicity → RealToxicityPrompts (challenging subset)
- C. Prompt stereotyping → CrowS-Pairs
- D. Code generation accuracy → HumanEval (FMEval built-in)
- E. Summarization quality → BoolQ

**Answer:** A, B, C
**Explanation:** **TREX** = factual knowledge (Wikipedia triplets). **RealToxicityPrompts** = adversarial toxicity, especially the challenging subset. **CrowS-Pairs** = prompt stereotyping (nine bias categories). HumanEval is not an FMEval built-in. BoolQ is for question answering (yes/no), not summarization (Gigaword / Government Report are summarization datasets).

---

## Q195 — Domain 2: ML Model Development
**Objective:** Map ClarifyCheckStep flags to use case

A pipeline runs after a Bias Drift Monitor flagged drift and the team retrained to fix it. They don't want the pipeline to fail on the very drift they're fixing, but they also want the baseline to update to the new "after fix" metrics so future runs compare against this new normal. Which `(skip_check, register_new_baseline)` combination applies?

- A. `(False, False)` — routine retrain, carry-over baseline, gate enabled.
- B. `(False, True)` — routine retrain with baseline refresh.
- C. `(True, False)` — post-violation retrain, skip the check.
- D. `(True, True)` — post-violation retrain, skip check, register new baseline as new normal.

**Answer:** D
**Explanation:** Four combinations: `(False, False)` is routine carry-over (most common). `(False, True)` is routine + baseline refresh (use sparingly — defeats drift detection if always on). `(True, False)` is post-violation skip-only. **`(True, True)`** is post-violation + accept the new model as the new normal and refresh the baseline accordingly.

---

## Q196 — Domain 2: ML Model Development
**Objective:** Recognize ClarifyCheckStep gating semantics

A pipeline's `ClarifyCheckStep` has `skip_check=True` and `fail_on_violation=True`. Which statement is correct?

- A. The check runs but the pipeline can't fail because `skip_check=True` overrides `fail_on_violation`.
- B. The pipeline does no drift comparison at all and cannot fail on drift — `skip_check=True` is "log only" / disabled mode.
- C. The check runs and the pipeline fails on any violation.
- D. The check runs and only warns; the pipeline never fails.

**Answer:** B
**Explanation:** **`skip_check=True` disables the comparison entirely**; the pipeline cannot fail on drift. `fail_on_violation` only matters when a check actually runs. Different from `(skip_check=False, fail_on_violation=False)` which runs the check in log-only mode. Memorize the difference — the exam tests this nuance directly.

---

## Q197 — Domain 2: ML Model Development
**Objective:** Pick the right Debugger rule for fp16 NaN explosion

A PyTorch training job using AMP (automatic mixed precision, fp16) starts producing NaN loss at step ~50 in early iterations. The job has been allocated 8× `ml.p4d.24xlarge` for 24 hours (~$6,300 if it runs to completion). Which Debugger rule + action combination is the right safety net?

- A. `Overfit` rule with `Email` action — notifies on-call.
- B. **`ExplodingTensor` rule with `StopTraining()` action** — fires on any NaN/Inf and stops the job programmatically in seconds, saving the bulk of the $6,300.
- C. `LowGPUUtilization` rule with `StopTraining()` — catches the fp16 issue.
- D. `WeightUpdateRatio` rule with `SMS` action.

**Answer:** B
**Explanation:** **`ExplodingTensor`** fires on NaN/Inf in any tensor — the canonical mixed-precision overflow trigger (set `only_nan=True` to restrict to NaN explicitly). Paired with `StopTraining()` it kills the job programmatically, in seconds, *before the human notification path fires*. The cost math is comically lopsided: rule side-car (typically `ml.t3.medium`) ≈ $0.05/hr; saved compute on the 8× p4d.24xlarge = ~$6,170 vs running to NaN-laden completion. **The maximum loss from leaving Debugger off is "you burn an entire doomed training job"; the maximum cost from leaving it on is ~$1/day for the side-car CPU instance.** `Overfit` is about val-vs-train divergence (also useful, pair with `StopTraining()` for free early stopping); `LowGPUUtilization` is a Profiler rule (catches under-utilization, not numeric explosion); `WeightUpdateRatio` is about Karpathy's "healthy training has update/weight ratio around 1e-3" heuristic, not NaN specifically.

---

## Q198 — Domain 2: ML Model Development
**Objective:** Recognize which Debugger rules are XGBoost-compatible

For an XGBoost training job, which built-in Debugger rules apply? (Select TWO)

- A. `VanishingGradient`
- B. `LossNotDecreasing`
- C. `DeadRelu`
- D. `Overfit`
- E. `SaturatedActivation`

**Answer:** B, D
**Explanation:** XGBoost-compatible rules are those that operate on losses / labels / predictions: **`LossNotDecreasing`, `Overfit`, `Overtraining`, `AllZero`, `StalledTrainingRule`**, plus XGBoost-specific `ClassImbalance`, `Confusion`, and `CreateXgboostReport`. **DL-only rules** (`VanishingGradient`, `ExplodingTensor`, `DeadRelu`, `SaturatedActivation`, `WeightUpdateRatio`, `PoorWeightInitialization`) require gradients/activations and don't apply to XGBoost.

---

## Q199 — Domain 2: ML Model Development
**Objective:** Manage the `save_interval` S3 cost trap

A team configures Debugger for a 7B-parameter LLM training run with `weights` and `gradients` collections at `save_interval=100` over 100,000 steps. After the run, their S3 bill spikes ~$260 just for Debugger tensor storage, and they realize this is a per-run cost. What is the right mitigation? (Select TWO)

- A. Raise `save_interval` (e.g., `weights` every 5000, `gradients` every 500).
- B. Use the `reduce_config` API to save reductions (mean / std / min / max) instead of full tensors.
- C. Switch instance types to reduce S3 traffic.
- D. Disable Debugger entirely by setting `s3_output_path=None` and run blind.
- E. Increase `MaxRuntimeInSeconds` to spread the cost.

**Answer:** A, B
**Explanation:** **S3 storage scales roughly with `1 / save_interval`** for tensor collections. The two right mitigations are **raising `save_interval`** and **using reductions** (which save 4 floats per tensor regardless of tensor size). S3 lifecycle rules to Glacier/delete are also valid. Instance type doesn't affect S3 cost. Disabling entirely loses convergence safety net. `MaxRuntime` is unrelated.

---

## Q200 — Domain 2: ML Model Development
**Objective:** Diagnose silent training stall

A 4-node `ml.p4d.24xlarge` distributed PyTorch job's trainer process crashes after 12 hours but the SageMaker job remains `InProgress` (the container's main PID is still alive but no progress is being made). The team would have eaten 12 more hours of compute (~$1,500) before noticing on Monday morning. Which Debugger rule + action would have caught this?

- A. `Overfit` with `StopTraining()`.
- B. **`StalledTrainingRule` with `StopTraining()`**, parameterized to fire after no new tensors are written for ~30 minutes.
- C. `DeadRelu` with `Email`.
- D. `MaxInitializationTime` (Profiler rule).

**Answer:** B
**Explanation:** **`StalledTrainingRule`** fires when no new tensor has been written for N seconds — the canonical "trainer crashed but SageMaker job kept billing" guard. Paired with `StopTraining()` it kills the job once stall is detected. `Overfit` is about val-vs-train divergence; `DeadRelu` is about ReLU activations going dead; `MaxInitializationTime` is about slow job startup.

---

## Q201 — Domain 2: ML Model Development
**Objective:** Recognize SageMaker Profiler replacing Debugger framework profiling

A team is upgrading from PyTorch 1.13 to PyTorch 2.1 and currently relies on `ProfilerConfig(framework_profile_params=FrameworkProfile(...))` (the Debugger-style framework profiling) for per-operator timing. What is the migration path?

- A. Nothing to change; Debugger framework profiling works on all PyTorch versions.
- B. **Migrate to standalone SageMaker Profiler (`smprof`).** Debugger framework profiling is deprecated for PyTorch ≥ 2.0 and TensorFlow ≥ 2.11. System monitoring inside Debugger still works on modern frameworks — only framework profiling moved out.
- C. Replace Debugger entirely with CloudWatch detailed monitoring.
- D. Disable mixed precision and stay on PyTorch 1.13.

**Answer:** B
**Explanation:** AWS explicitly deprecated Debugger framework profiling for **PyTorch ≥ 2.0 / TensorFlow ≥ 2.11** in favor of **standalone SageMaker Profiler** (`smprof`), GA December 2023. The deprecation notice reads: *"In favor of Amazon SageMaker Profiler, SageMaker AI Debugger deprecates the framework profiling feature starting from TensorFlow 2.11 and PyTorch 2.0."* The legacy `ProfilerConfig(framework_profile_params=FrameworkProfile(...))` config **silently stops producing useful data** on modern frameworks — it doesn't hard-error, which makes the bug subtle. System monitoring inside Debugger still works on modern frameworks; only the *framework* (per-operator) profiling layer moved out. The migration path: drop `FrameworkProfile` from `ProfilerConfig`, add SageMaker Profiler instrumentation in your `train.py` via `smprof` imports.

---

## Q202 — Domain 2: ML Model Development
**Objective:** Diagnose CPU bottleneck vs IO bottleneck on GPU instances

A PyTorch training job on `ml.p4d.24xlarge` shows persistent GPU utilization of ~12% while CPU is pegged at 95%. Which built-in Profiler rule is firing, and what's the canonical fix?

- A. **`CPUBottleneck` rule.** Fix: raise `DataLoader(num_workers=...)`, preprocess data offline (e.g., in a SageMaker Processing job), or use a **heterogeneous cluster** with a CPU-only instance group dedicated to preprocessing feeding the GPU group.
- B. `IOBottleneck` rule. Fix: switch to FSx for Lustre.
- C. `GPUMemoryIncrease`. Fix: smaller batch size.
- D. `MaxInitializationTime`. Fix: smaller container.

**Answer:** A
**Explanation:** **GPU underutilized while CPU pegged** = `CPUBottleneck`. Defaults: `cpu_threshold=90`, `gpu_threshold=10`. The advanced AWS-recommended fix is a **heterogeneous cluster** dedicating CPU instances to preprocessing. `IOBottleneck` is GPU underutilized + high I/O wait. `GPUMemoryIncrease` is gradual memory growth (often a tensor-accumulation bug). `MaxInitializationTime` is slow job startup.

---

## Q203 — Domain 2: ML Model Development
**Objective:** Distinguish IOBottleneck from CPUBottleneck

A PyTorch training job on `ml.p4d.24xlarge` shows GPU at ~12%, CPU at ~30%, and I/O wait at ~60%. Which Profiler rule fires and what is the right fix?

- A. `CPUBottleneck`. Fix: more CPU workers in the DataLoader.
- B. **`IOBottleneck`.** Fix: move from S3 File Mode to **FSx for Lustre** or **Fast File Mode**, shard the dataset (TFRecord / WebDataset), and add `prefetch_factor=4` to the DataLoader (or `tf.data.Dataset.prefetch(AUTOTUNE)` in TF).
- C. `LoadBalancing`. Fix: more shards.
- D. `BatchSize`. Fix: larger batch size.

**Answer:** B
**Explanation:** **GPU underutilized + high I/O wait** = `IOBottleneck`. Defaults: `io_threshold=50`, `gpu_threshold=70`. The fix is on the data-pipeline side: FSx Lustre / Fast File Mode, sharded formats, prefetching. CPU at 30% rules out CPUBottleneck. LoadBalancing is about worker imbalance; BatchSize is about under-utilizing all of CPU/GPU/memory.

---

## Q204 — Domain 2: ML Model Development
**Objective:** Recognize the 20-rule limit for Debugger

A platform team wants to attach 18 built-in Debugger rules plus 5 built-in Profiler rules to a training job. Is this configuration valid?

- A. No — total Debugger + Profiler rules cannot exceed 10 per job.
- B. Yes — Debugger and Profiler each have an independent **maximum of 20 rules per job**; 18 + 5 are both within limits.
- C. No — only one Debugger and one Profiler rule are allowed per job.
- D. No — Debugger rules cannot coexist with Profiler rules on the same training job.

**Answer:** B
**Explanation:** **Up to 20 built-in Debugger rules per job AND up to 20 built-in Profiler rules per job** (separate caps). 18 + 5 fits both budgets. If you need more, combine logic into a custom rule. They do coexist on the same training job by design.

---

## Q205 — Domain 2: ML Model Development
**Objective:** Bound the scope of Debugger vs Model Monitor vs Clarify

A junior engineer asks why you can't "just use Debugger to monitor the production endpoint." Which statement correctly bounds Debugger's scope? (Select TWO)

- A. Debugger captures tensors **during training**; Model Monitor watches the *deployed endpoint* — different services, different data planes.
- B. Debugger does not do explainability — that is **SageMaker Clarify**.
- C. Debugger replaces Model Monitor in 2026 — they merged into a single service.
- D. Debugger inspects S3 data quality before training — same data plane as Model Monitor.
- E. Debugger tracks experiments and hyperparameters — superset of MLflow.

**Answer:** A, B
**Explanation:** **Debugger watches a training job while it runs.** Model Monitor watches a deployed endpoint after training. Clarify does explainability + bias. MLflow / Experiments Classic tracks experiments. Debugger has none of those scopes. The cleanest one-sentence boundary: Debugger = while-it-runs convergence diagnostics; Model Monitor = production endpoint drift; Clarify = bias + SHAP.

---

# End of Q141–Q205

**Coverage map (cross-check against source chapters):**

- **Chapter 22 — Studio + Training Job Lifecycle:** Q141 (Domain immutability), Q142 (VpcOnly + CodeArtifact), Q143 (VPC endpoints / CloudWatch Logs), Q144 (`/opt/ml/model/` vs `/opt/ml/output/data/`), Q145 (`MaxWaitTime ≥ MaxRuntime`)
- **Chapter 23 — Built-in Algorithms:** Q147 (FM/recordIO-protobuf), Q148 (XGBoost CSV label-first/no-header), Q149 (RCF CPU-only), Q150 (DeepAR JSON Lines / Parquet), Q151 (Semantic Segmentation + OD-TF single-instance), Q152 (Seq2Seq deprecation), Q153 (NTM vs LDA), Q154 (k-NN vs K-Means), Q155 (IP Insights)
- **Chapter 24 — Script Mode:** Q146 (`if __name__ == '__main__':`), Q156 (`torch_distributed`), Q157 (SMDDP on EFA), Q158 (custom DLC extension for cold-start), Q159 (HuggingFace Estimator)
- **Chapter 25 — BYOC:** Q160 (BYOC `train` argv), Q161 (port 8080, /ping 2s, /invocations 60s, 8-min readiness), Q162 (Triton for multi-model GPU), Q163 (LMI/vLLM for LLMs not Triton), Q164 (ECR IMMUTABLE), Q165 (`docker buildx` multi-arch Graviton)
- **Chapter 26 — JumpStart:** Q166 (`accept_eula=True`), Q167 (post-fine-tune EULA), Q168 (Bedrock vs JumpStart), Q169 (Marketplace fee surprise)
- **Chapter 27 — Autopilot:** Q170 (V1 vs V2), Q171 (Ensembling vs HPO pools), Q172 (Auto fallback triggers), Q173 (`AutoMLStep` Ensembling-only), Q174 (auto-deploy cost), Q175 (objective metric for imbalance), Q176 (sample weights HPO-ignored), Q177 (Candidate notebook), Q178 (Canvas rebrand)
- **Chapter 28 — Experiments + MLflow:** Q179 (TrialComponent = Classic), Q180 (`experiment_config=`), Q181 (CloudTrail `Mlflow*`), Q182 (Stop vs Delete), Q183 (`sagemaker-mlflow:*` IAM), Q184 (serverless MLflow)
- **Chapter 29 — Clarify:** Q185 (DI four-fifths rule), Q186 (label-free DPPL+DI+FT+CDDPL), Q187 (DCAcc vs DAR), Q188 (FT counterfactual), Q189 (Online ExplainerConfig for FCRA), Q190 (latency math), Q191 (auto-baseline pitfall), Q192 (EndpointConfig not endpoint), Q193 (FMEval), Q194 (FMEval datasets), Q195 (ClarifyCheckStep flags), Q196 (`skip_check=True` semantics)
- **Chapter 30 — Debugger + Profiler:** Q197 (`ExplodingTensor` + StopTraining), Q198 (XGBoost-compatible rules), Q199 (`save_interval` S3 trap), Q200 (`StalledTrainingRule`), Q201 (Profiler replaces Debugger framework profiling for PT≥2.0), Q202 (CPUBottleneck + heterogeneous cluster), Q203 (IOBottleneck + FSx Lustre), Q204 (20-rule limit), Q205 (Debugger vs Model Monitor scope boundary)

**Multi-select count:** 5 (Q148, Q151, Q186, Q194, Q199, Q205 — 6 multi-select questions actually; target was 4–5).
## Q206 — Domain 2: ML Model Development
**Objective:** Select an AMT strategy for an iterative deep-learning fine-tune

A team is fine-tuning ResNet-50 for 60 epochs on `ml.g5.12xlarge`. The training script prints `val_top1: <num>` after every epoch. Budget is 80 trials with up to 10 concurrent jobs. Which combination is the most efficient choice?

- A. `strategy="Bayesian"`, `early_stopping_type="Auto"`, `max_parallel_jobs=10`
- B. `strategy="Random"`, `early_stopping_type="Off"`, `max_parallel_jobs=10`
- C. `strategy="Hyperband"`, `TrainingJobEarlyStoppingType="OFF"`, `max_parallel_jobs=10`
- D. `strategy="Grid"`, `early_stopping_type="Auto"`, `max_parallel_jobs=10`

**Answer:** C
**Explanation:** Per-epoch metrics make Hyperband the recommended strategy; AWS quotes 4.5–5× wall-clock speedups over Bayesian/Random on this exact workload class. Hyperband requires `TrainingJobEarlyStoppingType=OFF` because it owns its own multi-fidelity early stopping. Bayesian with `max_parallel=10` degrades to near-random. Grid is categorical-only.

---

## Q207 — Domain 2: ML Model Development
**Objective:** Recognize the Hyperband + early stopping incompatibility

A SageMaker tuning job is configured with `strategy="Hyperband"` and `TrainingJobEarlyStoppingType="AUTO"`. The CreateHyperParameterTuningJob API rejects the request. What is the correct fix?

- A. Switch the strategy to Bayesian so AUTO early stopping works
- B. Set `TrainingJobEarlyStoppingType="OFF"` — Hyperband uses its own internal early stopping
- C. Reduce `MaxParallelTrainingJobs` to 1
- D. Add a `HyperbandStrategyConfig` with `MinResource=1`

**Answer:** B
**Explanation:** AWS docs are explicit: *"The parameter TrainingJobEarlyStoppingType must be set to OFF when using the Hyperband internal early stopping feature."* The two stopping mechanisms conflict by design. Switching to Bayesian throws away the per-epoch advantage; parallelism and MinResource don't address the validation error.

---

## Q208 — Domain 2: ML Model Development
**Objective:** Choose ScalingType for a learning-rate-class hyperparameter

A tuner is configured with `learning_rate ∈ [1e-5, 1e-1]` using the default `ScalingType`. The team complains that AMT keeps picking values in the 0.01–0.1 range and never explores `1e-5` to `1e-3`. What is the minimal correct fix?

- A. Reduce `MaxNumberOfTrainingJobs` to force AMT to focus on smaller values
- B. Set `ScalingType="Logarithmic"` on the learning-rate parameter
- C. Switch from Bayesian to Random search
- D. Set `ScalingType="ReverseLogarithmic"` on the learning-rate parameter

**Answer:** B
**Explanation:** With linear sampling, 99% of samples land in `[0.001, 0.1]` because that's 99% of the range on a linear axis. `Logarithmic` gives each decade equal mass, making `3e-5` reachable. ReverseLogarithmic is for params near 1.0 (momentum). Strategy and trial count don't change the sampling distribution.

---

## Q209 — Domain 2: ML Model Development
**Objective:** Diagnose Bayesian convergence degradation under high parallelism

A Bayesian tuning job is configured with `max_jobs=50, max_parallel_jobs=50`. The team is unhappy with the best objective metric and blames the algorithm. What is the actual root cause and the right fix?

- A. The algorithm is stochastic — re-run with a different `RandomSeed`
- B. Bayesian degenerates to Random when `max_parallel ≈ max_jobs`; reduce `max_parallel_jobs` to 3–5 so the GP surrogate has time to learn between trials
- C. Switch to Grid search to guarantee coverage
- D. Add Auto early stopping to kill bad trials

**Answer:** B
**Explanation:** Bayesian relies on sequential surrogate updates; if 50 trials launch on the same surrogate snapshot, you get no learning. The canonical rule: as `MaxParallel` approaches `MaxNumberOfTrainingJobs`, Bayesian degenerates into Random. Production sweet spot is 3–5. RandomSeed, Grid, and Auto early stopping don't address the surrogate-staleness root cause.

---

## Q210 — Domain 2: ML Model Development
**Objective:** Compute the warm-start 500-job ceiling

A team has two completed parent tuning jobs that launched 250 and 250 child training jobs respectively. They want to warm-start a new tuning job with `IDENTICAL_DATA_AND_ALGORITHM` and `max_jobs=100`. What happens?

- A. The job succeeds and launches 100 new trials
- B. The job fails because 250 + 250 + 100 = 600 exceeds the 500-job ceiling for warm-started jobs
- C. The job succeeds but only launches 0 trials (the parents already exhausted the budget)
- D. The job succeeds but warm start is silently disabled

**Answer:** B
**Explanation:** Parent training jobs count against the new tuning job's 500-job hard cap for `IDENTICAL_DATA_AND_ALGORITHM` warm starts. 250 + 250 = 500 is already at the ceiling; adding 100 child trials pushes total to 600 and the API rejects. Fix: fewer child trials or fewer parents.

---

## Q211 — Domain 2: ML Model Development
**Objective:** Know warm-start restrictions

Which of the following ARE hard restrictions on a SageMaker AMT warm-start configuration? (Select TWO)

- A. Maximum 5 parent jobs
- B. Same objective metric across all parents and the new job
- C. Maximum 10 changes (tunable↔static flips plus static value changes)
- D. The new job must use the same `strategy` as the parents

**Answer:** A, B
**Explanation:** Warm start enforces: max 5 parents (A — valid), same objective metric (B — valid), same total hyperparameter count, same per-parameter type, ≤10 changes (C — valid), and not recursive. Strategy is NOT a warm-start restriction — you can warm-start a Bayesian child from Random parents, for example. The question lists three valid restrictions; A and B (the most fundamental two) are clearly correct.

---

## Q212 — Domain 2: ML Model Development
**Objective:** Identify the OverallBestTrainingJob field

A team is doing weekly retraining where each week's tuning job warm-starts from the previous week's. They want a single field to query that returns the best training job *across all parents plus the current child*. Which warm-start mode and which `DescribeHyperParameterTuningJob` response field do they need?

- A. `TRANSFER_LEARNING` mode; query `BestTrainingJob`
- B. `IDENTICAL_DATA_AND_ALGORITHM` mode; query `OverallBestTrainingJob`
- C. `TRANSFER_LEARNING` mode; query `OverallBestTrainingJob`
- D. `IDENTICAL_DATA_AND_ALGORITHM` mode; query `BestTrainingJob`

**Answer:** B
**Explanation:** The `OverallBestTrainingJob` field appears in `DescribeHyperParameterTuningJob` **only** when the warm-start type is `IDENTICAL_DATA_AND_ALGORITHM`. It tracks the best across all parent jobs plus the current job — exactly the unified leaderboard for chained weekly retrains. `BestTrainingJob` reports only the current job's best.

---

## Q213 — Domain 2: ML Model Development
**Objective:** Pick a strategy for a pure-categorical search space

A team wants to bake off 3 optimizers × 4 batch sizes × 2 schedulers = 24 combinations on a regulated model where the auditor requires "we tried every combination we said we would try." Which strategy is correct?

- A. Bayesian — converges fastest
- B. Hyperband — wall-clock wins
- C. Grid — categorical-only, exhaustive, audit-friendly
- D. Random — high parallelism

**Answer:** C
**Explanation:** Grid is categorical-only and exhaustively covers the Cartesian product (24 trials here, well under the 500 cap). For SR 11-7 style model-risk shops, the regulator-required guarantee of "every combination tested" only Grid provides. `MaxNumberOfTrainingJobs` is auto-computed. Bayesian/Hyperband may skip combos.

---

## Q214 — Domain 2: ML Model Development
**Objective:** Configure MetricDefinitions for AMT

A custom PyTorch script prints `Validation AUC: 0.913` after each epoch. The team's tuner config has `objective_metric_name="val_auc"` and `metric_definitions=[{"Name": "val_auc", "Regex": "Validation AUC: [0-9\\.]+"}]`. The tuning job completes 30 trials but `FinalObjectiveValue` is NaN for every trial. What is the bug?

- A. The script must use `logging.info` instead of `print`
- B. The regex has no capture group — the numeric value isn't being extracted
- C. The Name field must match the metric exactly with a colon (`val:auc`)
- D. AMT requires PyTorch to use the SageMaker Profiler to emit metrics

**Answer:** B
**Explanation:** SageMaker AMT extracts the **first capture group** of the regex as the metric float. `Validation AUC: [0-9\.]+` matches the line but captures nothing, so the value is ignored. Fix: `Validation AUC: ([0-9\.]+)` with parentheses around the number. Stdout via `print` is fine.

---

## Q215 — Domain 2: ML Model Development
**Objective:** Recognize Grid strategy quotas

A team configures a Grid strategy tuning job with 4 categorical parameters of sizes 6, 5, 5, and 5. They set `MaxNumberOfTrainingJobs=750` to match the AMT default. What happens?

- A. The job runs 750 trials, sampling combinations with replacement
- B. The job runs 750 trials, exhausting all 6×5×5×5=750 combinations
- C. The API rejects the request because Grid's `MaxNumberOfTrainingJobs` is auto-computed and must equal the product; it cannot exceed 500
- D. The job runs 600 trials (it caps at the Cartesian product size automatically)

**Answer:** C
**Explanation:** Two facts collide. (1) `MaxNumberOfTrainingJobs` is auto-computed for Grid — supplying a value that doesn't equal the Cartesian product is an error. (2) Grid has a hard cap of 500 combinations per tuning job. 6×5×5×5=750 exceeds the 500 cap, and the supplied 750 ≠ the auto product anyway. The team must split into multiple jobs or switch strategy.

---

## Q216 — Domain 2: ML Model Development
**Objective:** Apply Auto early stopping mechanics

Which best describes how `TrainingJobEarlyStoppingType="AUTO"` decides whether to kill a running trial?

- A. AMT compares the current metric to the absolute best-ever metric and kills any trial below 90% of it
- B. After each epoch, AMT computes the running average of the metric for previously completed trials at the same epoch, then takes the median of those averages; if the current trial is below that median, it is stopped
- C. AMT runs the Hyperband successive-halving algorithm internally
- D. AMT kills any trial that has failed to improve for 3 consecutive epochs

**Answer:** B
**Explanation:** Auto early stopping uses the "running median of running averages" comparison documented by AWS: per epoch, compare to median(running_avg(previous_completed_jobs_at_same_epoch)). It's a less aggressive cousin of Hyperband and is incompatible with Hyperband (whose own ASHA-based mechanism replaces it). 

---

## Q217 — Domain 2: ML Model Development
**Objective:** Identify the AMT cost-stack composition

A team's tuning bill is too high. Which TWO levers compose **multiplicatively** with the strategy choice and routinely cut total per-tuning-job cost by 5–10×? (Select TWO)

- A. Managed Spot Training on every child trial (`use_spot_instances=True` on the estimator)
- B. Auto early stopping (for Bayesian/Random/Grid) or Hyperband (which has its own early stopping)
- C. Switching the search space from continuous to categorical to enable Grid
- D. Using `TRANSFER_LEARNING` warm start instead of `IDENTICAL_DATA_AND_ALGORITHM`

**Answer:** A, B
**Explanation:** Spot composes orthogonally with every strategy and routinely cuts per-trial cost 70–90%. Early stopping (Auto or Hyperband) compounds by killing underperformers — AWS's case study shows 66% billable-minute reduction at the same metric. Both levers stack with strategy choice. C is a search-space contortion that usually hurts quality; D is a warm-start mode that doesn't directly cut cost.

---

## Q218 — Domain 2: ML Model Development
**Objective:** Choose between AMT, Optuna, and Ray Tune

A regulated insurance shop is migrating from Databricks-on-AWS to a SageMaker-native architecture. Models will train on SageMaker; the team wants every tuning run to land in CloudTrail with auditable model artifacts in the Model Registry. The lead data scientist prefers Optuna's TPE sampler. Which choice is most defensible?

- A. Keep Optuna — TPE is more accurate than Bayesian GP
- B. Switch to SageMaker AMT — zero-ops, IAM-scoped, CloudTrail-auditable, integrates with `TuningStep` in SageMaker Pipelines and the Model Registry
- C. Switch to Ray Tune for distributed scheduling
- D. Use Hugging Face Trainer's built-in HPO

**Answer:** B
**Explanation:** For an AWS-native regulated environment with SageMaker Pipelines, AMT wins on operational fit: native CloudTrail audit, IAM-scoped, billable to cost centers, no PostgreSQL/Ray cluster to operate, first-class `TuningStep`. The TPE vs GP difference is small relative to the operational/compliance gap. Ray Tune and HF HPO require additional ops you don't get for free.

---

## Q219 — Domain 2: ML Model Development
**Objective:** Pick a strategy for many short trials with massive parallel capacity

A team has account quota for 100 concurrent training jobs and wants to do an exploratory sweep over 10 hyperparameters on a fast tabular model where each trial takes 2 minutes. They want maximum wall-clock throughput. Which strategy?

- A. Bayesian with `max_parallel_jobs=100`
- B. Random with `max_parallel_jobs=100`
- C. Hyperband with `max_parallel_jobs=100`
- D. Grid with `max_parallel_jobs=100`

**Answer:** B
**Explanation:** Random has no surrogate to invalidate, so high parallelism gives linear speedup. Bayesian at `max_parallel=100` degenerates into Random while paying for the GP overhead. Hyperband needs per-epoch metrics, which a 2-minute trial likely doesn't emit usefully. Grid requires categorical-only. For high-dim, short, embarrassingly-parallel exploration, Random is the textbook answer.

---

## Q220 — Domain 2: ML Model Development
**Objective:** Recognize ScalingType for momentum-class parameters

A team's tuner has `momentum ∈ [0.9, 0.999]`. What is the correct `ScalingType` and why?

- A. `Linear` — small range, linear sampling is fine
- B. `Logarithmic` — momentum spans decades
- C. `ReverseLogarithmic` — momentum is close to 1.0, and the distance from 1 is what matters
- D. `Auto` — let AMT pick

**Answer:** C
**Explanation:** Momentum near 1.0 is the canonical use case for `ReverseLogarithmic`, which samples uniformly over `[log(1-Max), log(1-Min)]`. The interesting variation isn't `0.9 vs 0.95` linearly — it's the order-of-magnitude difference between `1−0.9 = 0.1` and `1−0.999 = 0.001`. Linear under-samples values closest to 1.

---

## Q221 — Domain 2: ML Model Development
**Objective:** Pick a parallelism setting for accuracy-first Bayesian

A team has a 60-trial Bayesian tuning budget on `ml.p3.2xlarge` ($3.83/hr) where each trial takes 1 hour. They want the best possible objective metric and are not in a hurry. Which `MaxParallel` setting?

- A. `MaxParallel=1` — surrogate updates after every trial, best metric quality
- B. `MaxParallel=10` — reasonable wall-clock
- C. `MaxParallel=30` — balance speed and quality
- D. `MaxParallel=60` — fastest wall-clock

**Answer:** A
**Explanation:** Pure Bayesian sweet spot is `MaxParallel=1` — the surrogate is refit after every completed trial, so every pick is maximally informed. Higher parallelism stales the surrogate. The question explicitly trades wall clock for accuracy, so 1 is the correct extreme. Production typically compromises at 3–5; pure quality says 1.

---

## Q222 — Domain 2: ML Model Development
**Objective:** Pick the AMT integration for SageMaker Pipelines

A team is wiring AMT into a SageMaker Pipeline that will register the best model into the Model Registry. Which approach is correct?

- A. Use a `ProcessingStep` to run Optuna inside the pipeline
- B. Use a `TuningStep` with a `HyperparameterTuner` instance; pass `tuning_step.get_top_model_s3_uri(top_k=0, ...)` to a downstream ModelStep
- C. Use a Lambda step to call `CreateHyperParameterTuningJob` directly
- D. Use `TrainingStep` with multiple parallel hyperparameter overrides

**Answer:** B
**Explanation:** `TuningStep` is the first-class SageMaker Pipelines wrapper for AMT (since 2021). It accepts a `HyperparameterTuner` and exposes `get_top_model_s3_uri(top_k=k, ...)` so downstream steps can register the top-N models. A Lambda or ProcessingStep wrapper would lose the Pipelines lineage and cache integration.

---

## Q223 — Domain 2: ML Model Development
**Objective:** Diagnose why SMDDP doesn't help on a single instance

A team observes that AllReduce dominates the timeline on a single `ml.p4d.24xlarge` (8 × A100 with NVLink). They propose enabling SMDDP to fix it. Why is this wrong?

- A. SMDDP requires EFA-equipped multi-node clusters; on a single node, NCCL drives intra-node NVLink fine and there's no inter-node fabric to optimize
- B. SMDDP doesn't support A100 hardware
- C. SMDDP is deprecated as of 2024
- D. SMDDP requires bf16 mixed precision

**Answer:** A
**Explanation:** SMDDP optimizes **inter-node** collectives over EFA on the AWS placement-group topology. A single `p4d.24xlarge` has no inter-node traffic — the 8 GPUs talk over NVLink, which NCCL handles optimally. The single-node fix is intra-node tuning (mixed precision, bigger micro-batch, profiler-guided kernel optimization), not SMDDP. This is one of AWS's favorite distractors.

---

## Q224 — Domain 2: ML Model Development
**Objective:** Map ZeRO stages to FSDP ShardingStrategy

Which mapping correctly pairs DeepSpeed ZeRO stages with their PyTorch FSDP `ShardingStrategy` equivalents?

- A. ZeRO-2 → `FULL_SHARD`; ZeRO-3 → `SHARD_GRAD_OP`
- B. ZeRO-2 → `SHARD_GRAD_OP`; ZeRO-3 → `FULL_SHARD`
- C. ZeRO-2 → `NO_SHARD`; ZeRO-3 → `HYBRID_SHARD`
- D. ZeRO-2 → `HYBRID_SHARD`; ZeRO-3 → `NO_SHARD`

**Answer:** B
**Explanation:** ZeRO-2 shards gradients + optimizer state → FSDP `SHARD_GRAD_OP`. ZeRO-3 shards params + gradients + optimizer state → FSDP `FULL_SHARD`. `NO_SHARD` is DDP-equivalent (a trap option); `HYBRID_SHARD` is `FULL_SHARD` intra-node + DP across nodes — typically the right multi-node SageMaker default but not a direct ZeRO mapping.

---

## Q225 — Domain 2: ML Model Development
**Objective:** Reject the FSDP NO_SHARD trap

A coworker proposes "let's enable FSDP with `NO_SHARD` to fix our OOM problem on a 30B model fine-tune." Why is this wrong?

- A. `NO_SHARD` is identical to DDP — full replication, no sharding, zero memory savings; the valid sharded options are `SHARD_GRAD_OP`, `FULL_SHARD`, or `HYBRID_SHARD`
- B. `NO_SHARD` only works on Trainium
- C. `NO_SHARD` is the default and they need to set it explicitly to a different value
- D. `NO_SHARD` requires bf16 mixed precision

**Answer:** A
**Explanation:** `NO_SHARD` is literally DDP under a confusing name — it replicates the full model state on every rank. It cannot fix an OOM caused by model state not fitting in HBM. For a 30B fine-tune the right answer is `FULL_SHARD` (max savings) or `HYBRID_SHARD` (multi-node fast intra-node + replicate across nodes). AWS likes putting `NO_SHARD` in distractor lists because the name *sounds* like it might mean "auto."

---

## Q226 — Domain 2: ML Model Development
**Objective:** Pick the right framework for a 70B + Tensor Parallelism workload

A team is fine-tuning a 70B model that requires tensor parallelism inside each node plus sharded data parallel across 8 nodes of `ml.p5.48xlarge`. They also want FP8 throughput on H100. Which AWS-native stack?

- A. Open-source PyTorch FSDP with NCCL backend
- B. DeepSpeed ZeRO-3 with CPU offload
- C. SageMaker SMP v2 with SDP + TP and NVIDIA Transformer Engine (FP8)
- D. SageMaker Training Compiler

**Answer:** C
**Explanation:** SMP v2 wraps an FSDP-ready model and adds TP, EP, CP, plus NVIDIA Transformer Engine for FP8 on Hopper GPUs (H100/H200) — roughly 2× throughput on the matmul-heavy path. Vanilla FSDP doesn't expose TP. DeepSpeed ZeRO-3 + CPU offload is for when total HBM is exhausted, not for FP8 on H100. Training Compiler is deprecated.

---

## Q227 — Domain 2: ML Model Development
**Objective:** Diagnose the g5 EFA cliff

A team trains a 30B Llama variant on 16 × `ml.g5.48xlarge` and AllReduce dominates. They've enabled SMDDP and tuned NCCL. Throughput is 5× worse than predicted. What's the bug?

- A. They need to switch from PyTorch to TensorFlow
- B. `ml.g5` has no EFA — inter-node traffic crawls; move to `ml.p4d` or `ml.p5`
- C. They should set `NCCL_ALGO=Tree`
- D. They need to use the deprecated SMDDP direct API

**Answer:** B
**Explanation:** The g5 family lacks EFA — inter-node bandwidth is ~100 Gbps ENA, roughly 30× worse than p4d's 400 Gbps EFA. No amount of SMDDP, FSDP, or NCCL tuning fixes a missing physical fabric. The fix is the instance family. SMDDP only optimizes collectives over EFA; it doesn't help where EFA doesn't exist.

---

## Q228 — Domain 2: ML Model Development
**Objective:** Recognize Training Compiler deprecation

A 2026 scenario asks "how do you speed up HuggingFace training on SageMaker without changing your script?" Which is the most current, forward-looking answer?

- A. SageMaker Training Compiler with `compiler_config=TrainingCompilerConfig()`
- B. `model = torch.compile(model)` inside the training script (Training Compiler is in maintenance / deprecated)
- C. Switch to TensorFlow
- D. Enable SageMaker Debugger

**Answer:** B
**Explanation:** AWS announced August 2024 there would be no new releases of SageMaker Training Compiler. `torch.compile()` in PyTorch 2.x covers ~90% of the same use cases natively — one-line wrap, no SageMaker-specific DLC, active upstream development. For Trainium, use the Neuron compiler. Training Compiler is the legacy-correct answer only for vintage 2023-era questions.

---

## Q229 — Domain 2: ML Model Development
**Objective:** Choose HyperPod or Training Jobs based on duration

For each pair below, which scenario should run on SageMaker HyperPod? (Select TWO)

- A. Fine-tuning a 7B Llama for 6 hours on 4 × `ml.p4d`
- B. Pre-training a 70B model for 36 days on 128 GPUs
- C. Dozens of short fine-tunes per day with different hyperparameters
- D. Pre-training a 405B MoE model for 90 days on 256 × `ml.p5.48xlarge`

**Answer:** B, D
**Explanation:** HyperPod's value (persistence + resiliency + checkpointless training + Slurm/EKS scheduling) only amortizes over multi-day/multi-week runs on large clusters where hardware failures become statistically inevitable. 6-hour fine-tunes and dozens of short ad-hoc jobs are ephemeral by nature — Training Jobs are the right answer for those.

---

## Q230 — Domain 2: ML Model Development
**Objective:** Recognize HyperPod checkpointless training benefits

HyperPod's December 2025 checkpointless training launch delivered which headline operational improvement at the 2,304-GPU H100 cluster scale?

- A. 50% reduction in per-token cost
- B. Recovery time reduced from 15–30 minutes (S3 checkpoint restore) to <2 minutes (peer-to-peer state replication), enabling >95% goodput
- C. Elimination of all checkpointing — no more S3 writes needed
- D. 4× faster training throughput

**Answer:** B
**Explanation:** Checkpointless training uses peer-to-peer state replication over EFA instead of S3 round-trips, cutting recovery from 15–30 min to <2 min (often <90s) at 2,304 GPUs — an 80–93% reduction. This drives goodput above 95% on clusters that historically struggled at 80%. S3 checkpointing is still retained for catastrophic full-cluster failures and final artifacts.

---

## Q231 — Domain 2: ML Model Development
**Objective:** Pick the HyperPod orchestrator

A research team wants `sbatch` and `srun` ergonomics on AWS for their 12-week RLHF campaign on a 64-GPU cluster. An enterprise platform team in a separate org wants Kubernetes-native scheduling with Kueue gang scheduling and shared training+inference workloads. Which orchestrator picks does each team get?

- A. Both teams: HyperPod with EKS
- B. Research team: HyperPod with Slurm; platform team: HyperPod with EKS
- C. Research team: HyperPod with EKS; platform team: HyperPod with Slurm
- D. Both teams: HyperPod with Slurm

**Answer:** B
**Explanation:** HyperPod offers two orchestrators on the same resilient cluster. Slurm fits research teams already comfortable with `srun`/`sbatch` lifecycle scripts. EKS fits enterprise platform teams wanting GitOps, IRSA, Kueue gang scheduling, and mixed training+inference. Choice is team preference + ecosystem, not capability.

---

## Q232 — Domain 2: ML Model Development
**Objective:** Recognize SMP v2 as PyTorch-only

A team using TensorFlow 2.x for distributed transformer training wants to migrate to SageMaker SMP v2 for FP8 throughput. What is the issue?

- A. SMP v2 is PyTorch-only; the team must port to PyTorch first
- B. SMP v2 doesn't support FP8
- C. SMP v2 requires Trainium hardware
- D. SMP v2 requires DeepSpeed

**Answer:** A
**Explanation:** SMP v2 (December 2023 rewrite) is PyTorch-only and wraps an FSDP-ready model with `torch.sagemaker.transform(model)`. SMP v1 supported TF/MXNet/PyTorch via AST rewriting but was abandoned. A TensorFlow shop wanting SMP v2 features must migrate to PyTorch.

---

## Q233 — Domain 2: ML Model Development
**Objective:** Distinguish SMDDP, SMP, FSDP

Which statement correctly distinguishes SMDDP, SMP v2, and FSDP?

- A. SMDDP and SMP v2 are alternatives; you must pick one
- B. SMDDP is a collective communication library (replaces NCCL); SMP v2 is a training framework that adds TP/EP/CP on top of FSDP; FSDP is the parallelism strategy. They compose: SMP v2 + FSDP + SMDDP backend
- C. FSDP is deprecated; use SMDDP or SMP v2 instead
- D. SMDDP is the same as SMP v2

**Answer:** B
**Explanation:** SMDDP is collective ops (AllReduce + AllGather over EFA, replaces NCCL). SMP v2 is a framework that wraps an FSDP-ready model and adds TP/EP/CP/FP8. FSDP is the sharding strategy. They compose — you can run FSDP via SMP v2 with SMDDP as the collective backend, all three layered.

---

## Q234 — Domain 2: ML Model Development
**Objective:** Pick the FSDP strategy for a multi-node cluster

A team is fine-tuning Llama-2-13B with LoRA on 4 × `ml.p4d.24xlarge` (32 × A100 40GB). DDP OOMs at batch size 1. Which sharding strategy is the BEST default for this multi-node config?

- A. `NO_SHARD` — DDP-equivalent
- B. `FULL_SHARD` across all 32 ranks — maximum memory savings
- C. `HYBRID_SHARD` — FULL_SHARD intra-node (NVLink) + replicate across nodes (EFA DP)
- D. `SHARD_GRAD_OP` — shard grads only

**Answer:** C
**Explanation:** `HYBRID_SHARD` is the canonical multi-node SageMaker default. Intra-node NVLink (~600 GB/s) handles the chatty AllGather; inter-node EFA carries only the gradient AllReduce per step. `FULL_SHARD` across all 32 ranks would do cross-node AllGather on every layer, which is slower. `NO_SHARD` doesn't solve the OOM. `SHARD_GRAD_OP` may not free enough memory for a 13B fine-tune.

---

## Q235 — Domain 2: ML Model Development
**Objective:** Diagnose the "1 worker stuck" pattern

A 64-rank DDP job on 8 × `ml.p5.48xlarge` shows one rank pinned at 100% GPU utilization while iteration count is frozen on that rank. Other ranks are progressing. Which diagnostic step is most likely to surface the root cause?

- A. Increase `NCCL_TIMEOUT` and hope it resolves
- B. Enable `NCCL_DEBUG=INFO` with `NCCL_DEBUG_SUBSYS=COLL`; look for the rank behind on iteration count — likely a data-loader stall, broken `IterableDataset`, or slow S3 shard load on that rank
- C. Switch to TensorFlow
- D. Disable EFA and use TCP

**Answer:** B
**Explanation:** The "stuck worker" pattern almost always points at data-loader skew or network asymmetry. NCCL_DEBUG with COLL subsystem reveals which collective each rank entered last; the lagging rank is the diagnostic. Timeout tweaks just delay the inevitable. Disabling EFA cripples bandwidth. TF won't help.

---

## Q236 — Domain 2: ML Model Development
**Objective:** Configure Managed Spot Training correctly

A team enables Managed Spot Training for a custom PyTorch fine-tune. They set `use_spot_instances=True`, `max_run=24*3600`, `max_wait=3600`. The CreateTrainingJob API rejects the request. What's wrong?

- A. Spot is incompatible with custom PyTorch — only built-ins are supported
- B. `MaxWaitTimeInSeconds (3600)` must be ≥ `MaxRuntimeInSeconds (86400)`
- C. Spot requires `instance_count=1`
- D. `CheckpointConfig.S3Uri` is missing

**Answer:** B
**Explanation:** Spot's `MaxWaitTimeInSeconds` is the outer envelope (compute + Spot queue waits) and must be ≥ `MaxRuntimeInSeconds`. Here `max_wait=3600 < max_run=86400`. AWS recommends `max_wait = 2 × max_run` (or 3–4× for scarce GPU types) to absorb retry latency. Custom PyTorch supports Spot fine.

---

## Q237 — Domain 2: ML Model Development
**Objective:** Compute Spot savings

A `DescribeTrainingJob` response reports `TrainingTimeInSeconds = 5000` and `BillableTimeInSeconds = 1500`. What is the Managed Spot savings percentage?

- A. 30%
- B. 50%
- C. 70%
- D. 90%

**Answer:** C
**Explanation:** The AWS formula is `(1 − BillableTimeInSeconds / TrainingTimeInSeconds) × 100 = (1 − 1500/5000) × 100 = 70%`. Both metrics are emitted to CloudWatch and visible in `DescribeTrainingJob`. The maximum savings ceiling is ~90%.

---

## Q238 — Domain 2: ML Model Development
**Objective:** Recognize Spot + Warm Pool incompatibility

A teammate proposes the following config for a 200-trial HPO sweep of 8-minute trials to stack Spot savings with Warm Pool latency wins:
```python
PyTorch(..., use_spot_instances=True, keep_alive_period_in_seconds=1800, max_wait=3600, max_run=600)
```
What happens?

- A. Both features compose; the job runs with both Spot pricing and warm-pool reuse
- B. The API rejects with a `ValidationException` — Managed Spot Training and Warm Pools are mutually exclusive
- C. Spot takes precedence; warm pool is silently ignored
- D. Warm pool takes precedence; Spot is silently ignored

**Answer:** B
**Explanation:** AWS docs are explicit: *"SageMaker AI managed warm pools cannot be used with spot instances."* A warm pool requires SageMaker to hold a specific instance for the next job; Spot's reclaim model contradicts that. Pick one. For 8-min trials, Spot's 70% discount on the 25-min trial duration dwarfs the 3-min cold-start saving — pick Spot.

---

## Q239 — Domain 2: ML Model Development
**Objective:** Identify the 60-minute MaxWaitTime cap

A nightly XGBoost retrain uses the built-in XGBoost algorithm (no script-mode checkpointing). The team enables Spot and sets `max_run=14400` (4h) and `max_wait=14400`. The API rejects with an error about `MaxWaitTimeInSeconds`. Why?

- A. `MaxWaitTime` for non-checkpointing built-ins and Marketplace algorithms is capped at 3600 seconds (60 minutes)
- B. XGBoost doesn't support Spot
- C. `max_wait` must be 2× `max_run`
- D. XGBoost requires `instance_count ≥ 2` for Spot

**Answer:** A
**Explanation:** AWS docs verbatim: *"SageMaker AI built-in algorithms and marketplace algorithms that do not checkpoint are currently limited to a MaxWaitTimeInSeconds of 3600 seconds."* Without checkpointing, every interrupt restarts from zero; long waits compound waste. Fix: switch to XGBoost in framework (script) mode with `xgb.callback.TrainingCheckPoint`, or use built-in XGBoost ≥0.90-1 which ships checkpointing.

---

## Q240 — Domain 2: ML Model Development
**Objective:** Apply atomic checkpointing on resume

A Spot training job resumed after an interrupt loaded the saved checkpoint but threw a `pickle.UnpicklingError`. What's the likely root cause and the fix?

- A. Non-atomic checkpoint write — the file was partially flushed when SIGTERM hit; use `os.replace()` from a staged `.tmp` file (atomic on POSIX)
- B. The checkpoint format is too new; downgrade PyTorch
- C. KMS key was rotated; re-encrypt the S3 prefix
- D. The training script must use `torch.jit.save` instead

**Answer:** A
**Explanation:** `torch.save()` is not atomic by default. If the process dies mid-flush, the file is truncated and unpicklable. Pattern: write to `.staging/.tmp`, fsync, then `os.replace(tmp, final)` — POSIX-atomic. Without this, the SageMaker checkpoint sidecar can mirror a partially-written file to S3.

---

## Q241 — Domain 2: ML Model Development
**Objective:** Identify full-state checkpoint contents

A resumed job's loss curve has a noticeable discontinuity that takes several hundred steps to smooth out. The team saved `model.state_dict()` only. What's the most likely cause? (Select TWO)

- A. The Adam optimizer first/second moments weren't saved — the optimizer re-learns its moments on resume
- B. The learning-rate scheduler state wasn't saved — LR restarts at base value
- C. CUDA was upgraded mid-run
- D. The data loader was using a different number of workers on resume

**Answer:** A, B
**Explanation:** Saving only `model.state_dict()` is the classic silent failure. Full state includes optimizer (Adam moments), scheduler, AMP `GradScaler`, and RNG states. Without these, resume is a "near-restart" that costs convergence. C and D would cause different symptoms (driver mismatch, throughput drift).

---

## Q242 — Domain 2: ML Model Development
**Objective:** Apply the no-RI-for-SageMaker rule

A finance team has $200K of unused EC2 Reserved Instance commitment on `m5.xlarge` expiring in 6 months. They want to apply the discount to SageMaker training jobs running on `ml.m5.xlarge`. Which is correct?

- A. The RI discount applies because `m5.xlarge` and `ml.m5.xlarge` are the same hardware
- B. EC2 Reserved Instances do NOT apply to SageMaker-managed instances; the only commitment-discount product for SageMaker is the SageMaker AI Savings Plan
- C. The team can file a support ticket to retroactively apply the RI
- D. RIs apply to SageMaker only for `ml.t3` family

**Answer:** B
**Explanation:** SageMaker runs on EC2 under the hood but bills a different SKU. EC2 RIs do not apply. The SageMaker commitment product is the SageMaker AI Savings Plan (up to 64% off, 1y or 3y, covers Studio + Training + Real-Time Inference + Batch Transform). On-Demand Capacity Reservations can guarantee capacity but provide no discount on their own.

---

## Q243 — Domain 2: ML Model Development
**Objective:** Configure Warm Pools for HPO

A team runs an HPO sweep of 50 trials, each 15 minutes, on the same instance config. Each cold start adds ~3 minutes. Which Warm Pool setting is most appropriate?

- A. `KeepAlivePeriodInSeconds=0` — disable warm pool
- B. `KeepAlivePeriodInSeconds=1200` — keep warm 20 min, longer than expected trial gap
- C. `KeepAlivePeriodInSeconds=3600` — maximum, just in case
- D. `KeepAlivePeriodInSeconds=86400` — 24 hours

**Answer:** B
**Explanation:** Per-job cap is `KeepAlivePeriodInSeconds ≤ 3600` (60 min). For HPO with ~15 min trials, setting it slightly longer than the trial gap (20 min here) is the sweet spot. The 3600 maximum is overkill and bills idle time if a follow-up doesn't arrive. 86400 exceeds the per-job cap entirely. Setting 0 wastes the ~3-min cold start every trial.

---

## Q244 — Domain 2: ML Model Development
**Objective:** Identify Warm Pool duration caps

Which TWO statements about SageMaker Managed Warm Pool durations are correct? (Select TWO)

- A. The per-job `KeepAlivePeriodInSeconds` is capped at 3600 seconds (60 minutes)
- B. The total chained warm-pool lifetime is capped at 28 days
- C. The persistent cache path is `/opt/ml/sagemaker/warmpoolcache`
- D. Warm pools provide a Spot-equivalent discount on the kept-warm idle time

**Answer:** A, B
**Explanation:** Per-job cap is 3600s; total chained reuse cap is 28 days for patching. C is true but not a *duration* fact. D is false — warm pools bill at full On-Demand rate during keep-alive (no Spot discount). The question asks specifically about durations.

---

## Q245 — Domain 2: ML Model Development
**Objective:** Compose SageMaker Savings Plan with Spot

A team has a SageMaker AI Savings Plan committing $10/hour for 1 year. Most production training runs on Managed Spot Training. What happens?

- A. The SP discount stacks on top of Spot — total savings ~70% + 35% = ~80%
- B. The SP does NOT stack with Spot — Spot pricing is already discounted; the SP covers On-Demand baseline. The mature pattern is SP for the always-on floor (Studio, real-time inference, baseline training), Spot for the burstable training ceiling
- C. Spot training jobs cannot be run when an SP is active
- D. The SP discounts only inference, not training

**Answer:** B
**Explanation:** SP and Spot don't stack — Spot already discounts the underlying training compute; SP doesn't further discount Spot usage. The correct compositional pattern: SP covers steady predictable spend (Studio domains, real-time endpoints, baseline batch jobs); Spot covers experimental/sweep training. Together they cover the whole SageMaker bill with the right discount per workload.

---

## Q246 — Domain 2: ML Model Development
**Objective:** Apply the AMT cost fan-out trap

A junior engineer copies a notebook configured with `MaxNumberOfTrainingJobs=1000` and `MaxNumberOfParallelTrainingJobs=50` on `ml.p4d.24xlarge` ($32/hr). Trials take ~3 hours each. What's the budget concern?

- A. Parallelism reduces total cost — total stays around $300
- B. `MaxNumberOfParallelTrainingJobs` trades wall-clock for peak burn rate; it does NOT reduce total cost. 1000 × 3h × $32 ≈ $96,000 regardless of parallelism. Always cap `MaxNumberOfTrainingJobs`
- C. AMT auto-caps cost at the account budget
- D. Spot kicks in automatically beyond 100 parallel jobs

**Answer:** B
**Explanation:** Three trials of 1 hour cost the same as one trial of 3 hours — parallelism is a wall-clock lever, not a cost lever. The total burn is `max_jobs × per_trial_cost`. The defensive pattern is to always cap `MaxNumberOfTrainingJobs`, set sensible `MaxParallel` (5 for Bayesian, higher for Hyperband), and use AMT-level `MaxRuntimeInSeconds` as a wallet.

---

## Q247 — Domain 2: ML Model Development
**Objective:** Recognize Compute Optimizer scope

A team wants to right-size their SageMaker training and inference instances using a managed AWS recommendation engine. Which tool is correct?

- A. AWS Compute Optimizer — it covers SageMaker
- B. Compute Optimizer does NOT cover SageMaker; use SageMaker **Inference Recommender** for endpoints and SageMaker Profiler + CloudWatch metrics for training right-sizing
- C. AWS Trusted Advisor's Compute Optimization check
- D. AWS Cost Anomaly Detection

**Answer:** B
**Explanation:** Compute Optimizer covers EC2, EBS, Lambda, ECS, and Auto Scaling Groups — NOT SageMaker. For SageMaker inference, Inference Recommender benchmarks instance/container/batching combos. For training, use Profiler hints + CloudWatch GPU utilization metrics. Anomaly Detection catches spikes but doesn't right-size.

---

## Q248 — Domain 2: ML Model Development
**Objective:** Apply Savings Plan scope

A team commits $20/hour to a Compute Savings Plan to cover their SageMaker training spend. Six months later, their SageMaker bill shows zero plan utilization. Why?

- A. Compute Savings Plans do NOT cover SageMaker; only SageMaker AI Savings Plans do. The team must purchase a SageMaker AI Savings Plan separately
- B. The team needs to activate the plan in the Billing console
- C. SP only applies to inference, not training
- D. SP only applies after 90 days of consumption

**Answer:** A
**Explanation:** This is the most-tested cost fact on MLA-C01. Compute Savings Plans cover EC2/Lambda/Fargate. SageMaker has its own SP product (up to 64% at 3y all-upfront), and the two are entirely separate. A $20/hr Compute SP applied to a SageMaker-only spend will sit idle, billing for the commitment with no offset on SageMaker.

---

## Q249 — Domain 2: ML Model Development
**Objective:** Migrate from Amazon Forecast

A new project in mid-2026 needs demand forecasting for 5000 SKUs over a 60-day horizon. The team's older study material says "use Amazon Forecast." What is the 2026 correct answer?

- A. Amazon Forecast — still the default
- B. Amazon Forecast is closed to new customers (July 29, 2024). Use SageMaker DeepAR (built-in algorithm) for engineering teams or SageMaker Canvas (no-code) for business analysts; Chronos foundation model for zero-shot
- C. Amazon Personalize
- D. CloudWatch Anomaly Detection

**Answer:** B
**Explanation:** Forecast was closed to new customers July 29, 2024. AWS recommends SageMaker DeepAR or Canvas as the migration target; the Chronos foundation model via JumpStart/Bedrock gives zero-shot forecasting for cold-start use cases. Personalize is recsys; CloudWatch Anomaly Detection is point-anomaly, not horizon-forecasting.

---

## Q250 — Domain 2: ML Model Development
**Objective:** Recognize the three Lookout retirements

In mid-2026, which of the following is NOT a discontinued AWS AI service? (Select the one still alive)

- A. Amazon Lookout for Equipment (discontinued October 10, 2025)
- B. Amazon Lookout for Metrics (discontinued October 10, 2025)
- C. Amazon Lookout for Vision (discontinued October 10, 2025)
- D. Amazon Comprehend Medical

**Answer:** D
**Explanation:** All three Lookout services were discontinued October 10, 2025 — their APIs stop responding and existing models are deleted. Comprehend Medical is in the safe core (still alive, HIPAA-eligible, with InferICD10CM / InferRxNorm / InferSNOMEDCT). Migration targets: SageMaker custom + IoT SiteWise (Equipment), OpenSearch/CloudWatch/RCF (Metrics), SageMaker CV or Rekognition Custom Labels (Vision).

---

## Q251 — Domain 2: ML Model Development
**Objective:** Identify HIPAA-eligible labeling paths

A hospital needs to label 50,000 medical images containing PHI. Which path is HIPAA-eligible? (Select TWO)

- A. SageMaker Ground Truth with a **private workforce** (under BAA)
- B. SageMaker Ground Truth Plus (AWS-managed labeling service)
- C. Amazon Mechanical Turk public workforce
- D. Augmented AI (A2I) with a private workforce for low-confidence review

**Answer:** A, D
**Explanation:** Plain Ground Truth (with private or vendor workforces under a BAA) is HIPAA-eligible. A2I is HIPAA-eligible but excludes Public and Vendor workforces. Ground Truth **Plus** is explicitly excluded from HIPAA scope. Mechanical Turk is the public workforce and is never eligible for PHI under any configuration.

---

## Q252 — Domain 2: ML Model Development
**Objective:** Recognize the four non-HIPAA-eligible AI services

Which AWS AI services are NOT HIPAA-eligible and therefore unsuitable for processing PHI? (Select TWO)

- A. Amazon Bedrock
- B. SageMaker Ground Truth Plus
- C. Amazon Fraud Detector
- D. Amazon Comprehend Medical

**Answer:** B, C
**Explanation:** Ground Truth Plus and Fraud Detector are both explicitly excluded from HIPAA eligibility (and Fraud Detector is also closed to new customers as of November 7, 2025). All three Lookout services are likewise excluded, and Mechanical Turk's public workforce is never eligible. Bedrock (including AgentCore) and Comprehend Medical are HIPAA-eligible.

---

## Q253 — Domain 2: ML Model Development
**Objective:** Choose between AI service, Bedrock, and SageMaker

A team needs to summarize 200 attorney-client emails per day into a 3-sentence brief each. Quality matters more than throughput. Which is the BEST 2026 answer?

- A. Comprehend Custom Classification
- B. Bedrock (Claude / Nova) with a few-shot summarization prompt and a Guardrail for PII anonymization
- C. SageMaker JumpStart with a fine-tuned T5 summarizer
- D. Amazon Kendra

**Answer:** B
**Explanation:** Summarization is a generative task — the rule-of-GenAI-equals-Bedrock applies. Few-shot prompting on Claude or Nova handles attorney-client tone without training data; a PII anonymize Guardrail keeps content safe. Comprehend doesn't do summarization. JumpStart + T5 is over-engineering for 200 emails/day. Kendra is search, not summarization.

---

## Q254 — Domain 2: ML Model Development
**Objective:** Identify Bedrock Converse API affordances

Which TWO statements about the Bedrock Converse API are correct? (Select TWO)

- A. Converse is a unified, model-agnostic chat API — same JSON shape across Claude, Nova, Llama, Mistral
- B. Converse supports image generation via `text-to-image` content blocks
- C. Converse exposes tool use, streaming (`ConverseStream`), prompt caching (`cachePoint`), and Guardrails (`guardrailConfig`)
- D. Converse is required for embedding model invocations

**Answer:** A, C
**Explanation:** Converse abstracts per-provider templating (you don't write Llama's `<|begin_of_text|>` tokens) and is the recommended path for chat-shaped workloads. It supports tool use, streaming, caching, Guardrails, multimodal content blocks (text/image/document/video). B is wrong — text-to-image and embeddings are NOT chat-shaped and require `InvokeModel`. Embeddings are also `InvokeModel`-only.

---

## Q255 — Domain 2: ML Model Development
**Objective:** Apply the Bedrock Provisioned Throughput mandate

A team fine-tunes Claude Haiku via Bedrock SFT for a ticket-classification workload that runs 200 requests/day. What's wrong with the architecture?

- A. SFT-produced custom Bedrock models can ONLY be served via Provisioned Throughput, with a minimum bill of ~$15K/month for one MU. At 200 requests/day, on-demand on the base model would be ~$5/month
- B. Bedrock SFT is not supported on Haiku
- C. Fine-tuning requires SageMaker, not Bedrock
- D. PT can serve on-demand, so the cost is fine

**Answer:** A
**Explanation:** Any model produced inside Bedrock (SFT, CPT, distillation, RFT) is **only** servable via Provisioned Throughput — the floor is roughly $15K/month per MU. For 200 req/day, that's indefensible. Alternatives: stay on base Haiku with few-shot prompting, use a Knowledge Base for retrieved examples, or only SFT if traffic is projected to grow to PT-justifying volume.

---

## Q256 — Domain 2: ML Model Development
**Objective:** Recognize Bedrock Batch pricing

A team wants to score 50M product descriptions overnight using Bedrock Claude Sonnet. Which mode optimizes cost?

- A. Bedrock on-demand with `Converse`
- B. Bedrock Provisioned Throughput
- C. Bedrock Batch inference — ~50% off on-demand pricing, asynchronous with a 24-hour SLA, results materialize to S3
- D. Bedrock Cross-Region Inference (Global profile)

**Answer:** C
**Explanation:** Batch inference is purpose-built for offline bulk scoring: 50% off on-demand, ~24h SLA, JSONL input + S3 output. PT is for steady high-volume real-time or required custom-model hosting. Global CRIS adds a small surcharge and routes anywhere worldwide (residency-risky). On-demand pays full price.

---

## Q257 — Domain 2: ML Model Development
**Objective:** Apply global CRIS data-residency caveat

A German subsidiary asks you to enable global cross-region inference (`global.anthropic.claude-...`) for their internal copilot to relieve regional throttling. Legal says BDSG forbids cross-border transfer of personal data. What's the correct response?

- A. Approve — Bedrock's global CRIS keeps data within the EU
- B. Reject global CRIS — it may route to any AWS region worldwide, breaching BDSG. Use the EU geographic CRIS profile (`eu.*`) for cross-region capacity within the EU; apply an SCP that denies `bedrock:InvokeModel*` when `aws:RequestedRegion: unspecified` (the global-CRIS placeholder)
- C. Approve but enable KMS encryption
- D. Switch to Provisioned Throughput

**Answer:** B
**Explanation:** Geographic CRIS (`us.*`, `eu.*`, `apac.*`) respects continent-level residency; global CRIS does not. For GDPR/BDSG/APP/sovereign-data workloads, only geographic CRIS or single-region is safe. The SCP pattern denies the global-CRIS placeholder. KMS doesn't fix residency. PT is regional but doesn't address the capacity issue cleanly.

---

## Q258 — Domain 2: ML Model Development
**Objective:** Pick a Bedrock Knowledge Base vector store for cost

A startup needs the cheapest possible RAG vector store for 5M PDFs queried at low volume (~1000 queries/day). Which 2026 vector store is the right pick?

- A. Amazon OpenSearch Serverless — fastest setup
- B. Amazon S3 Vectors (GA December 2025) — lowest cost for low-QPS RAG; native S3 pricing
- C. Pinecone — established vendor
- D. Redis Enterprise Cloud — sub-ms latency

**Answer:** B
**Explanation:** S3 Vectors (Dec 2025 GA) is positioned as up to 90% cheaper than OpenSearch Serverless for low-volume workloads because OpenSearch's 2-OCU floor (~$350+/mo) runs 24/7 regardless of queries; S3 Vectors charges per request. Trade-off: ~100ms warm latency vs sub-100ms OS. Pinecone and Redis Enterprise are premium offerings.

---

## Q259 — Domain 2: ML Model Development
**Objective:** Apply hybrid search benefits

A RAG chatbot keeps missing exact policy codes like `PPO-Gold-2026` even though retrieval similarity scores look high. Pure vector search returns plausible but wrong chunks. What's the most effective fix?

- A. Increase the embedding dimension from 256 to 1024
- B. Enable hybrid search (BM25 keyword + vector + RRF fusion) in the Bedrock Knowledge Base; typical +5-15% NDCG@10 lift, with the largest gains on corpora containing rare entities (codes, SKUs, identifiers)
- C. Switch from Titan Embed v2 to Cohere Embed v3
- D. Add more chunks to the prompt (top-20 instead of top-5)

**Answer:** B
**Explanation:** Exact-match queries (codes, SKUs, error IDs, brand names) are the canonical failure mode of pure dense retrieval — embedding models normalize away small token differences. BM25 catches these because it weights rare tokens; RRF fuses ranks robustly without score calibration. Bedrock KB exposes this as "hybrid" search type. The +5-15% NDCG lift is well-published.

---

## Q260 — Domain 2: ML Model Development
**Objective:** Pick Bedrock Guardrails for hallucination

A regulated insurance RAG chatbot is producing answers not actually supported by the retrieved documents. Which Bedrock Guardrails policy directly addresses this?

- A. Content filters (toxic content)
- B. Denied topics
- C. Contextual grounding check — sets a grounding score threshold; below threshold blocks or surfaces
- D. Word filters

**Answer:** C
**Explanation:** Contextual grounding is one of Bedrock Guardrails' seven policies, specifically designed to catch hallucination by scoring the response's grounding in the provided source AND its relevance to the query. Below the configured threshold, the response is blocked or surfaced. Content filters catch hate/insults/violence; denied topics block subject areas; word filters block exact phrases.

---

## Q261 — Domain 2: ML Model Development
**Objective:** Identify the seven Guardrails policies

Which of the following IS a Bedrock Guardrails policy type? (Select TWO)

- A. Automated Reasoning checks (formal-logic verification against a customer-defined policy)
- B. Prompt-attack filter (jailbreak / prompt injection / prompt leakage detection)
- C. KMS encryption enforcement
- D. SCP-style region restriction

**Answer:** A, B
**Explanation:** The seven Guardrails policies are: content filters (with prompt-attack sub-category), denied topics, word filters, sensitive information (PII) filters, contextual grounding, and Automated Reasoning checks. KMS and SCPs are AWS account-level controls, not Guardrails policies.

---

## Q262 — Domain 2: ML Model Development
**Objective:** Apply standalone ApplyGuardrail to non-Bedrock models

A team has a self-hosted Llama 3 on a SageMaker endpoint and needs to apply Bedrock-style content filtering to its outputs before returning them to users. Which API call works?

- A. `Converse` with `guardrailConfig` — requires the generation to come from a Bedrock model
- B. `ApplyGuardrail` standalone — policies the input/output of any text or image content without a Bedrock model call attached
- C. SageMaker Model Monitor
- D. Comprehend `DetectToxicContent`

**Answer:** B
**Explanation:** `ApplyGuardrail` is the cross-LLM safety primitive — it invokes a Guardrail on arbitrary text or images with `source: INPUT | OUTPUT` and no model call attached. The standard `Converse` integration requires a Bedrock generation. Comprehend toxic content works only on a narrow taxonomy; Guardrails is broader (seven policies) and supports custom denied topics and PII rules.

---

## Q263 — Domain 2: ML Model Development
**Objective:** Recognize Application Inference Profiles for cost attribution

A multi-tenant SaaS hosts Bedrock workloads for five product teams in one AWS account. The bill is a single $40K/month Bedrock line item with no per-team breakdown. How do you fix the attribution?

- A. Use AWS Cost Categories alone
- B. Create one Application Inference Profile (AIP) per team, attach cost-allocation tags, and have each app use its AIP ARN as `modelId` in Converse/InvokeModel; Cost Explorer then surfaces per-AIP usage
- C. Use CloudWatch metric filters
- D. Switch each team to a separate AWS account

**Answer:** B
**Explanation:** AIPs are user-created inference profiles that wrap one or more underlying models or system-defined CRIS profiles. Tagging them with cost-allocation tags (`team=x`, `env=prod`) gives per-AIP billing line items. AIPs also enable per-AIP CloudWatch metrics for rate-limiting and IAM-principal attribution. They do NOT change unit pricing — they're an observability/attribution layer.

---

## Q264 — Domain 2: ML Model Development
**Objective:** Recognize AgentCore vs Bedrock Agents

A team is building a long-running customer-success agent that needs (a) up to 8-hour execution windows, (b) session isolation per tenant in a multi-tenant SaaS, (c) integration with LangGraph, and (d) external MCP tool servers. Which is correct?

- A. Bedrock Agents (classic) — fastest path
- B. Amazon Bedrock AgentCore — framework-agnostic runtime with 8-hour windows, session isolation, MCP integration, A2A protocol, and managed Memory/Gateway/Identity/Observability
- C. Amazon Lex V2
- D. SageMaker custom inference

**Answer:** B
**Explanation:** AgentCore (GA October 2025, multi-region April 2026) is the production runtime for non-trivial agents. It supports LangGraph, CrewAI, Strands, custom code, MCP tools, A2A protocols, and 8-hour sessions. Classic Bedrock Agents is request-response with ~15-minute caps and pinned prompt templates — fine for a prototype, insufficient for this scenario.

---

## Q265 — Domain 2: ML Model Development
**Objective:** Pick the customization path for the model

A health insurance carrier has 50K labeled `(question, ideal_answer)` pairs from past customer service transcripts. They want the model to learn their brand voice. The team has no MLOps headcount. Which path?

- A. RAG with Bedrock Knowledge Bases
- B. Continued pre-training on unlabeled benefits PDFs
- C. Bedrock SFT (supervised fine-tuning) on Nova or Llama (and budget for Provisioned Throughput to serve the resulting custom model)
- D. Reinforcement Fine-Tuning (RFT) on Nova 2 Lite

**Answer:** C
**Explanation:** Labeled (prompt, completion) pairs targeting brand voice is the textbook SFT use case. Bedrock SFT covers Nova, Llama 3.x, Titan, Cohere Command. The team must budget for PT to host the resulting custom model. RFT requires a reward function, not labeled pairs. CPT is for unlabeled domain text. RAG handles freshness/citations but not voice.

---

## Q266 — Domain 2: ML Model Development
**Objective:** Recognize Bedrock RFT and Nova 2 Lite

In December 2025 at re:Invent, AWS launched Reinforcement Fine-Tuning (RFT) on Bedrock. Which model was the launch model, and what use case does RFT target?

- A. Nova Premier; chat tone customization
- B. Amazon Nova 2 Lite; verifiable objectives (math, code correctness, structured-output schema compliance) using a reward function (LLM-as-judge or deterministic grader). AWS reports up to ~66% accuracy gains on math benchmarks
- C. Claude Sonnet 4; long-context reasoning
- D. Llama 3.3 70B; multilingual

**Answer:** B
**Explanation:** Nova 2 Lite was the RFT launch model at re:Invent 2025 (expanded February 2026 to gpt-oss-20B and Qwen 3 32B). RFT replaces labeled pairs with a reward function — RLVR (deterministic graders) for math/code, RLAIF (LLM judge) for subjective tasks. The reported gains are large enough that workloads previously requiring custom PPO pipelines on SageMaker now stay on Bedrock.

---

## Q267 — Domain 2: ML Model Development
**Objective:** Pick Bedrock vs JumpStart for low traffic

A small startup needs an LLM chat feature in their app shipping next week. Traffic is unknown but expected to be bursty at low volumes (<1M tokens/day for the first quarter). The team has no ML engineers. Which choice?

- A. Bedrock on-demand — variable bill, no infrastructure, ship in hours
- B. JumpStart with Llama 3.1 8B on `ml.g5.2xlarge` — saves money
- C. Bedrock Provisioned Throughput — guaranteed capacity
- D. Self-hosted Llama on EC2

**Answer:** A
**Explanation:** At <1M tokens/day with bursty traffic, Bedrock on-demand wins by 10–60× over JumpStart because JumpStart real-time has a 24×7 instance floor (~$1,110/mo on g5.2xlarge for one replica, billed even at zero traffic). PT is overkill for unproven workloads. Bedrock has zero infra ops — perfect for "ship next week" with no ML team.

---

## Q268 — Domain 2: ML Model Development
**Objective:** Pick Bedrock vs JumpStart for steady high volume

A SaaS company has 50 enterprise tenants each with their own fine-tuned Llama 70B LoRA adapter. Combined traffic is ~120M tokens/day steady. They have an ML platform team. Which architecture wins?

- A. 50 separate Bedrock Custom Model Import deployments
- B. 50 separate JumpStart endpoints, one per tenant
- C. One JumpStart `ml.p4d.24xlarge` (or similar) multi-LoRA endpoint using LMI v15 / vLLM, hosting one Llama 70B base model with all 50 LoRA adapters dynamically routed per request
- D. Bedrock on-demand with Nova Pro

**Answer:** C
**Explanation:** Multi-LoRA serving on JumpStart's LMI v15 / vLLM (Feb 2026 collaboration) is the canonical 2026 multi-tenant SaaS pattern: one base model + 50 adapters on one node beats 50 endpoints by ~60× ($23K/mo vs $1.5M/mo). Bedrock has no per-request adapter routing for customer-uploaded LoRAs. Custom Model Import would charge per imported model. Nova Pro can't host customer fine-tunes.

---

## Q269 — Domain 2: ML Model Development
**Objective:** Identify the 2026 muddy zone and inflection point

What is the conventional 2026 wisdom for the Bedrock-vs-JumpStart cost crossover?

- A. JumpStart is always cheaper than Bedrock
- B. Below ~10K req/day Bedrock on-demand wins decisively; ~10K–50K req/day is a muddy zone decided by burstiness and model; past ~220M tokens/day (~6.6B/month), JumpStart's fixed-instance cost beats Bedrock's per-token cost when the same model can be hosted on both
- C. Bedrock is always cheaper than JumpStart
- D. The crossover is fixed at $5,000/month

**Answer:** B
**Explanation:** The two best-known 2026 numbers: (1) the muddy zone of 10K–50K req/day where burstiness decides, and (2) the ~220M tokens/day inflection past which JumpStart's instance-hour amortization wins. The Claude Sonnet @ 40M tokens/day ($12K/mo) vs Llama 70B on 2× g5.2xlarge ($2.2K/mo) ~81% gap is the canonical migration trigger story.

---

## Q270 — Domain 2: ML Model Development
**Objective:** Recognize the 2026 hybrid default

A financial services company is designing a serious production RAG application requiring: (a) 500K queries/day, (b) PII redaction before any text leaves their VPC, (c) Claude Sonnet 4 required for final generation, (d) a custom reranker already fine-tuned on their domain. What is the 2026 modal architecture?

- A. All Bedrock — every step uses Bedrock APIs
- B. All JumpStart — host every step on SageMaker endpoints inside the VPC
- C. Hybrid: JumpStart endpoints for PII redaction (BERT-NER) and the custom reranker (BGE-Reranker); Bedrock Knowledge Bases for retrieval; Bedrock Claude Sonnet 4 for generation; Bedrock Guardrails for PII anonymize + contextual grounding on the output
- D. Amazon Q Business

**Answer:** C
**Explanation:** The modal 2026 enterprise architecture is **Bedrock for generation + JumpStart for the cheap high-volume small models (rerank, embed, PII)**. Generation is hard and expensive to self-host at variable scale; small steady models (1B-parameter rerankers, NER) are cheap on dedicated GPU and over-pay on per-token Bedrock pricing. Claude is Bedrock-exclusive. Custom reranker must run on JumpStart since it's not in Bedrock. PII redaction in VPC is JumpStart territory. Pure Bedrock can't host the custom reranker; pure JumpStart can't access Claude.

---

---

# Domain 3 — Deployment and Orchestration of ML Workflows (22%)

# MLA-C01 Practice Questions — Domain 3 Part A (Q271–Q325)

> **Scope:** Domain 3 — Deployment and Orchestration of ML Workflows, Part A
> **Source:** Part G chapters 35–42 (endpoint types, real-time/serverless/async/batch, MME/MCE, autoscaling, deployment strategies, inference optimization, inference outside SageMaker)
> **Question range:** Q271 – Q325 (55 questions)
> **Format:** Single-answer A–D unless prefixed with "(Select TWO)" or "(Select THREE)". Multi-select answers are returned as comma-separated letters.

---

## Q271 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Match an inference workload to the correct SageMaker endpoint type

A retail company needs to score a 600 MB nightly batch of customer records (~10M rows) with no latency requirement. The model is only used for this nightly job and is otherwise idle. Which SageMaker option is the most cost-effective?

- A. SageMaker Real-time endpoint with auto-scaling minimum capacity = 0
- B. SageMaker Serverless Inference endpoint with MaxConcurrency = 200
- C. SageMaker Batch Transform job triggered nightly by EventBridge
- D. SageMaker Asynchronous Inference endpoint invoked from Lambda

**Answer:** C

**Explanation:** Batch Transform is the only option designed for offline batch scoring of large datasets — it spins up instances, scores, writes results to S3, and shuts down (pay-per-job). Real-time endpoints (even with min-capacity tricks) bill per-instance-hour. Serverless caps at 4 MB payload and is poorly suited to bulk records. Async is meant for large *individual* payloads from interactive clients, not offline batch.

---

## Q272 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Memorize endpoint payload limits

What is the maximum single-invocation payload size for each SageMaker endpoint type?

- A. Real-time 6 MB, Serverless 6 MB, Async 1 GB, Batch unlimited
- B. Real-time 6 MB, Serverless 4 MB, Async 1 GB, Batch unlimited
- C. Real-time 4 MB, Serverless 6 MB, Async 100 MB, Batch unlimited
- D. Real-time 1 GB, Serverless 4 MB, Async 6 MB, Batch unlimited

**Answer:** B

**Explanation:** These four payload limits are the single most-tested fact in Domain 3. Real-time = 6 MB, Serverless = **4 MB** (smaller than real-time), Async = 1 GB (largest single payload), Batch Transform = unlimited (it reads from S3, not the request body).

---

## Q273 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Identify cold-start and scale-to-zero behavior across endpoint types

Which two SageMaker endpoint types support **scale-to-zero** for cost savings during idle periods? (Select TWO)

- A. Real-time endpoint (classic ProductionVariant, no Inference Components)
- B. Serverless Inference
- C. Asynchronous Inference
- D. Batch Transform
- E. Multi-Model Endpoint (MME) on real-time hosting

**Answer:** B,C

**Explanation:** Serverless inference scales to zero by definition (idle = $0). Async inference supports scale-to-zero when configured with application auto-scaling on the `ApproximateBacklogSizePerInstance` metric. Classic real-time endpoints bill per-instance-hour even at zero traffic (Inference Components in 2024 added scale-to-zero, but the question stipulates classic ProductionVariant). Batch Transform is job-based — there's nothing to "scale to zero" because it doesn't persist.

---

## Q274 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Choose endpoint type for sporadic, spiky traffic

A team has a model that receives 0–50 requests per hour with unpredictable spikes, never more than a few KB per request, and tolerates a few seconds of cold-start latency. They want to minimize cost. Which option fits best?

- A. Real-time `ml.g5.xlarge` endpoint with auto-scaling 1–4 instances
- B. Serverless Inference with MemorySize=2048 MB and MaxConcurrency=20
- C. Async Inference with min capacity = 0
- D. Batch Transform invoked every minute

**Answer:** B

**Explanation:** Serverless is purpose-built for sporadic and spiky workloads where idle cost matters more than steady-state latency. Real-time always bills per-hour. Async is overkill for KB-sized payloads. Batch Transform every minute is an anti-pattern (job-startup overhead).

---

## Q275 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Real-time endpoint A/B traffic shifting

A team has deployed two ProductionVariants behind one real-time endpoint: `VariantA` (current model) with `InitialVariantWeight=99` and `VariantB` (new model) with `InitialVariantWeight=1`. Roughly what fraction of traffic does `VariantB` receive?

- A. 1% of traffic, because weights are normalized
- B. 99% of traffic — InitialVariantWeight is inverted
- C. 0% — the variant must be explicitly enabled with `UpdateEndpointWeightsAndCapacities`
- D. 100% — newer variants always receive all traffic

**Answer:** A

**Explanation:** `InitialVariantWeight` is a relative weight; SageMaker normalizes across all variants. With 99 vs 1, VariantB receives 1/(99+1) = 1% of requests. This is the canonical canary ramp pattern (95/5 → 50/50 → 0/100).

---

## Q276 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Distinguish Shadow Variants from A/B testing

A team wants to validate a new model in production with **zero customer impact** — they want the new model to see real traffic but its responses must never reach end users. Which feature should they use?

- A. ProductionVariant with `InitialVariantWeight=0.01` so only 1% of users see it
- B. Shadow Variants — mirror traffic to a second variant whose response is discarded
- C. A canary deployment with `CanarySize=10%`
- D. A blue/green deployment with `TerminationWaitInSeconds=0`

**Answer:** B

**Explanation:** Shadow Variants (GA 2022) mirror live traffic to a shadow model whose response is discarded — no client ever sees the shadow output, but you can compare latency and predictions in CloudWatch. A canary with 1% weight still serves 1% of *real users* the new model. Blue/green and canary deployments are about cutover, not zero-impact shadow testing.

---

## Q277 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Inference Components and per-model scaling

What problem do **Inference Components** (GA 2024) solve that classic ProductionVariants cannot?

- A. They allow real-time endpoints to support payloads larger than 6 MB
- B. They enable per-model independent scaling (and scale-to-zero) on a single shared endpoint, so multiple models can share GPU hardware
- C. They are the only way to enable HTTPS on a SageMaker endpoint
- D. They replace SageMaker Pipelines for orchestration

**Answer:** B

**Explanation:** Inference Components (ICs) decouple model scaling from endpoint scaling — each IC has its own `DesiredCopyCount` and scales independently on a shared instance fleet. This is what enabled Salesforce's reported ~8× cost reduction (packing many models per GPU, each scaling on its own metric). Payload limits are unchanged, HTTPS is automatic, and ICs are not an orchestration product.

---

## Q278 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Auto-scaling target metric for real-time endpoints

Which CloudWatch metric is the **default and recommended** target for application auto-scaling of a real-time SageMaker endpoint?

- A. `CPUUtilization`
- B. `MemoryUtilization`
- C. `SageMakerVariantInvocationsPerInstance`
- D. `ModelLatency`

**Answer:** C

**Explanation:** `SageMakerVariantInvocationsPerInstance` is the canonical, SageMaker-published target-tracking metric — `TargetValue = MAX_RPS × SAFETY_FACTOR × 60`. CPU/Memory are EC2-level and don't correlate with inference load reliably (a GPU model can saturate at low CPU). `ModelLatency` is a signal, not a scaling driver — it lags load.

---

## Q279 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Serverless inference exclusions

Which feature is NOT supported on a Serverless Inference endpoint?

- A. CloudWatch metrics for invocations and latency
- B. Custom container images from ECR
- C. GPU acceleration
- D. IAM-authenticated invocation through `InvokeEndpoint`

**Answer:** C

**Explanation:** Serverless inference is **CPU-only** — this is the most-tested disqualifier on the exam. The verbatim exclusion list also includes MME, VPC, Data Capture, Model Monitor, multi-variant, marketplace, inference pipelines, private registries, and network isolation. CloudWatch metrics, custom containers, and IAM auth all work normally.

---

## Q280 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Serverless memory and concurrency parameters

A serverless endpoint is configured with `MemorySizeInMB=3072` and `MaxConcurrency=50`. What is true?

- A. Memory must be one of {1024, 2048, 3072, 4096, 5120, 6144} MB; CPU scales with memory
- B. MaxConcurrency can be set up to 1000 in a single endpoint by default
- C. The endpoint can host one GPU worker per concurrent request
- D. Memory above 6144 MB is allowed if you request a quota increase

**Answer:** A

**Explanation:** Serverless memory is restricted to the six discrete values {1024, 2048, 3072, 4096, 5120, 6144} MB and vCPU scales proportionally. The hard MaxConcurrency limit per endpoint is 1–200 (region quota is now 500/1000 per *account*, not per endpoint). No GPU is ever available, and memory above 6144 MB is not offered.

---

## Q281 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Serverless cold-start mitigation

A team finds that their serverless endpoint shows ~6 s cold-start latency on the first request after idle, hurting their UX. They want to keep N workers warm at all times. Which feature should they enable?

- A. SageMaker Neo compilation
- B. Provisioned Concurrency
- C. Provisioned Throughput
- D. SnapStart

**Answer:** B

**Explanation:** Serverless **Provisioned Concurrency** keeps N workers warm (idle billing applies) and drops cold start to ~200 ms. Break-even vs on-demand is roughly 50–70% utilization. Provisioned **Throughput** is a Bedrock concept — easy trap. SnapStart is a Lambda feature, not serverless inference. Neo compiles models but doesn't address worker warm-up.

---

## Q282 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Serverless cold-start CloudWatch signal

Which CloudWatch metric on a serverless endpoint indicates time spent on cold-start / queueing rather than model compute?

- A. `ModelLatency`
- B. `OverheadLatency`
- C. `Invocations`
- D. `BehindScheduleTime`

**Answer:** B

**Explanation:** `OverheadLatency` captures everything outside the model container's compute time — including cold-start spin-up and request queuing. `ModelLatency` is the in-container compute time. A spike in `OverheadLatency` is the textbook signal to consider Provisioned Concurrency.

---

## Q283 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Converting between endpoint types

A team has a real-time endpoint and wants to convert it to a serverless endpoint in place. What must they do?

- A. Call `UpdateEndpointConfig` with `ServerlessConfig` and wait for it to convert
- B. There is no in-place conversion — create a new endpoint config and a new endpoint (or use UpdateEndpoint with a serverless config to swap), and migrate clients
- C. Use SageMaker Pipelines to swap the variant type
- D. Use Inference Recommender to perform the conversion

**Answer:** B

**Explanation:** Real-time and serverless endpoints use different underlying infrastructure and are not interchangeable on a single live endpoint object — there is no in-place conversion. The pattern is to create a new endpoint (or update with a fresh endpoint config) and migrate clients. The "one-way / no-conversion" wording is a recurring exam trap.

---

## Q284 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Async inference invocation flow

In SageMaker Async Inference, how does a client submit a 500 MB request payload?

- A. POST the payload directly in the body of `InvokeEndpointAsync`
- B. Upload the payload to S3, then call `InvokeEndpointAsync` with `InputLocation=s3://...`; the call returns an `InferenceId` immediately
- C. Stream the payload via gRPC to the endpoint
- D. Split the payload into 6 MB chunks and POST each in series

**Answer:** B

**Explanation:** Async inference uses an S3-staged payload pattern: client uploads to S3 → `InvokeEndpointAsync` with the S3 URI returns an InferenceId immediately → SageMaker processes asynchronously → output written to S3 → optional SNS notification. This is the only endpoint type that lets you submit up to 1 GB and process for up to 60 minutes per request.

---

## Q285 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Async inference scaling metric

Which CloudWatch metric should auto-scaling target on an async endpoint to scale instances from zero up when work arrives?

- A. `SageMakerVariantInvocationsPerInstance`
- B. `ApproximateBacklogSizePerInstance`
- C. `ModelLatency`
- D. `CPUUtilization`

**Answer:** B

**Explanation:** Async endpoints expose `ApproximateBacklogSizePerInstance` (backlog of queued requests divided by instance count). This is the metric you target for both scale-out and the special wake-from-zero step-scaling policy on `HasBacklogWithoutCapacity`. `InvocationsPerInstance` is the real-time metric.

---

## Q286 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Canonical async architecture

A typical event-driven async inference architecture chains which AWS services?

- A. API Gateway → Lambda → InvokeEndpoint (real-time) → SNS
- B. S3 upload → Lambda → InvokeEndpointAsync → SNS → Lambda → DynamoDB
- C. EventBridge → SageMaker Pipeline → Step Functions → SNS
- D. Kinesis Data Streams → Firehose → InvokeEndpointAsync

**Answer:** B

**Explanation:** The canonical async pattern is: client puts file in S3 → S3 event → Lambda → `InvokeEndpointAsync` → SageMaker writes output to S3 and publishes SNS success/failure → SNS-subscribed Lambda writes canonical result to DynamoDB. The pattern decouples slow inference from synchronous request handling.

---

## Q287 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Async maximum processing time

What is the maximum per-request processing time on a SageMaker Async Inference endpoint?

- A. 6 minutes
- B. 15 minutes (same as Lambda)
- C. 60 minutes
- D. 24 hours

**Answer:** C

**Explanation:** Async caps each request at 60 minutes processing time. If your job can exceed 60 minutes, use Batch Transform or a SageMaker Processing/Training job instead.

---

## Q288 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Batch Transform parameters

In a Batch Transform job, `MaxConcurrentTransforms` and `MaxPayloadInMB` must satisfy what constraint?

- A. `MaxConcurrentTransforms × MaxPayloadInMB ≤ 100`
- B. `MaxConcurrentTransforms + MaxPayloadInMB ≤ 100`
- C. Both must be powers of 2
- D. No constraint — they are independent

**Answer:** A

**Explanation:** The Batch Transform documented limit is `MaxConcurrentTransforms × MaxPayloadInMB ≤ 100`. Plan job tuning around this — if your records are 25 MB each, you can do at most 4 concurrent transforms per instance.

---

## Q289 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Batch Transform input splitting

Which `BatchStrategy` and `SplitType` combination is appropriate to score one CSV row per invocation when the input file contains 10M rows?

- A. `BatchStrategy=SingleRecord`, `SplitType=Line`
- B. `BatchStrategy=MultiRecord`, `SplitType=None`
- C. `BatchStrategy=SingleRecord`, `SplitType=None`
- D. `BatchStrategy=MultiRecord`, `SplitType=RecordIO`

**Answer:** A

**Explanation:** `SplitType=Line` splits the input by newline, and `BatchStrategy=SingleRecord` sends one record per request to the container. (`MultiRecord` packs as many records as fit under `MaxPayloadInMB` per call — usually more efficient but the question stipulated one row per invocation.)

---

## Q290 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Multi-Model Endpoint configuration

Which of the following describes the correct `CreateModel`/`CreateEndpointConfig` setup for a Multi-Model Endpoint (MME)?

- A. Specify `Mode: MultiModel` on the container and point `ModelDataUrl` at an S3 *prefix* containing many model artifacts
- B. Specify `Mode: SingleModel` and use `TargetVariant` at invoke time
- C. List all models in `ProductionVariants` (one variant per model)
- D. Use `ServerlessConfig` with `MultiModel: true`

**Answer:** A

**Explanation:** MME is configured with `Mode: MultiModel` on the container and `ModelDataUrl` set to an S3 *prefix* (not a single tar.gz). At invoke time, clients pass `TargetModel=<key.tar.gz>` and SageMaker LRU-caches model artifacts in memory. Per-variant models would defeat the purpose; serverless doesn't support MME at all.

---

## Q291 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** MME constraints

Which is a documented limitation of classic SageMaker Multi-Model Endpoints?

- A. All hosted models must use the same framework / container image
- B. They cannot use CPU instances
- C. They require Inference Components
- D. They support unlimited active models in memory simultaneously

**Answer:** A

**Explanation:** MME requires a single shared container — every model on the endpoint must use the same framework / container image. MME on CPU works out-of-the-box, GPU MME requires Triton or TorchServe, Graviton is not supported, and the LRU cache evicts cold models (not all are in memory at once). MME is also not recommended for LLM hosting.

---

## Q292 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** MME hot-model performance

A customer hosts 2,000 small models on an MME and observes occasional ~500 ms tail latency when a model is cold-loaded from S3 on first call. For a handful of hot models that must never be cold, what setting helps?

- A. Set `ModelCacheSetting: Disabled` for hot models so they stay resident (no eviction)
- B. Increase `MaxConcurrency` on the endpoint
- C. Switch to Provisioned Concurrency
- D. Enable Inference Recommender on the endpoint

**Answer:** A

**Explanation:** Setting `ModelCacheSetting: Disabled` (per-model setting available on MME) keeps that model resident — it is not subject to LRU eviction. (The wording is counter-intuitive: "Disabled" disables *caching/eviction*, meaning the model stays loaded.) Provisioned Concurrency is a serverless-only knob; Inference Recommender is unrelated.

---

## Q293 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** MME vs Inference Components

A team is choosing between classic MME and Inference Components for hosting 50 medium-sized models. Which statement is correct?

- A. Inference Components support per-model scale-to-zero and independent scaling, which classic MME does not
- B. MME and IC are functionally identical
- C. Classic MME supports GPU out-of-the-box while ICs do not
- D. ICs require all models to use the same container image; MME does not

**Answer:** A

**Explanation:** Inference Components (2024) are the newer mechanism — each IC scales independently and can scale to zero, including across heterogeneous frameworks. Classic MME shares one container, evicts via LRU, and scales the entire endpoint as one unit. IC is the modern path for multi-model GPU efficiency.

---

## Q294 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** MCE Direct vs Serial mode

A Multi-Container Endpoint (MCE) is created with `InferenceExecutionConfig.Mode = Direct`. How is a specific container invoked?

- A. SageMaker round-robins requests across containers
- B. The client sets the `TargetContainerHostname` header on `InvokeEndpoint` to pick the container
- C. Requests pipeline through containers in declared order
- D. Each container must be hit through its own endpoint URL

**Answer:** B

**Explanation:** In Direct mode, the caller chooses a container per request via `TargetContainerHostname`. In Serial mode, the request is piped through each container in declared order (a lightweight inference pipeline pattern). Both modes share one endpoint URL.

---

## Q295 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Inference Pipelines

Which statement about SageMaker Inference Pipelines is correct?

- A. They support 2–15 containers chained in a single endpoint, sharing memory and network
- B. They are deprecated in favor of MCE Direct mode
- C. They require all containers to use the same framework
- D. They only run on serverless endpoints

**Answer:** A

**Explanation:** Inference Pipelines chain 2–15 containers in a single endpoint (e.g., Spark ML / sklearn preprocessor → model → postprocessor) for training-serving parity. They run on real-time endpoints (not serverless) and explicitly allow heterogeneous frameworks.

---

## Q296 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Cooldown asymmetry in auto-scaling

A team's real-time endpoint thrashes between 5 and 8 instances during bursty traffic. Which adjustment to the target-tracking scaling policy is the textbook fix?

- A. Set `ScaleOutCooldown` and `ScaleInCooldown` to the same value
- B. Set `ScaleOutCooldown` short (~300s) and `ScaleInCooldown` long (~600s) — "out fast, in slow"
- C. Disable cooldowns entirely
- D. Switch to step scaling on CPU

**Answer:** B

**Explanation:** Cooldown asymmetry — scale out fast (~300s) to absorb spikes, scale in slow (~600s) to avoid flapping — is the canonical SageMaker auto-scaling pattern, and stops the thrash described.

---

## Q297 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Application Auto Scaling target dimension

To attach an Application Auto Scaling policy to a SageMaker endpoint's variant, what `ResourceId` form is registered?

- A. `endpoint/{EndpointName}/variant/{VariantName}`
- B. `arn:aws:sagemaker:...:endpoint/{EndpointName}`
- C. `sagemaker/{EndpointName}`
- D. `{EndpointName}.{VariantName}`

**Answer:** A

**Explanation:** Application Auto Scaling registers a SageMaker scalable target as `endpoint/{EndpointName}/variant/{VariantName}` with dimension `sagemaker:variant:DesiredInstanceCount` (or `sagemaker:inference-component:DesiredCopyCount` for ICs).

---

## Q298 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Inference Component scaling

What scalable dimension does Application Auto Scaling use for Inference Components?

- A. `sagemaker:variant:DesiredInstanceCount`
- B. `sagemaker:inference-component:DesiredCopyCount`
- C. `sagemaker:endpoint:DesiredInstanceCount`
- D. `sagemaker:async:DesiredInstanceCount`

**Answer:** B

**Explanation:** Inference Components scale on `DesiredCopyCount` — the number of model copies, not the number of underlying instances. This is what enables per-model scale-to-zero on a shared instance fleet.

---

## Q299 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Wake-from-zero scaling

Which scaling policy type and metric combination is used to wake an async endpoint from zero instances?

- A. Target tracking on `InvocationsPerInstance`
- B. Step scaling on `HasBacklogWithoutCapacity`
- C. Scheduled scaling at fixed times
- D. Predictive scaling on `CPUUtilization`

**Answer:** B

**Explanation:** Async endpoints at zero instances have no `InvocationsPerInstance` denominator, so target tracking can't wake them. The documented pattern is a step-scaling policy on the `HasBacklogWithoutCapacity` metric, which fires when a request is queued with no instance to serve it.

---

## Q300 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Deployment strategies overview

(Select THREE) Which of the following are valid SageMaker `DeploymentConfig` update strategies?

- A. All-at-once
- B. Blue/Green with traffic shifting (canary, linear, or all-at-once)
- C. Rolling Updates for Inference Components
- D. Cold deploy (delete & recreate)
- E. Shadow update — automatically promotes after 24h of shadow traffic

**Answer:** A,B,C

**Explanation:** SageMaker supports All-at-once, Blue/Green (with All-at-once, Canary, or Linear traffic shifting), and Rolling Updates (IC-only, 2024). "Cold deploy" and "shadow auto-promote" are not built-in strategies.

---

## Q301 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Blue/Green capacity implications

Which statement about Blue/Green deployments on SageMaker is true?

- A. Blue/Green requires approximately 2× the steady-state instance capacity during the cutover
- B. Blue/Green has no extra capacity cost — both fleets share instances
- C. Blue/Green is only available on serverless endpoints
- D. Blue/Green and Canary deployments are the same thing

**Answer:** A

**Explanation:** Blue/Green stands up an entirely fresh fleet (green) alongside the existing fleet (blue), shifts traffic, then tears down blue — so during cutover you're paying for ~2× capacity. Canary is a sub-mode of Blue/Green's traffic-shifting choice (canary vs linear vs all-at-once).

---

## Q302 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Auto-rollback

A team configures `AutoRollbackConfiguration` with a CloudWatch alarm on `ModelLatency`. The new model deploys, latency stays normal, but the offline AUC of the predictions silently drops 8%. What happens?

- A. Auto-rollback fires because AUC dropped
- B. Auto-rollback does NOT fire — CloudWatch alarms see latency/errors, not prediction quality; Model Monitor / quality drift checks are needed for silent regressions
- C. SageMaker automatically computes online AUC and rolls back
- D. The endpoint pauses until the alarm is hand-edited

**Answer:** B

**Explanation:** Auto-rollback only fires on the CloudWatch alarms you wire it to — typically latency and 5XX/4XX errors. A "silent quality regression" (the model is fast and returns 200s but the predictions are worse) is invisible to auto-rollback. Catching this is Model Monitor's job (data-quality / model-quality drift checks).

---

## Q303 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Endpoint metrics

Which CloudWatch metric should you alarm on to detect upstream instance saturation distinct from in-container compute time?

- A. `ModelLatency`
- B. `OverheadLatency`
- C. `Invocation5XXErrors`
- D. `Invocations`

**Answer:** B

**Explanation:** `ModelLatency` is what the model code spends; `OverheadLatency` is queueing/framework overhead inside SageMaker before/after the model. Rising `OverheadLatency` while `ModelLatency` is flat usually means instance saturation (or, on serverless, cold-starts).

---

## Q304 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Inference Recommender — Default vs Advanced

Which statement contrasts Inference Recommender's Default and Advanced jobs correctly?

- A. Default ~45 min picks from an AWS-curated instance shortlist; Advanced ~2h runs a custom load test against up to 10 candidate configurations with user-supplied SLOs
- B. Default jobs require a custom traffic generator; Advanced jobs use AWS defaults
- C. Both jobs run for exactly the same duration; only the price differs
- D. Advanced jobs only support serverless endpoints

**Answer:** A

**Explanation:** Default job (~45 min) is a quick screen over AWS's curated instance shortlist. Advanced job (~2h) accepts your traffic pattern + SLO (latency, max invocations) and benchmarks up to 10 candidate configurations, returning rows with `ModelLatency`, `MaxInvocations`, `CostPerHour`, `CostPerInference`.

---

## Q305 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Inference Recommender prerequisites

What is a hard prerequisite for running an Inference Recommender job?

- A. The model must be registered as a ModelPackage in the SageMaker Model Registry
- B. The endpoint must already be live
- C. The account must have ≥ 100 GPU instances of quota
- D. The model must be compiled with SageMaker Neo first

**Answer:** A

**Explanation:** Inference Recommender takes a registered `ModelPackage` (in Model Registry) as input — it spins up its own test endpoints. The endpoint does not need to pre-exist, no Neo compilation is required, and there's no GPU-quota mandate.

---

## Q306 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Compute Optimizer trap

A team wants right-sizing recommendations for their SageMaker inference endpoints. Which AWS service should they use?

- A. AWS Compute Optimizer
- B. AWS Trusted Advisor
- C. SageMaker Inference Recommender
- D. AWS Cost Explorer

**Answer:** C

**Explanation:** This is a recurring exam trap — **Compute Optimizer does NOT cover SageMaker** (EC2, Lambda, EBS, Auto Scaling Groups, ECS on Fargate, RDS — but not SageMaker endpoints). Right-sizing inference endpoints is Inference Recommender's job.

---

## Q307 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** SageMaker Neo

Which frameworks/formats does SageMaker Neo support for compilation?

- A. Only TensorFlow and PyTorch
- B. PyTorch, TensorFlow, Keras, MXNet, ONNX, TFLite, XGBoost
- C. Only ONNX
- D. Only Hugging Face Transformers via JumpStart

**Answer:** B

**Explanation:** Neo (built on Apache TVM) compiles PyTorch, TensorFlow, Keras, MXNet, ONNX, TFLite, and XGBoost for a wide range of cloud and edge targets (Inferentia, GPU, CPU, ARM, Greengrass devices).

---

## Q308 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Inferentia vs GPU

For hosting Llama-70B in production at significant scale, which combination tends to be the best price-performance choice today?

- A. p4d.24xlarge with vanilla PyTorch
- B. Inf2 instances with Neo-compiled or LMI-served model (often ~60% cheaper than p4d)
- C. CPU c6i instances with INT4 quantization
- D. ml.t3.medium with FP16

**Answer:** B

**Explanation:** Inferentia2 (Inf2) is AWS's purpose-built inference accelerator — Neo-compiled or LMI-served Llama-70B on Inf2 is consistently around 60% cheaper than equivalent p4d-class GPU hosting (AWS-published benchmarks show ~5.4× price-perf vs compiled GPU). CPU is far too slow for 70B; t3 has no GPU and tiny memory.

---

## Q309 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Edge inference deployment

A factory wants to run a vision model on Greengrass devices at the edge. Which AWS service is the recommended path today?

- A. AWS IoT Greengrass v2 ML components (Model + Runtime + Inference)
- B. SageMaker Edge Manager (still the preferred path)
- C. AWS Outposts
- D. SageMaker Real-time endpoint in eu-west-1

**Answer:** A

**Explanation:** **SageMaker Edge Manager has been deprecated** — the recommended path is Greengrass v2 ML components (Model component, Runtime component such as DLR/TFLite, Inference component for app logic), typically pre-compiled with Neo. Outposts is a hybrid hardware play, not the standard edge ML answer.

---

## Q310 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Triton vs LMI for LLM serving

A team in 2025 plans to host a 13B-parameter LLM on a SageMaker GPU endpoint and wants the highest tokens/sec/$ and continuous batching with paged-attention. Which container is the right choice?

- A. SageMaker Large Model Inference (LMI) container, which wraps vLLM
- B. NVIDIA Triton Inference Server with dynamic batching
- C. The default PyTorch DLC
- D. SageMaker XGBoost container

**Answer:** A

**Explanation:** As of 2025–26, LLM serving on SageMaker has converged on the **LMI container (vLLM-based)** for continuous batching + PagedAttention. Triton is still excellent for multi-framework, ensembles, and dynamic-batched non-LLM workloads — but **Triton ≠ LLM serving answer** anymore on the exam.

---

## Q311 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Quantization tradeoffs

What is a reasonable expectation when applying INT8 post-training quantization to a transformer model?

- A. 1–3% accuracy drop, ~4× memory reduction, 2–4× throughput improvement
- B. 50% accuracy drop with no throughput gain
- C. Memory footprint unchanged but 10× speedup
- D. Accuracy improves and memory increases

**Answer:** A

**Explanation:** INT8 PTQ typically yields a small accuracy drop (~1–3%), ~4× memory reduction vs FP32, and 2–4× throughput improvement on accelerators that support INT8 math. INT4/AWQ pushes memory savings further for memory-bound LLM workloads; FP8 is supported on H100/H200.

---

## Q312 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Lambda inference limits

A team wants to host a small XGBoost classifier on AWS Lambda behind API Gateway. Which Lambda constraint is most relevant?

- A. 15-minute max execution time, 10 GB container-image limit, 10 GB `/tmp`, no GPU
- B. 60-minute max execution time and GPU available via `Architecture: gpu`
- C. 100 MB max deployment package and no container image support
- D. Lambda cannot be called from API Gateway

**Answer:** A

**Explanation:** Lambda for inference: 15-minute max, 10 GB image (via ECR), 10 GB ephemeral `/tmp`, and crucially **no GPU**. API Gateway + Lambda is a canonical lightweight-inference pattern for small CPU models. (For larger models, use SageMaker Serverless or real-time.)

---

## Q313 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Lambda SnapStart

What is Lambda SnapStart's effect on Python ML cold starts (post Nov 2024 GA)?

- A. It eliminates the need for ECR images
- B. It reduces Python cold starts dramatically (≈ 16s → ≈ 1.4s in published examples) by snapshotting the initialized runtime
- C. It is available on Node.js only
- D. It adds a permanent ~5 s tax to every invocation

**Answer:** B

**Explanation:** SnapStart snapshots a fully initialized execution environment and rehydrates from it, slashing cold starts. Originally Java-only, Lambda SnapStart for **Python 3.12+** GA'd in November 2024 — published examples show ~16s → ~1.4s cold-start reductions for Python ML loaders.

---

## Q314 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** EKS for ML serving — vLLM

In 2024–26, which combination is the dominant pattern for self-managed LLM serving on EKS?

- A. KServe with vLLM (PagedAttention + multi-LoRA), GPU node groups via Karpenter
- B. Spark Structured Streaming with MLlib pipelines
- C. Amazon Lex with hand-written intents
- D. Fargate-only EKS clusters with no GPU

**Answer:** A

**Explanation:** The reference EKS LLM stack today is KServe (or raw Deployments) running **vLLM with PagedAttention + multi-LoRA**, with Karpenter provisioning GPU nodes on demand. Capital One's "IFX" platform (KServe + K8s + 7 engineers + millions of tx/day) is the often-cited case study. Fargate has no GPU support.

---

## Q315 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** SageMaker Operators for Kubernetes (ACK)

Which statement is true about running SageMaker workloads from a Kubernetes cluster in 2024–26?

- A. The original SageMaker Operators for Kubernetes is deprecated; use ACK-based SageMaker Operators (released 2024)
- B. The only way to call SageMaker from EKS is via Step Functions
- C. There is no Kubernetes-native CRD for SageMaker
- D. SageMaker Operators for Kubernetes only work in EKS Anywhere

**Answer:** A

**Explanation:** The original SageMaker Operators for Kubernetes (2019) was deprecated. The replacement is the **ACK-based SageMaker controllers** (AWS Controllers for Kubernetes), which provide CRDs for TrainingJob, ProcessingJob, Endpoint, Model, etc., and are the recommended path today.

---

## Q316 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** HyperPod Inference Operator

What is the HyperPod Inference Operator (April 2026)?

- A. A managed EKS add-on for HyperPod that provides tiered KV-cache hosting for LLMs and roughly 40% latency reduction in published benchmarks
- B. A replacement for SageMaker Pipelines
- C. A Lambda extension
- D. A new IDE for SageMaker Studio

**Answer:** A

**Explanation:** The HyperPod Inference Operator is an EKS managed add-on released April 2026 for HyperPod clusters; it ships tiered KV-cache management for LLM inference and AWS-published benchmarks show roughly 40% latency reduction on large models.

---

## Q317 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** EKS vs SageMaker breakeven

A team is debating "self-managed EKS LLM hosting" vs "SageMaker real-time endpoints." Approximately what monthly inference spend is the typical breakeven where EKS starts to pay off?

- A. Around $30K–$50K per month
- B. Around $500 per month
- C. Around $5M per month
- D. There is no breakeven — SageMaker is always cheaper

**Answer:** A

**Explanation:** The widely-cited heuristic is ~$30–50K/month of inference spend before EKS self-management (plus ~3–7 platform engineers) recovers the SageMaker premium. Below that, SageMaker's managed cost is hard to beat.

---

## Q318 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Real-time vs serverless decision

A pricing API needs sub-100 ms p99 latency on every request, sustained 50 RPS during business hours, near-zero on weekends. The model is 500 MB and CPU-only. What is the best endpoint choice?

- A. Real-time endpoint with target-tracking auto-scaling on `InvocationsPerInstance`, optional scale-to-zero with Inference Components
- B. Serverless inference with MaxConcurrency=200 and no PC
- C. Async inference
- D. Batch Transform every minute

**Answer:** A

**Explanation:** Sub-100 ms p99 + sustained 50 RPS rules out serverless cold-start surprises (without expensive PC). Real-time with `InvocationsPerInstance` target tracking handles the daily ramp; if weekend cost matters, Inference Components add per-model scale-to-zero. Async/batch don't meet sub-100ms.

---

## Q319 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Real-time vs async decision

A genomics workflow submits one 800 MB sequencing record at a time; results are tolerable within 10–30 minutes, and traffic is irregular (10 records per hour during the day). Which endpoint fits?

- A. Real-time endpoint (it's just one record at a time)
- B. Serverless endpoint
- C. Async inference endpoint
- D. Batch Transform

**Answer:** C

**Explanation:** 800 MB > real-time's 6 MB cap and >> serverless's 4 MB cap. Async accepts payloads up to 1 GB via S3 staging, processes for up to 60 min, can scale to zero between requests, and supports SNS notifications when a long job finishes. Batch Transform is fine but is "submit a job" semantics rather than "submit a record and get an InferenceId."

---

## Q320 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** MME use-case fit

(Select TWO) Which workloads are good fits for a classic Multi-Model Endpoint?

- A. 5,000 small per-customer tree-based recommendation models, similar size and same framework
- B. A single 70B-parameter LLM
- C. 1,000 small per-region sklearn classifiers, all in one container image
- D. A mixed fleet: one PyTorch model, one TensorFlow model, one XGBoost model
- E. A vision model needing GPU-accelerated dynamic batching with Triton ensembles

**Answer:** A,C

**Explanation:** MME shines for many small same-framework models on shared CPU (or Triton-GPU) instances — Zendesk's reported 90% cost-savings hosting thousands of per-account models and the Stable Diffusion MME 75% savings ($218k → $54k/month) story both fit. LLM hosting on MME is explicitly discouraged. Mixed frameworks need MCE, not MME. The Triton ensemble case is a Triton problem, not the classic MME use case.

---

## Q321 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Real-time variant traffic ramp

A team wants to gradually migrate 100% of traffic from `VariantA` to `VariantB` over a week. Which API call shifts live weights?

- A. `UpdateEndpointWeightsAndCapacities` with the desired new `DesiredWeight` per variant
- B. `UpdateEndpointConfig` (which would replace the endpoint config and risk a full re-deploy)
- C. `DeleteEndpointConfig` and `CreateEndpoint`
- D. `InvokeEndpoint` with a header `Weight: 50`

**Answer:** A

**Explanation:** `UpdateEndpointWeightsAndCapacities` adjusts `DesiredWeight` (and optionally `DesiredInstanceCount`) per variant on a live endpoint — no redeploy, no downtime. `UpdateEndpointConfig` swaps the entire config, which is heavier and has different blue/green semantics.

---

## Q322 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Rolling Updates scope

Rolling Updates as a SageMaker deployment strategy applies to which workload?

- A. Any real-time endpoint
- B. Inference Components only (2024)
- C. Serverless endpoints only
- D. Batch Transform jobs

**Answer:** B

**Explanation:** Rolling Updates were introduced in 2024 specifically for **Inference Components** — they update IC copies progressively rather than swapping whole fleets. Classic ProductionVariants still use All-at-once, Canary, or Linear under Blue/Green semantics.

---

## Q323 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Step Functions integration with async inference

How can a Step Functions workflow synchronously wait for a SageMaker async inference job to complete?

- A. Poll `DescribeAsyncJob` in a Wait state
- B. Use the `.waitForTaskToken` integration pattern — pass the task token into the async job and call `SendTaskSuccess` from the SNS-completion Lambda
- C. Use the `.sync` pattern, which is natively supported for InvokeEndpointAsync
- D. Step Functions cannot interact with async inference

**Answer:** B

**Explanation:** Async inference has no `.sync` Step Functions integration (it returns InferenceId immediately, then completes asynchronously). The canonical pattern is `.waitForTaskToken`: the Lambda that calls `InvokeEndpointAsync` includes the task token; the SNS-success Lambda calls `SendTaskSuccess` with the result, unblocking the workflow.

---

## Q324 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Batch Transform cost optimization

(Select TWO) Which options reduce the cost of a nightly Batch Transform job over a 500 GB input?

- A. Use Spot instances for the Transform job
- B. Increase `MaxConcurrentTransforms` (subject to the `× MaxPayloadInMB ≤ 100` constraint) and use `BatchStrategy=MultiRecord`
- C. Switch the endpoint to serverless
- D. Increase `MaxPayloadInMB` to 1024 to pack more per request
- E. Call `InvokeEndpoint` from a Lambda in a loop instead of using Transform

**Answer:** A,B

**Explanation:** Batch Transform supports Spot, which can cut compute cost dramatically for tolerant overnight workloads. Tuning `MaxConcurrentTransforms` and using `MultiRecord` packs more records per call (subject to the 100 product constraint), increasing throughput and lowering cost. Batch Transform isn't an endpoint, so "serverless conversion" doesn't apply; `MaxPayloadInMB=1024` violates the constraint at any nontrivial concurrency; Lambda-loop invocation is expensive and rate-limited.

---

## Q325 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** End-to-end inference architecture choice

A bank needs to host (a) a fraud-scoring model with <50 ms p99 at sustained traffic, (b) 2,000 small per-merchant risk models, and (c) periodic 800 MB document analyses that can take 20 minutes. Which combination is the best fit?

- A. Real-time endpoint for fraud, MME (or Inference Components) for the 2,000 merchant models, Async inference for document analyses
- B. Serverless for everything
- C. Batch Transform for everything
- D. EKS-only — abandon SageMaker

**Answer:** A

**Explanation:** Real-time matches the <50ms SLO of fraud scoring; MME or Inference Components match the many-small-models pattern (Zendesk-style cost savings); Async matches the large-payload, long-running document case. Serverless can't carry the 50 ms SLO at scale and is capped at 4 MB payload (so docs are out). Batch Transform is wrong for the interactive workloads. EKS is viable but is an extreme answer; this combination is the canonical SageMaker fit.

---
# MLA-C01 Practice — Domain 3 (Part H, Half B): Pipelines, Orchestration, EventBridge, CI/CD, IaC

> **Scope:** 55 exam-realistic questions covering Chapters 43-47 of the AWS Certified Machine Learning Engineer — Associate (MLA-C01) curriculum.
>
> **Covered topics:**
> - **Ch 43 — SageMaker Pipelines** (15 step types, Parameters vs ExecutionVariables, PropertyFile/JsonGet, caching, SelectiveExecution, retries, PipelineSession, `@step`, limits, triggers)
> - **Ch 44 — Orchestrator comparison** (Step Functions Standard vs Express, Distributed Map, `.sync` matrix, MWAA environment classes & Airflow 3.x, decision tree)
> - **Ch 45 — EventBridge** (Rules, Scheduler, Pipes, 1 MB payload bump Jan 2026, `aws.sagemaker` event catalog, drift-to-retrain loop, cross-account, S3 toggle)
> - **Ch 46 — CodePipeline / CodeBuild / CodeDeploy / CodeArtifact / CodeCommit / GitHub Actions OIDC**
> - **Ch 47 — IaC: CloudFormation, CDK (L1/L2/L3, Pipelines self-mutation), SAM, Terraform, SageMaker Projects**
>
> **Parseable format:**
> ```
> ## Q{n} — Domain 3: Deployment and Orchestration of ML Workflows
> **Objective:** {one-line objective}
>
> {question stem}
>
> - A. {option}
> - B. {option}
> - C. {option}
> - D. {option}
>
> **Answer:** {letter or comma-separated letters for multi-select}
>
> **Explanation:** {why correct + why distractors fail}
> ```

---

## Q326 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize that `ModelStep` replaces the legacy `CreateModelStep` + `RegisterModel`

In a new SageMaker Pipelines project, a data engineer needs to register a trained model to the Model Registry with `approval_status="PendingManualApproval"`. Which step type is the modern (post-2022, SDK v2.90+) authoring approach?

- A. `RegisterModel(name="Register", estimator=xgb, model_data=...)`
- B. `CreateModelStep(name="Register", model=model)` followed by a `RegisterModel(...)` step
- C. `ModelStep(name="Register", step_args=model.register(...))`
- D. `LambdaStep` that calls `sagemaker.create_model_package(...)` directly

**Answer:** C

**Explanation:** `ModelStep` (introduced in SageMaker Python SDK v2.90.0, mid-2022) consolidates the legacy `CreateModelStep` and `RegisterModel` classes — call `model.create(...)` for a deployable model or `model.register(...)` for a versioned Model Package, and wrap the returned `step_args` in a single `ModelStep`. Options A and B are deprecated authoring styles still seen in older docs and Skill Builder labs; the modern answer is always `ModelStep`. Option D bypasses Pipelines' native step semantics and loses lineage tracking.

---

## Q327 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Identify the PipelineSession vs Session trap

A junior engineer wired up an `XGBoost` estimator with the default `sagemaker.Session()`, then passed it into a `TrainingStep`. They notice that every `pipeline.upsert()` triggers a real training job *in addition to* the one that runs on `pipeline.start()`. What is the one-line fix?

- A. Add `cache_config=CacheConfig(enable_caching=True, expire_after="P30D")` to the `TrainingStep`
- B. Change the estimator's `sagemaker_session=` to `PipelineSession()` (and share it with the `Pipeline`)
- C. Call `pipeline.upsert(dry_run=True)` instead of `pipeline.upsert()`
- D. Wrap the `TrainingStep` inside a `ConditionStep` so it only runs at execution time

**Answer:** B

**Explanation:** A regular `Session` executes SageMaker API calls **immediately**, so `xgb.fit(...)` at definition time actually starts a training job. `PipelineSession` defers execution — every `fit`/`run`/`transform`/`register` call returns step arguments instead of starting work. The classic doubled-job symptom always points to this fix. Caching (A) doesn't prevent the definition-time job. `dry_run=True` (C) isn't an `upsert` parameter. Wrapping in `ConditionStep` (D) doesn't change when the estimator's `fit` executes.

---

## Q328 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply the AutoMLStep ENSEMBLING-only constraint

A team wants to run SageMaker Autopilot inside a pipeline and reads in an old blog post that `mode="HYPERPARAMETER_TUNING"` gives better results. They wire up an `AutoMLStep` with that mode. What happens?

- A. The pipeline runs successfully and uses Bayesian HPO under the hood
- B. The pipeline runs but skips the AutoMLStep with a warning
- C. The pipeline fails because `AutoMLStep` inside a SageMaker Pipeline only supports `ENSEMBLING` mode
- D. The pipeline fails because `AutoMLStep` requires `mode="V2_DEFAULT"`

**Answer:** C

**Explanation:** Inside a SageMaker Pipeline, `AutoMLStep` (wrapping `CreateAutoMLJobV2`) only supports `mode="ENSEMBLING"` (the H2O-based stack of GBMs, linear models, and neural nets). The older HPO Bayesian path is **not** allowed in a pipeline context, though it is permitted for standalone Autopilot jobs outside Pipelines. The canonical pattern is `AutoMLStep → ConditionStep (gate on metric) → ModelStep (register the winner via `step_automl.get_best_auto_ml_model(...)`)`.

---

## Q329 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Choose Parameters vs ExecutionVariables

For each requirement, choose the correct SageMaker Pipelines primitive: (1) **user-overridable per run** (e.g., MSE threshold tunable from CI), and (2) **SageMaker-controlled runtime identifier** (e.g., a unique S3 path per execution).

- A. (1) ExecutionVariable, (2) ParameterString
- B. (1) ParameterFloat, (2) ExecutionVariables.PIPELINE_EXECUTION_ID
- C. (1) ParameterString, (2) ParameterString
- D. (1) Pipeline metadata tag, (2) Pipeline metadata tag

**Answer:** B

**Explanation:** **Parameters** (`ParameterString`, `ParameterInteger`, `ParameterFloat`, `ParameterBoolean`) are user-controlled and overridable at `pipeline.start(parameters={...})` time — perfect for a tunable threshold. **ExecutionVariables** (`PIPELINE_EXECUTION_ID`, `START_DATETIME`, `PIPELINE_ARN`, etc.) are SageMaker-filled at execution start and are the canonical answer for "unique S3 path per execution," typically joined into the destination via `sagemaker.workflow.functions.Join`. The other options conflate the two.

---

## Q330 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply PropertyFile + JsonGet for inter-step data passing

A `ProcessingStep` writes `/opt/ml/processing/evaluation/evaluation.json` containing `{"regression_metrics": {"mse": {"value": 4.2}}}`. A downstream `ConditionStep` must gate on whether `mse <= 6.0`. Which combination is correct?

- A. Declare `PropertyFile(name="EvalReport", output_name="evaluation", path="evaluation.json")` on the ProcessingStep, then use `JsonGet(step_name=..., property_file=..., json_path="regression_metrics.mse.value")` in the condition
- B. Use `step_eval.properties.RegressionMetrics.MSE.Value` directly (PropertyFile not needed)
- C. Pass the value through a Lambda via `LambdaStep` and reference its output
- D. Write the value to a `ParameterFloat` mid-execution and read it later

**Answer:** A

**Explanation:** **PropertyFile + JsonGet** is the canonical mechanism for passing **arbitrary JSON your code writes** between steps. The `PropertyFile` tells SageMaker where the JSON lives (relative to a named ProcessingOutput); `JsonGet` reads any nested path via dotted notation (not JSONPath `$.`). Max property file size is 5 MB. Option B is wrong — `.properties` exposes only the underlying `Describe*Job` API response, not arbitrary user JSON. Option C works but is wasteful. Option D is impossible — parameters can't be mutated mid-execution.

---

## Q331 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Configure step caching with ISO-8601 duration

A team runs the same pipeline 15-20 times a day; only `evaluate.py` changes between runs. Preprocessing takes 40 minutes and training takes 20 minutes. Which `CacheConfig` is correct AND cost-effective?

- A. `CacheConfig(enable_caching=True, expire_after="30d")`
- B. `CacheConfig(enable_caching=True, expire_after="P30D")` on Processing and Training steps
- C. `CacheConfig(enable_caching=False, expire_after="P30D")` everywhere
- D. `CacheConfig(enable_caching=True, expire_after="2592000")` (seconds)

**Answer:** B

**Explanation:** `expire_after` requires **ISO-8601 duration** notation (`P30D`, `P7D`, `PT12H`, `PT30M`). `"30d"` (A) and raw seconds (D) are not valid. Caching scoped to Processing and Training steps lets unchanged upstream hashes cache-hit, saving 60 of every 65 minutes per run when only `evaluate.py` changes — exactly the canonical iteration cost-killer. Disabling caching (C) defeats the purpose.

---

## Q332 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Use SelectiveExecution to re-run a subset of steps

Yesterday's pipeline execution `arn:aws:sagemaker:...:pipeline-execution/abc123` succeeded through training but failed at evaluation because of a typo. The fix is a one-character change in `evaluate.py`. The team wants to re-run only Eval, GateOnMSE, and Register — not preprocessing or training. Which mechanism is the most deterministic answer?

- A. Enable `CacheConfig` and rely on signature-based reuse
- B. Use `SelectiveExecutionConfig(source_pipeline_execution_arn="...abc123", selected_steps=["Eval", "GateOnMSE", "Register"])`
- C. Call `pipeline.start()` with `parameters={"SkipPreprocessing": True, "SkipTraining": True}`
- D. Use a `ConditionStep` at the top of the pipeline that branches on a "ResumeFrom" parameter

**Answer:** B

**Explanation:** **SelectiveExecution** (GA June 2023) is the *explicit, execution-pointer-based* primitive — you name a prior execution ARN and the steps to re-run; SageMaker reuses upstream outputs from that source execution. It's more deterministic than caching because it doesn't depend on hash matching. Caching (A) still works but a script edit (even whitespace) that changes the hash breaks the cache. Options C and D are not built-in primitives and require custom plumbing.

---

## Q333 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply the ConditionStep nesting prohibition

A scenario requires: "if MSE ≤ threshold, *then* check bias; if both pass, register." A junior engineer writes a `ConditionStep` whose `if_steps` contains another `ConditionStep`. Which statement is correct?

- A. Nested `ConditionStep`s are supported via the `ConditionAnd` operator
- B. `ConditionStep` cannot be nested inside another `ConditionStep`'s `if_steps`/`else_steps` branches; collapse both checks into one `ConditionStep` with `conditions=[mse_ok, bias_ok]` (implicit AND), or use two sequential top-level ConditionSteps
- C. The SDK silently flattens nested ConditionSteps; no change needed
- D. Wrap each ConditionStep in a `LambdaStep` to enable nesting

**Answer:** B

**Explanation:** A `ConditionStep` **cannot contain another `ConditionStep`** in its branches — this is a top-three exam trap. The correct expression is either (a) a single `ConditionStep` with `conditions=[mse_ok, bias_ok]` (implicit AND across the list) or (b) two sequential top-level ConditionSteps where the first's `if_steps` points at the second. `ConditionAnd` (A) doesn't exist as an operator class — AND is implicit; OR uses `ConditionOr`.

---

## Q334 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Choose between LambdaStep and CallbackStep

A team needs to pause a pipeline for **up to 4 hours** while an external Jenkins job runs on-prem and reports back. Which step type is correct?

- A. `LambdaStep` — invoke a Lambda that polls Jenkins synchronously
- B. `CallbackStep` — SQS + task token; external worker calls `SendPipelineExecutionStepSuccess` with the token
- C. `ProcessingStep` running a long-polling Python script
- D. `EMRStep` that wraps the Jenkins call

**Answer:** B

**Explanation:** `LambdaStep` has a **15-minute hard timeout** (Lambda's own limit), so it cannot wait 4 hours. `CallbackStep` is the **async escape hatch**: SageMaker drops a message on your SQS queue with a token, the step waits indefinitely, and the external system calls `SendPipelineExecutionStepSuccess(CallbackToken=...)` or `…StepFailure(...)` to resume the DAG. Default timeout is unbounded; configurable per step. Options C and D would require hacks and aren't designed for this.

---

## Q335 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize Pipelines limits

Which set correctly lists default SageMaker Pipelines limits the exam may test?

- A. 1,000 steps per pipeline; 10 MB definition; 50 concurrent executions; 1 MB property file
- B. 100 steps per pipeline (soft); 1 MB definition; 200 concurrent executions per account (soft); 5 MB property file
- C. 50 steps per pipeline; 256 KB definition; 100 concurrent executions; 256 KB property file
- D. Unlimited steps; 1 MB definition; 10 concurrent executions; 5 MB property file

**Answer:** B

**Explanation:** The four numbers to recite under exam pressure are **100 steps (soft), 1 MB definition, 200 concurrent executions (soft), 5 MB property file**. The 100-step soft limit is the most common pressure point on large pipelines — decompose into sub-pipelines or invoke from Step Functions when you exceed it.

---

## Q336 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Identify FailStep semantics

A `ConditionStep` has `else_steps=[]` (empty list). What happens if the condition evaluates to False?

- A. The pipeline execution status is `Failed` with a descriptive error message
- B. The pipeline silently succeeds — the empty branch is a no-op, so execution status becomes `Succeeded`
- C. SageMaker raises a validation error at `pipeline.upsert()` time
- D. The pipeline retries the ConditionStep until the condition becomes True

**Answer:** B

**Explanation:** An empty `else_steps=[]` is **legal** and means "do nothing" — the pipeline finishes green even though the gate logically "failed." To make rejection explicit and observable in execution history (and for auditors), use a `FailStep` with a descriptive `error_message` in the `else_steps`. This is one of the fifteen documented Pipelines traps.

---

## Q337 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Distinguish ParallelismConfiguration from TuningStep's max_parallel_jobs

A `TuningStep` declares `max_parallel_jobs=8` on the `HyperparameterTuner`. The pipeline is started with `ParallelismConfiguration(max_parallel_execution_steps=2)`. How many tuning trials run concurrently?

- A. 2 (capped by ParallelismConfiguration)
- B. 8 (ParallelismConfiguration does not affect TuningStep internal trial parallelism)
- C. 16 (multiplicative)
- D. 1 (TuningStep is always sequential)

**Answer:** B

**Explanation:** `ParallelismConfiguration.max_parallel_execution_steps` caps concurrent **pipeline steps**, not concurrent **trials inside a TuningStep**. Trial concurrency is controlled by `max_parallel_jobs` on the `HyperparameterTuner` and is independent. This is a frequent exam trap — the two settings look similar but operate at different layers.

---

## Q338 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** List valid pipeline trigger sources

Which of the following are **valid native trigger sources** for a SageMaker Pipeline? (Select THREE)

- A. EventBridge Scheduler with universal-target ARN `arn:aws:scheduler:::aws-sdk:sagemaker:startPipelineExecution`
- B. S3 EventBridge "Object Created" event via an EventBridge Rule
- C. MWAA via `SageMakerStartPipelineExecutionOperator`
- D. A SageMaker Endpoint's auto-scaling alarm directly
- E. AWS Macie classification job completion directly

**Answer:** A, B, C

**Explanation:** The seven canonical pipeline trigger sources are: SDK/CLI/console, EventBridge Rule, EventBridge Scheduler, S3 EventBridge events, MWAA (`SageMakerStartPipelineExecutionOperator`), Step Functions (`startPipelineExecution.sync`), and CodePipeline. Endpoint auto-scaling alarms (D) trigger scaling, not pipelines (you'd need a CloudWatch alarm → EventBridge → Lambda hop). Macie (E) does not natively trigger Pipelines.

---

## Q339 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize Pipelines' auto-enabled lineage tracking

A compliance officer asks: "Show me end-to-end lineage from the raw transaction CSV through preprocessing, training, evaluation, and registration to the deployed endpoint — with no custom instrumentation code." Which orchestrator gives this **out of the box**?

- A. AWS Step Functions
- B. Amazon MWAA
- C. SageMaker Pipelines (auto-creates Artifacts, Trial components, Trial, Action, and Context entities)
- D. AWS Glue Workflows

**Answer:** C

**Explanation:** Pipelines auto-emits lineage entities (Artifacts, Trial components, Trial, Action, Context) per execution — queryable via `sagemaker.lineage.query.LineageQuery` or `aws sagemaker query-lineage`. Step Functions and MWAA require **manual lineage instrumentation** (you write code to emit Artifacts via the SageMaker SDK). Glue Workflows has data-catalog lineage but doesn't extend to SageMaker model artifacts.

---

## Q340 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Use the @step decorator for Python-function steps

What is the `@step` decorator (Nov 2023) in SageMaker Pipelines?

- A. A way to mark a function as a `ConditionStep`
- B. A decorator that lifts a Python function into a pipeline step that runs as a SageMaker Training job, with the DAG inferred from the call graph
- C. A timing utility that profiles step execution
- D. A decorator that enables step caching automatically with no other configuration

**Answer:** B

**Explanation:** The `@step` decorator (introduced Nov 2023) converts a plain Python function into a pipeline step backed by a SageMaker Training job (pickled state + a SageMaker container). The dependency graph is inferred by inspecting the **call graph** — passing one `@step` function's return value to another creates a data-dependency edge. Limitations: no non-Python state (no Spark sessions, JVM objects), and step types like Tuning/Transform/Condition/Lambda/Callback still require class-based forms.

---

## Q341 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize EMRStep vs EMRServerlessStep

A team's pipeline must run a Spark job. Their org already runs a 24/7 EMR cluster shared with the BI team. Which step type fits?

- A. `EMRServerlessStep` with `cluster_id` of the existing cluster
- B. `EMRStep` with `cluster_id="j-1ABC..."` and `step_config=EMRStepConfig(jar="command-runner.jar", args=[...])`
- C. `ProcessingStep` with `PySparkProcessor` (mandatory; EMRStep not allowed in Pipelines)
- D. `LambdaStep` that calls EMR via the AWS SDK

**Answer:** B

**Explanation:** `EMRStep` with a `cluster_id` submits a step (`AddJobFlowSteps`) to an **existing long-running EMR cluster**. This is the canonical pattern when the org already pays for a 24/7 cluster. `EMRServerlessStep` (cluster_id=None) is the right answer for "cluster-less Spark — pay only per job." Both are valid; the question's framing of "existing 24/7 cluster" selects EMRStep. `PySparkProcessor` (C) is valid but spins up its own cluster and ignores the existing one.

---

## Q342 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Choose Step Functions Standard vs Express for ML

A team is designing a Step Functions workflow that orchestrates a SageMaker training job (45-minute typical duration) followed by `CreateModel` and `CreateEndpoint`. Which choice is correct?

- A. Standard — Express has a 5-minute max duration and at-least-once semantics that would silently re-run training jobs on worker failure
- B. Express Async — cheapest at scale
- C. Express Sync — needed for synchronous API behavior
- D. Either; the choice is reversible later

**Answer:** A

**Explanation:** Express workflows have a **5-minute max duration** (way below 45-minute training) and **at-least-once semantics** (Async) that may re-run states on worker failure — silently re-running a training job costs real GPU-hours. Standard is **exactly-once** semantics and supports up to 1-year duration with 90-day execution history. The Standard-vs-Express choice is also **immutable** — you cannot change it after creation; you must build a new state machine.

---

## Q343 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize the Distributed-Map Standard-only constraint

A scenario asks: "Process 100,000 S3 objects in parallel through a SageMaker endpoint with up to 1,000 concurrent invocations." Which combination is feasible?

- A. Express workflow with a Distributed Map state and `MaxConcurrency=1000`
- B. Standard workflow with a Distributed Map state (`Mode=DISTRIBUTED`, `ExecutionType=EXPRESS` for children) and `MaxConcurrency=1000`
- C. Express workflow with inline Map (40 concurrent items)
- D. Standard workflow with inline Map and `MaxConcurrency=10000`

**Answer:** B

**Explanation:** **Distributed Map is Standard-only** — Express workflows cannot host a Distributed Map state. Inline Map (C, D) caps at **40 concurrent iterations**, far below 1,000. The canonical Capital One pattern (10,000 ceiling, 256 GB input from S3, child Express executions for cheap fan-out) is the right shape and matches B.

---

## Q344 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply the `.sync` integration-pattern matrix for SageMaker

Which SageMaker API does **NOT** support the `.sync` integration pattern in Step Functions (and instead requires Request/Response or a polling Lambda for completion)?

- A. `CreateTrainingJob`
- B. `CreateHyperParameterTuningJob`
- C. `CreateTransformJob`
- D. `CreateEndpoint`

**Answer:** D

**Explanation:** `CreateEndpoint` (and `CreateEndpointConfig`, `CreateModel`, `UpdateEndpoint`) is **Request/Response only** — `.sync` is not supported. Endpoint creation is asynchronous in SageMaker but lacks an EventBridge "endpoint creation completed" event Step Functions can hook into the same way training emits state changes. Workarounds: a follow-up Lambda that polls `DescribeEndpoint`, or `.waitForTaskToken` with an EventBridge rule on `SageMaker Endpoint Deployment State Change`. Training, tuning, processing, transform, and labeling all support `.sync`.

---

## Q345 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize the Express + `.sync` prohibition

What happens if you author an Express Step Functions workflow with a Task state using ARN `arn:aws:states:::sagemaker:createTrainingJob.sync`?

- A. It runs but ignores the `.sync` suffix
- B. The state machine creation is rejected — Express workflows are limited to **Request/Response** integrations only
- C. It runs in synchronous (at-most-once) mode but with a 5-minute hard cutoff that may abort training
- D. It is allowed only if `wait_for_completion=true` is also set

**Answer:** B

**Explanation:** Express workflows cannot use `.sync` — the combination of 5-minute max duration and in-memory state makes long-poll integrations physically impossible. State machine creation/deployment is rejected. This is the second-most-common Step Functions exam trap (after Distributed Map being Standard-only).

---

## Q346 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Choose between Pipelines, Step Functions, and MWAA

For each scenario, which orchestrator is the canonical AWS-native pick?

- **Scenario 1:** ML-only DAG (Preprocess → Train → Eval → Register), team uses the SageMaker Python SDK, wants Model Registry + Lineage for free.
- **Scenario 2:** Cross-service workflow (Glue ETL → Lambda → SageMaker → SNS), needs Distributed Map fan-out.
- **Scenario 3:** Team already operates 200+ Airflow DAGs on-prem and wants continuity.

- A. (1) Step Functions, (2) Pipelines, (3) Pipelines
- B. (1) SageMaker Pipelines, (2) Step Functions, (3) MWAA
- C. (1) MWAA, (2) Step Functions, (3) Step Functions
- D. (1) Pipelines, (2) MWAA, (3) Step Functions

**Answer:** B

**Explanation:** The canonical decision tree: **ML-only DAG → SageMaker Pipelines** (free orchestration, native Model Registry / Lineage / Studio DAG / SelectiveExecution). **Cross-service or needing Distributed Map → Step Functions**. **Airflow shop or multi-cloud → MWAA**. These three orchestrators are often composed (Step Functions wrapping Pipelines is the most common production hybrid).

---

## Q347 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize MWAA environment-class capacity and cost

A team needs to budget for MWAA running 24/7. They expect to host 30-40 DAGs with bursty concurrent task loads in the dozens. Which environment class is the typical floor, and what is the approximate monthly cost (us-east-1, 2026)?

- A. `mw1.micro` at ~$153/mo — sufficient for any small team
- B. `mw1.small` at ~$350/mo — practical floor for production teams; supports auto-scaling
- C. `mw1.2xlarge` at ~$3,375/mo — required for any production workload
- D. MWAA does not bill by environment; only per-DAG-execution

**Answer:** B

**Explanation:** `mw1.small` (~$350/month at 24/7 hourly) is the practical floor for production teams — supports auto-scaling, 5 concurrent tasks default, 50-DAG capacity. `mw1.micro` (A) does **not** auto-scale (single worker pinned, 3 concurrent tasks) and is unsuitable for bursty loads. `mw1.2xlarge` is over-provisioned for 30-40 DAGs. **MWAA bills hourly even when idle** — there is no scale-to-zero, which is the most consequential cost trap.

---

## Q348 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply Airflow operator best practice in MWAA for SageMaker training

A DAG runs a 4-hour SageMaker training job using `SageMakerTrainingOperator` with `wait_for_completion=True`. The team complains about MWAA worker exhaustion. What is the recommended fix?

- A. Set `deferrable=True` so the worker slot is released and the triggerer polls for completion
- B. Set `wait_for_completion=False` and trust the next DAG run to detect completion
- C. Switch to MWAA's `mw1.2xlarge` class regardless of cost
- D. Run the training job in a Glue job instead

**Answer:** A

**Explanation:** `wait_for_completion=True` is the Airflow equivalent of Step Functions `.sync` — but Airflow holds a worker slot for the entire wait, so a 4-hour training job consumes a worker for 4 hours doing nothing. Setting `deferrable=True` releases the worker and lets the triggerer (Airflow 2.2+) poll instead — equivalent semantics, dramatically lower resource cost. This is the canonical production pattern for long-running SageMaker tasks in MWAA.

---

## Q349 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recall EventBridge's three sub-services

Which statement correctly summarizes the three sub-services sold under the EventBridge brand?

- A. Rules for time-based, Scheduler for events, Pipes for cross-account routing
- B. Rules for event-pattern matching on buses, Scheduler for time-based invocation (cron/rate/at), Pipes for source → filter → enrich → target plumbing on streams/queues
- C. Rules and Pipes are deprecated; only Scheduler is supported
- D. Rules, Scheduler, and Pipes are three names for the same service

**Answer:** B

**Explanation:** EventBridge has three architecturally distinct sub-services: **Rules** (pattern-matched routing on event buses), **Scheduler** (Nov 2022, time-based invocations with timezone/DST, 1M-schedule scale), and **Pipes** (2023, point-to-point source → filter → enrich → target where source is a stream or queue: SQS, Kinesis, DynamoDB Streams, MSK, Kafka, MQ).

---

## Q350 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Choose Scheduler over Rules for timezone-aware scheduling

A SageMaker Pipeline must run every Monday at 02:00 **America/New_York** time, honoring DST transitions. Which is correct?

- A. EventBridge Rule with `ScheduleExpression="cron(0 7 ? * MON *)"` (UTC equivalent) — Rules support DST automatically
- B. EventBridge Scheduler with `ScheduleExpression="cron(0 2 ? * MON *)"` and `ScheduleExpressionTimezone="America/New_York"`
- C. CloudWatch Events scheduled rule with `cron(0 2 ? * MON *)` — local timezone
- D. SageMaker Pipelines' built-in cron field

**Answer:** B

**Explanation:** **Schedule rules are UTC-only** and cannot honor DST. **EventBridge Scheduler** supports 60+ IANA-named timezones via `ScheduleExpressionTimezone` and handles DST natively. SageMaker Pipelines has no built-in cron. The "use Scheduler for any non-UTC schedule" rule is one of the top EventBridge exam traps.

---

## Q351 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Identify the S3-to-EventBridge per-bucket toggle

A team wires up an EventBridge Rule with pattern `{"source": ["aws.s3"], "detail-type": ["Object Created"], ...}` and target = SageMaker Pipeline. They upload a file. Nothing happens. What is the most likely root cause?

- A. The bucket's EventBridge notification is not enabled (Properties → Event notifications → "Send notifications to Amazon EventBridge" is OFF)
- B. EventBridge Rules cannot target SageMaker Pipelines
- C. S3 events route only through SQS, not EventBridge
- D. The rule must be in a custom bus, not the default bus

**Answer:** A

**Explanation:** **S3-to-EventBridge is a per-bucket toggle** and is OFF by default. You must enable "Amazon EventBridge" notifications in the bucket Properties → Event notifications section. The classic exam stem ("you wired the rule but it doesn't fire") nearly always points here. SageMaker Pipelines is a first-class EventBridge target. S3 events do route through EventBridge (when enabled). The default bus receives the events.

---

## Q352 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply the January 2026 EventBridge 1 MB payload bump

In a 2026-dated architecture review, a team wants to include a ~600 KB SHAP attribution dump inline in an EventBridge event. Which statement is correct?

- A. Impossible — EventBridge events are capped at 256 KB; must use S3 claim-check
- B. Allowed — since January 29, 2026 the max event size is 1 MB, though billing is still metered per 64 KB chunk so a 1 MB event costs 16× a 64 KB event
- C. Allowed only on partner buses, not the default bus
- D. Allowed only via API destinations, not Rules

**Answer:** B

**Explanation:** On **January 29, 2026**, AWS bumped the EventBridge max event size from 256 KB to **1 MB** (for `PutEvents`, `PutPartnerEvents`, SQS `SendMessage`, Lambda Invoke). It is automatic — no SDK upgrade, no API version bump. **Billing is still per 64 KB chunk** so a 1 MB event costs 16× a 64 KB one. For low-volume high-value events (drift/SHAP/eval reports) this is fine; high-volume telemetry should still use S3 claim-check.

---

## Q353 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Identify SageMaker event types for MLOps

Which `detail-type` value fires when a Model Registry approval status transitions (e.g., from `PendingManualApproval` to `Approved`)?

- A. `SageMaker Endpoint Deployment State Change`
- B. `SageMaker Model Package State Change`
- C. `SageMaker Training Job State Change`
- D. `aws.sagemaker.modelapproval`

**Answer:** B

**Explanation:** `SageMaker Model Package State Change` (source `aws.sagemaker`) fires on every Model Package state transition, with `detail.ModelApprovalStatus`, `detail.ModelPackageGroupName`, and `detail.ModelPackageVersion` in the payload. This is the event that powers the canonical model-build-to-model-deploy pipeline handoff. Endpoint deployment state changes (A) are a different event. Training state changes (C) are also different. Option D is not a real `detail-type` value.

---

## Q354 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply the canonical drift-to-retrain pattern

In the canonical drift-to-retrain loop, EventBridge sits between which two components, and why doesn't it call SageMaker Pipelines directly on the drift path?

- A. Between Model Monitor and Studio; it does call Pipelines directly
- B. Between a CloudWatch alarm (`aws.cloudwatch`) and a Lambda dispatcher, because the alarm event does not carry the pipeline name/parameters — the Lambda maps "which model drifted" → "which pipeline with which parameters" and calls `StartPipelineExecution`
- C. Between the SageMaker endpoint and the Model Registry; it calls Pipelines directly
- D. Between S3 and CodePipeline; Pipelines is not in this loop

**Answer:** B

**Explanation:** The canonical loop is **Endpoint (DataCapture) → Model Monitor → CloudWatch metric → CloudWatch alarm → EventBridge Rule (source=`aws.cloudwatch`, detail-type=`CloudWatch Alarm State Change`, alarmName prefix=`drift-`) → Lambda dispatcher → `StartPipelineExecution`**. Lambda sits in the middle because the alarm event carries only the alarm name and state — not the pipeline name or parameters — so a dispatcher must parse "which model drifted" (typically encoded in the alarm name) and build the right `PipelineParameters` map before starting the pipeline.

---

## Q355 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize cross-account EventBridge one-hop limit

A central `ml-platform-acct` operates a hub event bus. Local source accounts `PutEvents` to the hub; rules in the hub forward selected events to local target accounts. Which statement is correct?

- A. EventBridge supports unlimited cross-account hops as long as IAM allows
- B. Cross-account routing is **one hop only** — Local → Central → Local is supported, but two-hop chains are not (resource policies on the hub use `aws:PrincipalOrgID`)
- C. Cross-account routing is forbidden by default — only same-account events flow
- D. Cross-account requires AWS Transit Gateway for event traffic

**Answer:** B

**Explanation:** EventBridge cross-account routing is **one-hop only** — the central bus pattern (`Local → Central → Local`) works; two-hop chains do not. Resource policies on the hub bus typically use `aws:PrincipalOrgID` to permit `PutEvents` from any account in the AWS Organization. Same for cross-region.

---

## Q356 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Differentiate Pipes from Lambda event-source mapping

A team uses an SQS queue to deliver messages to **two** downstream destinations: an SNS topic for alerting and a DynamoDB table for audit. They want to "move to Pipes." Why is this a poor fit, and what is the right shape?

- A. Pipes is correct — Pipes natively supports multiple targets
- B. Pipes has exactly **one target**; the right pattern is `SQS → Pipe → Default Event Bus → Rule (two targets: SNS + DynamoDB)` or a Lambda target that fans out
- C. Pipes does not support SQS as a source
- D. Pipes is deprecated; use Lambda event-source mapping with multiple destinations

**Answer:** B

**Explanation:** **Pipes has exactly one target** (source → filter → enrich → target). For multi-target fan-out, route the Pipe into an event bus and let a Rule with multiple targets do the fan-out (Rules support up to 5 targets; beyond that, fan out via SNS). Pipes does consume SQS (and Kinesis, DynamoDB Streams, MSK, Kafka, MQ) — not deprecated.

---

## Q357 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recall EventBridge quotas

Which set is correct for default EventBridge quotas (May 2026)?

- A. 1 MB max event size; 10 entries per `PutEvents`; 100 custom buses per region; 300 rules per bus; 5 targets per rule
- B. 256 KB max event size; 1 entry per `PutEvents`; 50 buses; unlimited rules
- C. 1 MB max event; 100 entries per `PutEvents`; 1,000 buses; 10 targets per rule
- D. No quotas — EventBridge is unlimited

**Answer:** A

**Explanation:** Post-January 2026: 1 MB max event size, 10 `PutEvents` entries per request, 100 custom event buses per region (adjustable), 300 rules per bus (adjustable), **5 targets per rule** (not adjustable — fan out via SNS if you need more). Target retry attempts: 185; max age: 24 hours.

---

## Q358 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Differentiate CodePipeline V1 vs V2

Which set of features is V2-only (not available in V1)?

- A. Source action, Manual approval, SNS notification
- B. Typed pipeline-level variables; trigger filters by branch/path/tag; execution modes (Superseded/Queued/Parallel); conditional stages; stage rollback API
- C. Per-action IAM, S3 source, CodeCommit source
- D. Only the pricing model differs; feature set is identical

**Answer:** B

**Explanation:** **CodePipeline V2** (GA Sept 2023, default in console 2024) added typed pipeline variables, Git trigger filters (branch/file-path/tag includes/excludes), execution modes (SUPERSEDED/QUEUED/PARALLEL), conditional stages (`BeforeEntry`/`OnSuccess`/`OnFailure`), one-click `RollbackStage`, and per-action-execution-minute pricing ($0.002/action-min with 100 action-min free tier). V1 charges flat $1.00/pipeline/month and has none of these.

---

## Q359 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Choose execution mode for the model-deploy pipeline

A regulated org's model-deploy pipeline must guarantee that every approved model package is deployed in order, with full audit traceability — skipping intermediate versions is not allowed. Which execution mode fits?

- A. SUPERSEDED — latest commit wins
- B. QUEUED — first-in, first-out queue (default depth 50); every commit eventually deploys
- C. PARALLEL — executions run independently
- D. SHARDED — distributes across regions

**Answer:** B

**Explanation:** **QUEUED** mode lets every commit/approval flow through the pipeline in order, preserving audit traceability. SUPERSEDED (A) is appropriate for high-velocity dev branches but skips intermediate commits. PARALLEL (C) lets executions run side-by-side and is typically used for PR validation (not deploy). SHARDED (D) is not a real CodePipeline execution mode.

---

## Q360 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply CodeBuild compute type for ML

Which compute type is appropriate for an ML CI job that needs to validate a CUDA layer, export an ONNX model, and run a GPU-bound smoke test?

- A. `BUILD_LAMBDA_10GB`
- B. `BUILD_GENERAL1_SMALL`
- C. `BUILD_GENERAL1_GPU_LARGE` (NVIDIA Tesla, 255 GiB / 32 vCPU)
- D. `BUILD_GENERAL1_2XLARGE` (CPU-only, 72 vCPU)

**Answer:** C

**Explanation:** `BUILD_GENERAL1_GPU_LARGE` is the GPU-equipped EC2 compute type (NVIDIA Tesla) — the right pick for CUDA validation and GPU smoke tests. Lambda compute (A) has no Docker-in-Docker and no GPU. SMALL (B) is 4 GiB/2 vCPU and too small. 2XLARGE (D) has massive CPU but no GPU.

---

## Q361 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply CodeBuild batch builds

A team wants to run unit tests, integration tests, and a security scan **in parallel** within a single CodePipeline Build action. Which batch pattern fits?

- A. `build-list` — parallel distinct tasks
- B. `build-matrix` — Cartesian product of env-var combinations
- C. `build-graph` — DAG of tasks with dependencies
- D. `build-fanout` — split one task into N parallel workers

**Answer:** A

**Explanation:** **`build-list`** runs N parallel distinct tasks — exactly the right shape for "unit + integration + security in parallel." `build-matrix` is for testing across env-var combinations (Python 3.9/3.10/3.11 × Ubuntu/AL2). `build-graph` is for tasks with declared dependencies (lint → unit → package). `build-fanout` shards one task across workers (parallelizing a slow pytest suite).

---

## Q362 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply CodeDeploy predefined Lambda canary configurations

Which CodeDeploy configuration shifts 10% traffic for 15 minutes, then 100%?

- A. `CodeDeployDefault.LambdaCanary10Percent5Minutes`
- B. `CodeDeployDefault.LambdaCanary10Percent15Minutes`
- C. `CodeDeployDefault.LambdaLinear10PercentEvery3Minutes`
- D. `CodeDeployDefault.LambdaAllAtOnce`

**Answer:** B

**Explanation:** The Lambda predefined family is **AllAtOnce + four canary intervals (5/10/15/30 min) + four linear intervals (1/2/3/10 min)** = nine total. `LambdaCanary10Percent15Minutes` shifts 10% for 15 min then jumps to 100%. Linear configurations shift in equal steps (10% every N minutes).

---

## Q363 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize CodeDeploy ECS NLB restriction

An ECS service runs behind a Network Load Balancer. A team wants a 10%-for-15-min canary. Which is correct?

- A. Use `CodeDeployDefault.ECSCanary10Percent15Minutes`
- B. Not supported — ECS services behind an NLB only support `CodeDeployDefault.ECSAllAtOnce`; switch to ALB to enable canary
- C. Use a custom CodeDeploy configuration with `MinimumHealthyHosts`
- D. NLB always supports canary natively; CodeDeploy is not required

**Answer:** B

**Explanation:** ECS services behind an **NLB** support only `ECSAllAtOnce` — NLB health checks are too slow for fractional traffic shifting. Switching to an **ALB** enables the five ECS predefined configurations (AllAtOnce + Canary5/15 min + Linear1/3 min). Note ECS has fewer predefined options than Lambda (5 vs 9) — the missing 10-min/30-min canaries and 2-min/10-min linears are a common exam trap.

---

## Q364 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize that CodeDeploy is NOT used for SageMaker endpoints

A scenario says: "Deploy a new XGBoost model version to a SageMaker real-time endpoint with a 10% canary for 5 minutes, with auto-rollback on a CloudWatch latency alarm." Which service owns the traffic shift?

- A. AWS CodeDeploy with `CodeDeployDefault.LambdaCanary10Percent5Minutes`
- B. SageMaker's native `UpdateEndpoint` with `DeploymentConfig.BlueGreenUpdatePolicy` (CANARY traffic-routing) + `AutoRollbackConfiguration` listing the latency alarm
- C. AWS App Mesh weighted routing
- D. Route 53 weighted records

**Answer:** B

**Explanation:** **CodeDeploy is for Lambda / ECS / EC2 — NOT SageMaker endpoints.** SageMaker has its own deployment safety primitives: `UpdateEndpoint` accepts `DeploymentConfig` with `BlueGreenUpdatePolicy` (traffic routing: ALL_AT_ONCE / CANARY / LINEAR), `RollingUpdatePolicy`, and `AutoRollbackConfiguration` (CloudWatch alarms that auto-rollback if they fire during the deployment window). CodePipeline can orchestrate the update (via a CloudFormation action), but the traffic shifting is executed by the SageMaker control plane. CodeDeploy only enters SageMaker architecture when API Gateway → Lambda sits in front of the endpoint.

---

## Q365 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply CodeArtifact authentication

A CodeBuild project's `buildspec.yml` pre_build phase needs to install Python packages from a private CodeArtifact repository. Which line is the canonical first step?

- A. `aws codeartifact get-authorization-token --domain mycompany --query authorizationToken --output text > /tmp/token`
- B. `aws codeartifact login --tool pip --domain mycompany --domain-owner 111122223333 --repository ml-deps`
- C. `pip config set global.index-url https://pypi.org/simple/`
- D. `aws s3 cp s3://my-bucket/pip.conf ~/.pip/pip.conf`

**Answer:** B

**Explanation:** `aws codeartifact login --tool pip` is the canonical helper — it fetches a short-lived token (max TTL **12 hours**) and writes `~/.pip/pip.conf` pointing at CodeArtifact with the token. The same helper works for `--tool npm`. CodeBuild's service role needs `codeartifact:GetAuthorizationToken`, `codeartifact:GetRepositoryEndpoint`, `codeartifact:ReadFromRepository`, and `sts:GetServiceBearerToken` (the underlying token-issuing API — easy to forget). Option A fetches a token manually but doesn't wire pip to use it.

---

## Q366 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize CodeArtifact upstream/external-connection limits

How many upstream repositories and external connections can a single CodeArtifact repository declare?

- A. Up to 10 upstreams + 1 external connection
- B. Up to 5 upstreams + 5 external connections
- C. Unlimited upstreams + 1 external connection
- D. 1 upstream + 1 external connection

**Answer:** A

**Explanation:** Each CodeArtifact repository can chain to at most **10 upstream repositories** plus exactly **1 external connection** (e.g., `public:pypi`, `public:npmjs`, `public:maven-central`). For deep promotion chains beyond 10 levels, you must flatten the topology or split into multiple domains. Auth tokens are limited to a **12-hour** max TTL.

---

## Q367 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize CodeCommit closed-to-new-customers status

A green-field ML project starts in 2026 on a new AWS account. The team needs Git-based source for CodePipeline. What is the modern AWS recommendation?

- A. Create a new CodeCommit repository — it remains the AWS-native default
- B. Use GitHub (or GitLab/Bitbucket) via **AWS CodeStar Connections** — CodeCommit was closed to new customers on July 25, 2024
- C. Use Bitbucket Server installed on EC2
- D. Use S3 as the Git host

**Answer:** B

**Explanation:** AWS announced on **July 25, 2024** that CodeCommit was closed to new customer onboarding (a partial reversal occurred in November 2025 but the strategic recommendation remains the same). For green-field projects, the modern answer is **GitHub / GitLab / Bitbucket via CodeStar Connections** (formerly named CodeConnections — same service). Distractors that propose creating a new CodeCommit repo are wrong by default for new accounts.

---

## Q368 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply GitHub Actions OIDC sub-claim hardening

A GitHub Actions workflow assumes an AWS IAM role via OIDC. The trust policy currently has `"token.actions.githubusercontent.com:sub": "repo:acme-org/*"`. Why is this unsafe, and what is the correct value?

- A. Safe as-is — wildcard matches are the recommended pattern
- B. Unsafe — *any branch* of *any repo* in the org (including a malicious PR branch) can assume the role; pin to `repo:acme-org/ml-platform:ref:refs/heads/main` or `repo:acme-org/ml-platform:environment:production`
- C. Unsafe — must use long-lived access keys instead of OIDC
- D. Unsafe — must include `aud: github.com` (not `sts.amazonaws.com`)

**Answer:** B

**Explanation:** Without a tight `sub` claim, any branch of any repo in the org can assume the role — including malicious PR branches. The AWS Security blog flags wildcard-subbed OIDC as the #1 OIDC misconfiguration. Always pin to `repo:org/repo:ref:refs/heads/main` (specific branch) or `repo:org/repo:environment:production` (GitHub environment with protection rules). The `aud` claim must be `sts.amazonaws.com` (not `github.com`).

---

## Q369 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply the canonical two-pipeline MLOps shape

In the canonical two-pipeline MLOps reference architecture, what is the link between the **model-build** and **model-deploy** pipelines? (Select TWO)

- A. The Model Registry — the build pipeline registers a Model Package; the deploy pipeline reads it
- B. An EventBridge rule on `SageMaker Model Package State Change` with `ModelApprovalStatus=Approved` that calls `StartPipelineExecution` on the deploy pipeline (with `ModelPackageArn` as a V2 pipeline variable)
- C. The two pipelines share a single CodeBuild project
- D. The build pipeline directly invokes the deploy pipeline via Lambda
- E. They share a single Git repository with branch-based routing

**Answer:** A, B

**Explanation:** The two pipelines are **independent** — separate service roles, separate artifact buckets, separate triggers. Their **only** link is the Model Registry: the build pipeline writes a Model Package; the deploy pipeline reads. The handoff is mediated by an **EventBridge rule** on `SageMaker Model Package State Change` (filtered to `ModelApprovalStatus=Approved`), which calls `StartPipelineExecution` on the deploy pipeline with the approved `ModelPackageArn` as a V2 pipeline variable. Sharing CodeBuild projects (C), direct invocation (D), or shared repos (E) would couple the pipelines and violate the separation.

---

## Q370 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Distinguish CloudFormation change sets from drift detection

A scenario says: "An SRE manually changed an EndpointConfig in the console during an incident. The next scheduled deploy needs to detect and either preserve or codify the change." Which CloudFormation feature applies?

- A. Change set — preview the next deploy before applying
- B. **Drift detection** — compares current live state to the last deployed template (and the 2025 drift-aware change sets do a three-way diff: new + last-deployed + live)
- C. Stack policy — protects resources from update
- D. Rollback triggers — CloudWatch alarms that auto-rollback during the monitoring period

**Answer:** B

**Explanation:** **Change sets** answer "what am I about to do" (dry-run preview of an update). **Drift detection** answers "what has somebody else already done outside CFN" — it scans live state vs. the last deployed template. The 2025 **drift-aware change sets** combine both: a three-way diff (new template + last-deployed template + live state) that flags overwrites of drifted attributes before execution. Stack policy and rollback triggers are different safety primitives.

---

## Q371 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Identify CloudFormation hard limits

Which CloudFormation limit most often forces ML platforms to decompose into nested stacks?

- A. 200 parameters per template
- B. **500 resources per template** (a SageMaker domain + 30 user profiles + Pipelines + Endpoints + IAM + KMS + monitoring schedules adds up shockingly fast)
- C. 60 dynamic references per template
- D. 100 mappings per template

**Answer:** B

**Explanation:** The **500-resource limit** is the most-tested CFN limit. A "logically one stack" ML platform with 1,200 resources cannot be a single physical CFN stack — the workaround is **nested stacks** (parent + child templates in S3) or, in CDK, splitting into multiple stacks within a single Stage. The 1 MB template body limit and 4 KB custom-resource response payload are secondary traps.

---

## Q372 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize CFN StackSets for multi-account ML platforms

A central platform team owns a SageMaker execution role + KMS key + CloudWatch log group + monitoring Lambda that must exist in every account in the `ml-workloads` OU — including auto-deployment when a new account joins. Which feature fits?

- A. CloudFormation StackSets with **service-managed permissions** and automatic deployment to OU members
- B. Multiple independent stacks created manually in each account
- C. SageMaker Projects (which doesn't span accounts)
- D. Terraform Cloud workspaces

**Answer:** A

**Explanation:** **CloudFormation StackSets** with **service-managed permissions** (uses AWS Organizations trusted access — required for automatic deployment to new accounts when they join an OU) is the canonical answer for multi-account, multi-region deployment from one template. Self-managed permissions are for accounts outside an Organization. Caveat: service-managed StackSets do not support templates with macros (including `Transform: AWS::Serverless-2016-10-31`).

---

## Q373 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Distinguish CDK construct levels

Match the construct level to its definition. Which is correct?

- A. L1 = 1:1 with a CFN resource (no abstraction, `Cfn` prefix); L2 = 1:1 with curated defaults and helper methods; L3 = multiple resources composed for a use case (patterns)
- B. L1 = lowest level; L2 = SDK calls; L3 = Terraform export
- C. All three levels are 1:1 with CFN resources; they differ only in language support
- D. L3 is a single CFN resource with high abstraction

**Answer:** A

**Explanation:** **L1** ("CFN resources") map 1:1 with a single CloudFormation resource, no abstraction, `Cfn` prefix (`CfnBucket`, `CfnEndpoint`). **L2** ("curated constructs") still map 1:1 with a CFN resource but add sensible defaults (e.g., `Bucket` has encryption by default), helper methods (`bucket.grantRead(role)`), and typed properties. **L3** ("patterns") compose multiple resources for a use case (e.g., `ApplicationLoadBalancedFargateService`). SageMaker is **L1-heavy** in `aws-cdk-lib/aws-sagemaker`; L2 lives in `@aws-cdk/aws-sagemaker-alpha` (experimental).

---

## Q374 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize CDK Pipelines self-mutation

What does "self-mutating" mean for CDK Pipelines (`pipelines.CodePipeline`)?

- A. The pipeline rebuilds its Docker base images on every run
- B. On every run, the pipeline runs `cdk synth`, compares to the deployed pipeline, and if different **deploys the new pipeline first** before re-invoking itself to run application stages — eliminating manual `cdk deploy` after the first bootstrap
- C. The pipeline encrypts itself on every run
- D. The pipeline mutates the IAM roles of all target accounts

**Answer:** B

**Explanation:** CDK Pipelines' killer feature is the `SelfMutate` stage: every run synthesizes the pipeline's own CFN template, diffs against deployed, and updates the pipeline itself before running application stages with the new definition. This removes the chicken-and-egg of "who deploys the pipeline that deploys things" — after the initial `cdk deploy`, all pipeline changes flow through Git merges. Gotchas: synth must be deterministic, the pipeline must live in its own stack, and ephemeral test stages need explicit cleanup.

---

## Q375 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Position AWS SAM relative to CloudFormation

Which statement about AWS SAM is correct?

- A. SAM is a separate IaC engine that replaces CloudFormation
- B. SAM is a **CloudFormation transform (macro)** `AWS::Serverless-2016-10-31` plus a CLI (`sam build`, `sam local invoke`, `sam deploy`); the transform expands shortened serverless syntax into raw CFN resources at deploy time
- C. SAM is a Python framework that compiles to Terraform HCL
- D. SAM only works for Lambda — it cannot use any other CFN resource types

**Answer:** B

**Explanation:** SAM is **not** a separate IaC tool — it is a CFN macro plus a CLI. The transform expands `AWS::Serverless::Function`, `AWS::Serverless::Api`, etc., into native CFN at deploy time. SAM is a **subset** of CFN — anything in SAM is doable in pure CFN; the reverse is not true. SAM templates can mix `AWS::Serverless::*` with arbitrary native CFN resources. Important caveat: **service-managed StackSets cannot use SAM** because they don't support macros.

---

## Q376 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Choose CDK vs Terraform for an MLOps platform

A scenario describes an AWS-only Python-first ML team that wants unit-testable infrastructure with built-in CI/CD self-mutation, latest AWS feature support at GA, and SageMaker Projects integration. Which IaC is the canonical pick?

- A. Terraform — multi-cloud is the default in 2026
- B. **AWS CDK with CDK Pipelines** — AWS-native, real programming language (Python), L1s ship the day a service does, CDK Pipelines self-mutation, integrates with SageMaker Projects (which is CFN-based)
- C. Pulumi — language-first, but not on AWS
- D. AWS SAM — serverless-only

**Answer:** B

**Explanation:** Decision axes: **CDK** wins on AWS-only, developer-led Python/TypeScript teams that want unit tests, fast new-feature parity (L1s ship at GA), CDK Pipelines self-mutation, and tight integration with Service Catalog / SageMaker Projects (both CFN-based — you cannot write a SageMaker Project template in Terraform). **Terraform** wins on multi-cloud, hybrid (AWS + Azure + Snowflake + Datadog + Okta), large existing module libraries, and regulated environments with required third-party scanners (Checkov, tfsec). SAM (D) handles serverless only.

---

## Q377 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Recognize SageMaker Projects as composite scaffolding

What does a SageMaker Project provision, and what is it NOT?

- A. A runtime ML pipeline that replaces SageMaker Pipelines
- B. Scaffolding: a **CloudFormation** template that lays down infrastructure + a **CodePipeline** (or Jenkins) for CI/CD + one or more **SageMaker Pipelines** for ML steps + a Model Package Group + EventBridge rules — Projects is **not** a runtime; Pipelines is standalone and can exist without Projects
- C. A managed alternative to Step Functions
- D. A drag-and-drop UI builder for Lambda functions

**Answer:** B

**Explanation:** A Project is a Studio-managed bundle of **CFN + CodePipeline + SageMaker Pipelines** plus IAM/S3/repositories. The common trap is conflating Projects with Pipelines — Pipelines are standalone entities ("You can create, update, and run pipelines directly within a notebook by using the SageMaker Python SDK without using a SageMaker AI project," per AWS docs). Projects is scaffolding **around** Pipelines.

---

## Q378 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Apply the SageMaker Projects CodeCommit retirement

A team selecting a SageMaker Project template in 2025 sees only third-party Git options. Why?

- A. AWS removed all CFN-based templates
- B. Per AWS docs: "Effective **September 9, 2024**, project templates that use the AWS CodeCommit repository are no longer supported. For new projects, select from the available project templates that use third-party Git repositories" (GitHub, GitHub Enterprise, Bitbucket, GitLab) via **CodeStar Connections / CodeConnections**
- C. CodeCommit-backed templates require AWS Premium Support
- D. CodeCommit-backed templates were renamed but still available

**Answer:** B

**Explanation:** Per AWS docs (verbatim): SageMaker Project templates that use CodeCommit have been retired effective September 9, 2024. New Projects use **GitHub / GitHub Enterprise / Bitbucket / GitLab** via **AWS CodeStar Connections** (also called **AWS CodeConnections** — same service, renamed in 2024). This is the most testable single fact about SageMaker Projects in 2025-2026. The broader 2025 direction also includes **S3-based templates** replacing the heavier Service-Catalog model.

---

## Q379 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Choose between Pipelines step caching and SelectiveExecution

A team iterates on `evaluate.py` 15 times per day; Processing (40 min) and Training (20 min) do **not** change. Which mechanism is the **simpler, implicit** answer for cost savings during iteration?

- A. SelectiveExecution — explicit list of steps to re-run from a pointed-at prior execution
- B. Step caching with `CacheConfig(enable_caching=True, expire_after="P30D")` on Processing and Training — signature-based reuse, implicit
- C. ParallelismConfiguration tuning
- D. Manually call `pipeline.start()` with `skip_steps=[...]`

**Answer:** B

**Explanation:** **Caching is implicit, signature-based** — same image URI + same input S3 URIs (and ETags) + same instance type/count + same hyperparameters + same entry-point code (SHA-equivalent) → cache hit. It is the cheapest answer to express for iterative development where everything except the script changes. **SelectiveExecution** is more deterministic but requires you to point at a prior execution ARN and list the steps explicitly — better for "we changed eval logic; re-run from eval onward" than for "we re-run everything 20 times a day." Option D is not a real parameter.

---

## Q380 — Domain 3: Deployment and Orchestration of ML Workflows
**Objective:** Integrate the full Part H stack — multi-step

A regulated org needs the following: (1) weekly retraining at 02:00 New York time honoring DST; (2) Model Monitor drift alarms that trigger ad-hoc retraining; (3) auto-deploy to a staging account via CodePipeline V2 on Model Registry approval, with manual approval before prod; (4) blue/green CANARY 10% / 5-minute traffic shift on the prod endpoint with auto-rollback on a latency alarm. Which combination is correct? (Select TWO that are CORRECT statements)

- A. (1) EventBridge Scheduler with `ScheduleExpressionTimezone="America/New_York"` invoking `arn:aws:scheduler:::aws-sdk:sagemaker:startPipelineExecution`; (2) Model Monitor → CloudWatch alarm → EventBridge Rule → Lambda → `StartPipelineExecution`
- B. (3) CodePipeline V2 with QUEUED execution mode + V2 pipeline variable `ModelPackageArn` from the EventBridge rule on `SageMaker Model Package State Change` (Approved)
- C. (4) AWS CodeDeploy with `LambdaCanary10Percent5Minutes` for the SageMaker endpoint
- D. (1) An EventBridge schedule rule with `cron(0 7 ? * SUN *)` UTC — Rules support DST automatically
- E. (2) EventBridge directly targets the SageMaker Pipeline; no Lambda needed because the CloudWatch alarm event carries the pipeline name and parameters

**Answer:** A, B

**Explanation:** **A is correct** — Scheduler with `ScheduleExpressionTimezone` is the canonical timezone/DST-aware scheduler, and the drift loop routes alarm → EventBridge → **Lambda dispatcher** → `StartPipelineExecution` because the alarm event does not carry the pipeline name. **B is correct** — V2 QUEUED + pipeline variable from the EventBridge rule on `SageMaker Model Package State Change` is the canonical model-deploy pipeline shape. **C is wrong** — CodeDeploy is NOT used for SageMaker endpoints; the right answer is SageMaker's native `UpdateEndpoint` with `DeploymentConfig.BlueGreenUpdatePolicy` (CANARY) + `AutoRollbackConfiguration`. **D is wrong** — schedule rules are UTC-only and do not handle DST. **E is wrong** — the alarm event carries only the alarm name/state, not the pipeline name; Lambda must dispatch.

---

*End of Domain 3 (Part H, Half B) practice question set.*

---

# Domain 4 — ML Solution Monitoring, Maintenance, and Security (24%)

# AWS Certified Machine Learning Engineer — Associate (MLA-C01)
# Practice Question Bank — Domain 4 (Part A): Monitoring, Drift, Observability, Registry, A/B Testing

> **Scope:** 60 exam-realistic questions (Q381–Q440) covering the first half of Domain 4 of the MLA-C01 blueprint — SageMaker Model Monitor, drift theory, CloudWatch/X-Ray/CloudTrail observability, SageMaker Model Registry / Model Cards / Lineage, and A/B + Shadow variant testing.
>
> **Source chapters (Part I):**
> - `48_model_monitor.md` — Model Monitor (Data Quality, Model Quality, Bias Drift, Feature Attribution Drift)
> - `49_drift_fundamentals.md` — Drift theory (covariate / label / concept), detection statistics, retraining strategies
> - `50_cloudwatch_xray_cloudtrail.md` — CloudWatch Metrics/Logs/Alarms, X-Ray (ADOT migration), CloudTrail (Lake sunset)
> - `51_registry_cards_lineage.md` — Model Package Group / Version, Model Cards, Lineage Tracking, Managed MLflow
> - `52_ab_shadow_testing.md` — Production Variants, Shadow Variants, statistical testing, OEC/guardrails
>
> **Format:** Single-answer A–D unless prefixed `(Select TWO)` or `(Select THREE)`. Same parseable layout as the Topic 9a bank.

---

## Q381 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Choose the correct Model Monitor type for a given failure mode

A SageMaker real-time endpoint hosts a binary classifier. The team observes that the **input feature distributions look identical to the training set** (KS tests pass on every feature), but **business metrics have degraded sharply** and ground-truth labels confirm accuracy fell from 0.91 to 0.74. Which Model Monitor type is the *primary* tool to detect this failure?

- A. Data Quality monitor — it covers all distributional changes including label shift
- B. Model Quality monitor — only it ingests ground-truth labels and computes accuracy/AUC/F1 against fresh outcomes
- C. Bias Drift monitor — degradation always implies a fairness violation
- D. Feature Attribution Drift monitor — SHAP NDCG@k will catch it before the labels arrive

**Answer:** B

**Explanation:** The pattern (P(X) unchanged, P(Y|X) changed) is classic **concept drift**, which Data Quality cannot see — it only compares input distributions to a baseline. Model Quality is the only monitor type that **requires ground-truth ingestion** (via the `merge_job` joining captured inferences on `InferenceId` to labels) and surfaces ProblemType-specific metrics (accuracy, AUC, F1 for binary; RMSE/MAE/MSE for regression). Bias Drift uses Clarify post-training metrics and is about subgroup parity, not overall accuracy. Attribution Drift is a *leading* indicator but cannot replace true label-based metrics.

---

## Q382 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recall the 4 Model Monitor MonitoringType enum values

Which of the following is **NOT** one of the four `MonitoringType` enum values supported by SageMaker Model Monitor?

- A. `DataQuality`
- B. `ModelQuality`
- C. `ModelBias`
- D. `ConceptDrift`

**Answer:** D

**Explanation:** The four valid enum values are `DataQuality`, `ModelQuality`, `ModelBias` (bias drift via Clarify post-training metrics), and `ModelExplainability` (feature-attribution drift via SHAP). "ConceptDrift" is a drift *theory* term — concept drift is detected by the **Model Quality** monitor (which uses labels), not by a separately-named monitor type.

---

## Q383 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Identify Model Monitor baseline artifact files

A Model Monitor baselining job has just succeeded. Which two JSON artifacts are written to S3 and used by every subsequent monitoring execution? **(Select TWO)**

- A. `statistics.json` — summary stats per feature (mean, stddev, count, distinct, KLL sketch)
- B. `constraints.json` — thresholds & schema (allowed types, completeness, distance metrics)
- C. `predictions.json` — captured inference responses
- D. `lineage.json` — auto-generated lineage entities
- E. `monitor_schedule.json` — the cron schedule definition

**Answer:** A, B

**Explanation:** Baselining produces exactly two artifacts: `statistics.json` (per-feature summary stats built via Deequ + KLL sketches) and `constraints.json` (thresholds the monitoring execution will check). When a monitoring run finds violations, it writes a third file — `constraint_violations.json` — but this is an *output* of execution, not a baseline artifact. The endpoint itself produces JSONL capture files via `DataCaptureConfig`; those are not baseline artifacts.

---

## Q384 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Trace the canonical Model Monitor → retraining loop

Order the components of the canonical drift-triggered retraining loop on AWS:

1. SageMaker Pipelines retrain job
2. EventBridge rule on the alarm state-change event
3. CloudWatch alarm on `feature_baseline_drift_<feature>`
4. Model Monitor processing job emits CloudWatch metric
5. Endpoint with `DataCaptureConfig` enabled

- A. 5 → 4 → 3 → 2 → 1
- B. 5 → 3 → 4 → 1 → 2
- C. 4 → 5 → 3 → 2 → 1
- D. 5 → 4 → 2 → 3 → 1

**Answer:** A

**Explanation:** The capture-first chain is: endpoint with DataCaptureConfig (5) → Model Monitor schedule runs and emits a CloudWatch metric to the `aws/sagemaker/Endpoints/data-metrics` namespace (4) → CloudWatch alarm trips when, e.g., `feature_baseline_drift > 0.1` for two consecutive periods (3) → EventBridge rule matches the `ALARM` state-change (2) → triggers a SageMaker Pipelines retrain (1). A production-grade loop adds a **human-approval gate**, a **fresh-labels check**, a **regression test against a holdout**, and a **circuit breaker** so consecutive trips don't deploy a worse model.

---

## Q385 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Distinguish Data Quality from Model Quality monitors

Which statement is TRUE about the Data Quality monitor?

- A. It requires the customer to ingest ground-truth labels via a `MergeJob`
- B. It detects concept drift even if input features are unchanged
- C. It compares captured input feature distributions to a baseline using `linf_simple` and `chisquare` by default and is sufficient to catch **covariate shift**
- D. Its CloudWatch namespace is `aws/sagemaker/Endpoints/model-metrics`

**Answer:** C

**Explanation:** Data Quality only sees inputs — it cannot detect concept drift (which is a change in P(Y|X) with P(X) unchanged). It does NOT require labels (that's Model Quality's MergeJob requirement). Its CloudWatch namespace is `aws/sagemaker/Endpoints/data-metrics` (Model Quality lives under `.../model-metrics`). The default constraints are `linf_simple` for numeric distributional drift and `chisquare` for categorical.

---

## Q386 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Identify the MergeJob mechanics for Model Quality

The Model Quality monitor needs to join captured inferences with ground-truth outcomes. Which configuration is required?

- A. The endpoint must include a custom HTTP header `X-Amzn-SageMaker-InferenceId` and labels must be written to S3 with the same `inferenceId` field; the monitor's MergeJob then joins on that key before computing metrics
- B. Ground-truth labels must be POSTed back to the endpoint within 60 seconds; no separate merge is needed
- C. Labels must be embedded inside `DataCaptureConfig` JSONL records before they reach S3
- D. The MergeJob auto-discovers labels in the Feature Store via primary key

**Answer:** A

**Explanation:** Each invocation generates a unique `InferenceId` (sent by the client in the `X-Amzn-SageMaker-InferenceId` header, or auto-generated by SageMaker). When the team later writes the actual label to S3 keyed by the same `InferenceId`, Model Monitor's **MergeJob** step joins capture + labels on this key, producing the labeled record set on which accuracy/AUC/F1/RMSE etc. are computed. There is no real-time label POST, no `DataCaptureConfig` label embedding, and no Feature Store auto-discovery.

---

## Q387 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Apply the EEOC 4/5ths rule via Bias Drift

A Bias Drift monitor computes Disparate Impact (DI) hourly. The team wants an alarm only when the model fails the **EEOC 4/5ths rule**. Which alarm condition is correct?

- A. `DI > 1.0` for any period
- B. `DI ∉ [0.80, 1.25]` for two consecutive periods
- C. `|DPPL| > 0.50` for any period
- D. `DI < 0.5` for one period

**Answer:** B

**Explanation:** The U.S. EEOC's **four-fifths rule** treats a selection-rate ratio below 0.80 (or, symmetrically, above 1.25) between protected groups as a prima facie indicator of disparate impact. SageMaker Clarify computes DI as `selection_rate_unprivileged / selection_rate_privileged`, so the no-bias band is `[0.80, 1.25]`. `|DPPL| > 0.10` is a common secondary threshold (Demographic Parity in Predicted Labels), but the 4/5ths rule is specifically about DI.

---

## Q388 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recognize Feature Attribution Drift as a leading indicator

A team wants the earliest possible warning that the model's *decision logic* is changing, even before labels are available and before raw feature distributions move. Which monitor is the best leading indicator?

- A. Data Quality — KS test on every feature
- B. Model Quality — accuracy and AUC
- C. Feature Attribution Drift — SHAP attribution rank using NDCG@k
- D. Bias Drift — DPPL over time

**Answer:** C

**Explanation:** Feature Attribution Drift uses SageMaker Clarify to compute SHAP values online and compares the **ranked importance** of features to the baseline using a **Normalized Discounted Cumulative Gain (NDCG@k)** score. Production alarm: `NDCG < 0.90`. Because attribution rank can shift before raw feature distributions visibly move and well before labels are available, it is the canonical **leading indicator** of model behavior change.

---

## Q389 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Compute the 4 CloudWatch namespaces

Match the Model Monitor type to its CloudWatch metrics namespace.

- A. Data Quality → `aws/sagemaker/Endpoints/data-metrics`; Model Quality → `model-metrics`; Bias Drift → `bias-drift-metrics`; Attribution Drift → `feature-attribution-drift-metrics`
- B. All monitors share `aws/sagemaker/ModelMonitor`
- C. Data Quality → `data-metrics`; Model Quality → `quality-metrics`; Bias → `clarify-metrics`; Attribution → `shap-metrics`
- D. They all write to `AWS/SageMaker` regardless of type

**Answer:** A

**Explanation:** Each of the four monitor types publishes to a dedicated namespace under `aws/sagemaker/Endpoints/`: `data-metrics`, `model-metrics`, `bias-drift-metrics`, and `feature-attribution-drift-metrics`. Dimensions always include `Endpoint` and `MonitoringSchedule`. Knowing the namespace exactly is required to wire CloudWatch alarms.

---

## Q390 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Use cron expressions in `CreateMonitoringSchedule`

A team wants a Data Quality monitor that runs **at the top of every hour**. Which `ScheduleExpression` is valid for `CreateMonitoringSchedule`?

- A. `cron(0 * ? * * *)`
- B. `rate(1 hour)`
- C. `cron(0 0/1 * * ? *)`
- D. Both A and C are valid 6-field AWS cron expressions; B is also accepted

**Answer:** D

**Explanation:** `CreateMonitoringSchedule` accepts AWS-style 6-field cron expressions and `rate(...)` expressions. `cron(0 * ? * * *)` and `cron(0 0/1 * * ? *)` are equivalent ways of saying "every hour on the hour"; `rate(1 hour)` is also accepted. The minimum supported frequency for Model Monitor is hourly — sub-hour cron values are silently rounded up.

---

## Q391 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Production threshold cheat-sheet

Which set of alarm thresholds matches the *production defaults* taught in Chapter 48?

- A. `feature_baseline_drift > 0.1` for 2 periods; `accuracy < 0.85`; `|DPPL| > 0.10`; `DI ∉ [0.80, 1.25]`; NDCG `< 0.90`
- B. `feature_baseline_drift > 0.5` for 1 period; `accuracy < 0.5`; `|DPPL| > 0.30`; `DI ∉ [0.5, 2.0]`; NDCG `< 0.7`
- C. KL `> 0.05`; F1 `< 0.95`; `|DPPL| > 0.05`; `DI > 1.0`; NDCG `> 0.99`
- D. PSI `> 0.5`; AUC `< 0.5`; `|DPPL| > 0.20`; DI `< 0.5`; NDCG `< 0.80`

**Answer:** A

**Explanation:** The Chapter 48 production cheat-sheet pairs covariate-shift trigger `feature_baseline_drift > 0.1` over 2 consecutive periods (to reduce single-period noise) with `accuracy < 0.85` (model quality), `|DPPL| > 0.10` (parity drift), the EEOC band `DI ∈ [0.80, 1.25]` (bias), and `NDCG < 0.90` (attribution drift leading indicator).

---

## Q392 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Model Monitor cost model

A startup runs four monitors (Data Quality, Model Quality, Bias Drift, Attribution Drift) on a single endpoint. Each monitor runs **hourly**. What is the cost implication in the first month?

- A. The first **30 monitor-hours per month per account are free**, then each schedule billed at standard SageMaker Processing rates by instance type/size — 4 monitors × 24 h × 30 days = 2880 monitor-hours billable beyond the free tier
- B. Model Monitor is always free; you only pay for CloudWatch
- C. Each monitor has its own 30-hour free tier (so 120 free hours)
- D. Monitors are billed as endpoint hours, not processing-job hours

**Answer:** A

**Explanation:** Model Monitor gives **30 free monitor-hours per month per account** (not per monitor). Beyond that, each scheduled run is a SageMaker Processing Job billed at the instance rate (often `ml.m5.xlarge`). Running 4 hourly monitors on one endpoint consumes 4×24×30 = 2880 monitor-hours/month — only the first 30 are free. Customers typically batch monitors to daily or use a single monitor type to control cost.

---

## Q393 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Identify the drift type taxonomy

Match each drift type to its mathematical definition. **(Select THREE)**

- A. Covariate shift = P(X) changes, P(Y|X) stable
- B. Label shift = P(Y) changes, P(X|Y) stable
- C. Concept drift = P(Y|X) changes — the input→output relationship itself moved
- D. Concept drift = P(X) changes — same as covariate shift
- E. Label shift = P(X) changes — same as covariate shift

**Answer:** A, B, C

**Explanation:** The three canonical drift types are: **covariate shift** (P(X) shifts; classic example: input feature distribution moves), **label shift / prior probability shift** (the marginal P(Y) changes — e.g., fraud rate goes from 1% to 5%), and **concept drift** (the conditional P(Y|X) itself changes — the world rewires, like Covid changing what "normal" purchasing looks like). Confusing concept drift with covariate shift (D) is the most common exam trap.

---

## Q394 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** PSI banking thresholds

A risk analyst computes Population Stability Index (PSI) on a credit feature and gets 0.27. Per the Basel/IFRS 9 banking convention, how should they react?

- A. PSI < 0.10 — no change; investigate later
- B. 0.10 ≤ PSI < 0.25 — small drift, monitor
- C. **0.25 ≤ PSI < 0.50 — significant drift, investigate and likely retrain**
- D. PSI ≥ 0.50 — major drift, immediate retrain

**Answer:** C

**Explanation:** The de-facto banking traffic-light: **PSI < 0.10 = stable; 0.10–0.25 = small drift (watch); 0.25–0.50 = significant drift (investigate / retrain); > 0.50 = major drift (immediate action)**. PSI 0.27 falls in the significant band. PSI is closely related to symmetric KL divergence and is the standard regulatory drift metric in Basel/IFRS 9 credit modelling.

---

## Q395 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Identify the default non-parametric two-sample test for drift on continuous features

For continuous features without distributional assumptions, the textbook default two-sample drift test is:

- A. Chi-squared test
- B. Anderson-Darling test
- C. **Kolmogorov-Smirnov (KS) test** — non-parametric, compares empirical CDFs, two-sample default
- D. Student's t-test

**Answer:** C

**Explanation:** The **two-sample KS test** is the canonical non-parametric default for detecting distributional drift in continuous features — it compares empirical CDFs and produces the supremum distance D-statistic plus a p-value, with no normality assumption. Chi-squared is for categorical features; Anderson-Darling and Cramér-von Mises are alternative continuous tests; a t-test only checks mean shifts (not full distribution).

---

## Q396 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** KL divergence formula

The Kullback-Leibler divergence of distribution Q from reference P is defined as:

- A. `D_KL(P||Q) = Σ P(x) log(P(x)/Q(x))`
- B. `D_KL(P||Q) = Σ Q(x) log(Q(x)/P(x))`
- C. `D_KL(P||Q) = ½[Σ P(x) log(P(x)/Q(x)) + Σ Q(x) log(Q(x)/P(x))]`
- D. `D_KL(P||Q) = Σ (P(x) − Q(x))²`

**Answer:** A

**Explanation:** KL divergence is **asymmetric** and defined as `Σ P(x) log(P(x)/Q(x))`. Option C is the **symmetric Jensen-Shannon divergence** (an average of the two KL directions over the mixture). Option D is closer to Hellinger / squared L2. KL goes to infinity if Q has zero mass where P has support, which is why Jensen-Shannon / PSI / Wasserstein are often preferred in production.

---

## Q397 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Map drift types to Model Monitor types

Match each drift type to the Model Monitor that *primarily* detects it.

- A. Covariate shift → Data Quality; label shift + concept drift → Model Quality; bias + attribution drift → Clarify (Bias Drift + Attribution Drift monitors)
- B. All drift detected by Data Quality
- C. Covariate shift → Model Quality; concept drift → Data Quality
- D. Label shift → Bias Drift; concept drift → Attribution Drift

**Answer:** A

**Explanation:** Data Quality sees only inputs (covariate). Model Quality sees the labeled join and is the only monitor that catches concept drift (P(Y|X)) and label shift effects on accuracy. The two Clarify-based monitors — Bias Drift and Feature Attribution Drift — handle subgroup parity and explanation-rank drift respectively. The map is essential for picking the right monitor type on the exam.

---

## Q398 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Drift detection anti-patterns

A team runs KS-tests independently on **180 features** every hour with α = 0.05. After a week they have an "alarm fatigue" problem with dozens of false alarms per day. Which two corrections directly address the issue? **(Select TWO)**

- A. Apply **Bonferroni correction** (α / m) or **Benjamini-Hochberg FDR control**
- B. Increase the test window so each comparison has more samples
- C. Switch from KS to a chi-squared test
- D. Apply a single composite alarm with `ALARM ≥ 5` of the per-feature alarms tripping
- E. Disable monitoring entirely

**Answer:** A, D

**Explanation:** This is the **multiple-testing problem** — 180 simultaneous tests at α = 0.05 yield ~9 expected false positives per run, hundreds per day. Two correct fixes: (A) per-test correction (Bonferroni divides α by m, or BH controls False Discovery Rate) and (D) require **k-of-n** correlated features to fire via a CloudWatch *composite* alarm. Larger window helps power but does not fix the multiplicity; changing test family doesn't either.

---

## Q399 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Drift detection — Wasserstein vs KL

Why might a team prefer **Wasserstein (Earth Mover's) distance** over KL divergence for production drift monitoring?

- A. Wasserstein is bounded by 1; KL is unbounded
- B. **Wasserstein is finite even when Q has zero mass where P has support** (KL goes to infinity), and it's symmetric and considers the metric of the support
- C. Wasserstein requires fewer samples than KL
- D. Wasserstein only works on categorical features

**Answer:** B

**Explanation:** KL divergence blows up to infinity whenever Q assigns zero probability to a region where P has positive mass — that breaks production monitoring under sparse data. Wasserstein (also called Earth Mover's Distance) is **finite for any pair of distributions on a common space**, symmetric, and respects the geometry of the support (so a small shift "looks" small). This is why Wasserstein and PSI tend to be more stable in real-world monitoring than raw KL.

---

## Q400 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Retraining strategies

A demand-forecasting model began drifting after a sudden change in user behavior (think Covid lockdowns). Which retraining strategy is **most appropriate** when drift is *unpredictable* and labels stream in within hours?

- A. Scheduled retraining every Sunday — predictable cost
- B. **Drift-triggered retraining** — pipeline kicked off by a CloudWatch alarm wired to EventBridge
- C. Performance-triggered retraining only — wait for accuracy to fall below threshold
- D. Champion/challenger only — never replace champion automatically

**Answer:** B

**Explanation:** When drift is unpredictable but labels arrive quickly, **drift-triggered retraining** wins because it reacts to the actual distributional event rather than waiting for a clock or a long performance lag. Scheduled retraining wastes compute when stable and is too slow when shocked. Performance-triggered is reactive — accuracy may have to drop and recover labels first. Champion/challenger is a deployment pattern, not a trigger. Mature stacks combine drift-triggered + performance-triggered + a human approval gate (see Ch 48's canonical retraining loop).

---

## Q401 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Covid-era war story — interpret a 4× RMSE event

In March 2020 a New York City taxi-demand DeepAR model saw RMSE rise from baseline 1× to ~4× in a single week even though feature inputs (hour-of-day, weather) looked normal. The most accurate classification of this event is:

- A. **Concept drift** — the relationship between features and target (P(Y|X)) changed; lockdowns broke the historical demand-feature mapping
- B. Pure covariate shift — the input feature distributions all moved sharply
- C. Data quality bug — must be a pipeline error
- D. Label shift — the underlying P(Y) shifted but features stayed identical

**Answer:** A

**Explanation:** Inputs were stable (hours, weather still arrived normally) but **the response curve itself collapsed** — lockdown shifted the relationship between weekday/weather and ride demand. That is the textbook **concept drift** signature. This is the canonical war story that motivates: (1) always run Model Quality monitor with ground-truth, (2) treat attribution drift as a leading indicator, and (3) keep retraining pipelines warm.

---

## Q402 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Avoid drift-monitoring anti-patterns

Which of the following is an anti-pattern when designing a drift-monitoring system? **(Select TWO)**

- A. Using only a **3-minute monitoring window** for an hourly endpoint with <100 invocations
- B. Computing baseline statistics each release and **redeploying simultaneously** so the constraints.json matches the deployed model
- C. **Baseline-without-redeploy** — refreshing the baseline against current traffic to silence alarms without retraining the model
- D. Using composite alarms to require multiple correlated features to fire

**Answer:** A, C

**Explanation:** **Small windows** create huge statistical noise — KS p-values fluctuate randomly. **Baseline-without-redeploy** is one of the seven classic anti-patterns: refreshing the baseline against drifted production traffic permanently silences the alarm without fixing anything, hiding the drift. The remaining anti-patterns from Ch 49 include: multiple-testing without correction, all-correlated-features firing, ignoring seasonality, ignoring late labels, and double-thresholding. Options B and D are *good* practices.

---

## Q403 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** CloudWatch metric statistics

A team alarms on the **p99** of `ModelLatency`. Which CloudWatch concept does p99 represent?

- A. A dimension
- B. A namespace
- C. **An extended (percentile) statistic** applied at the alarm or graph level
- D. A metric

**Answer:** C

**Explanation:** `ModelLatency` is a *metric*; `Endpoint` and `VariantName` are *dimensions*; `aws/sagemaker/Endpoints` is the *namespace*. p50/p90/p99 are **extended statistics** (percentiles) applied when reading the metric data — not separate metrics. Percentiles require enough sample data points and are not available with sparse metrics.

---

## Q404 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** CloudWatch composite alarms

A team needs an alarm that triggers when (`ModelLatency` p99 > 200 ms) AND (`Invocation5XXErrors` > 0) AND the on-call has not snoozed the alert. Which CloudWatch feature meets all three needs?

- A. Anomaly detection band
- B. Single-metric alarm with multiple datapoints
- C. **Composite alarm with AND, NOT logic, and an ActionsSuppressor**
- D. Subscription filter on the application log

**Answer:** C

**Explanation:** **Composite alarms** combine other alarms with `AND`, `OR`, `NOT` boolean logic and accept an `ActionsSuppressor` (another alarm whose ALARM state suppresses notifications — the on-call snooze pattern). Single-metric alarms can't span metrics; anomaly detection is a different paradigm; subscription filters are about routing log data, not alarming.

---

## Q405 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Anomaly detection alarms

A team owns a metric that has **strong daily/weekly seasonality**. Hard thresholds keep producing false positives at peak times and false negatives at trough times. Which CloudWatch feature directly addresses this?

- A. Composite alarms
- B. **Anomaly Detection alarms** — auto-learn the seasonal baseline and alarm on deviation from the band
- C. Logs Insights queries
- D. Subscription filters

**Answer:** B

**Explanation:** **CloudWatch Anomaly Detection** trains a model on up to two weeks of metric history, learns seasonality (hourly/daily/weekly), and exposes an expected band; alarms fire when the metric leaves the band. This avoids brittle hard thresholds for traffic-driven metrics like `Invocations` or daily click-through rate. Composite alarms combine binary alarms; they don't infer seasonality.

---

## Q406 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** CloudWatch Logs retention and Insights

Pick the TRUE statement about CloudWatch Logs.

- A. Default retention is 30 days
- B. **Retention is configurable from 1 day to 10 years to "Never expire"**
- C. Logs Insights is bundled with Logs and free up to 1 GB scanned/day
- D. KMS encryption is enabled by default

**Answer:** B

**Explanation:** Default retention is **Never expire** unless explicitly set — a common bill shock. Retention is configurable from **1 day to 10 years**. **CloudWatch Logs Insights** is a paid query language ($0.005/GB scanned) — not free. KMS encryption is opt-in per log group. Logs ingestion is $0.50/GB ingested, storage $0.03/GB-mo (numbers worth knowing for cost questions).

---

## Q407 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Embedded Metric Format (EMF) — when to use it

A Lambda function emits 12 different custom metrics per invocation with high-cardinality dimensions (user_id). The team wants to avoid the cost and rate limits of `PutMetricData`. Which approach is most cost-effective and idiomatic?

- A. Call `PutMetricData` once per invocation with all 12 metric data points
- B. Emit Embedded Metric Format (EMF) JSON to stdout/log group; CloudWatch extracts metrics asynchronously from logs — no PutMetricData calls, only log ingestion charges
- C. Send metrics via `aws sns publish` and parse in CloudWatch
- D. Buffer metrics in DynamoDB and flush hourly

**Answer:** B

**Explanation:** **Embedded Metric Format (EMF)** lets you log a single structured JSON record to CloudWatch Logs; CloudWatch extracts metrics from the log automatically. This avoids `PutMetricData` API calls and rate limits and is the recommended pattern for Lambda and ECS. Cost is just logs ingestion. EMF is also the most idiomatic way to attach high-cardinality dimensions cheaply.

---

## Q408 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** X-Ray future: ADOT migration

A team is starting a new distributed tracing implementation in mid-2026 for a SageMaker-fronted application. Which is the correct guidance?

- A. Instrument with the X-Ray SDK — it's the AWS-native default
- B. **Use the AWS Distro for OpenTelemetry (ADOT)** — the X-Ray SDK enters maintenance mode in Feb 2026 and ADOT is the forward path; X-Ray *service* (backend) continues
- C. Use ADOT for languages without an X-Ray SDK; X-Ray SDK for Java/Python
- D. Roll your own OpenTracing client

**Answer:** B

**Explanation:** AWS announced the **X-Ray SDK enters maintenance mode in February 2026** — no new features, security fixes only. The recommended path for new applications is **AWS Distro for OpenTelemetry (ADOT)**, which exports OTLP traces to the X-Ray backend (and other targets). The X-Ray *backend service* (service map, traces, segments) continues; only the *SDK* is being deprecated.

---

## Q409 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** X-Ray concepts

Which is the correct definition pair?

- A. Segment = the work done by *one* service in a trace; subsegment = a finer-grained slice (DB call, downstream HTTP request); the **service map** is the graph of services derived from segments
- B. Segment = the full trace; subsegment = one service
- C. Segment = one HTTP request; service map = list of metrics
- D. Subsegment = a sampling rule

**Answer:** A

**Explanation:** An X-Ray **segment** is one service's contribution to a trace (e.g., the Lambda function); **subsegments** are nested units inside (e.g., a DynamoDB query, an HTTP egress call). The **service map** is the auto-derived graph of segments showing call paths, latency, and error rate between services — the heart of X-Ray's UX. Sampling rules govern *which* requests get traced (default 1 request/sec + 5% of remaining).

---

## Q410 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** CloudTrail Management vs Data events

A security engineer wants every `sagemaker:InvokeEndpoint` call recorded with caller identity. Which configuration is required?

- A. None — Management events are on by default and include `InvokeEndpoint`
- B. **Enable Data events for SageMaker on the trail — `InvokeEndpoint` is a Data event (off by default) and is billed (~$0.10 per 100K events)**
- C. Enable Insights events
- D. Subscribe a SQS queue to the default trail

**Answer:** B

**Explanation:** CloudTrail records **Management events by default** (CreateEndpoint, UpdateEndpoint, etc.) but **Data events** (S3 object-level, Lambda invocations, and `sagemaker:InvokeEndpoint`) are **off by default** because they can be high-volume. You must explicitly enable Data events for SageMaker on a trail; cost is ~$0.10 per 100K events. Insights events are anomaly-on-API-calls and unrelated.

---

## Q411 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** CloudTrail Lake sunset

A team currently uses **CloudTrail Lake** to query 2 years of audit history. They want to plan for the future. Which is correct?

- A. CloudTrail Lake is the AWS-recommended forward-looking solution with no announced changes
- B. **CloudTrail Lake is closing to new customers on May 31, 2026** — existing customers retain access; the recommended alternatives for new customers are **Athena over CloudTrail S3** or **Amazon Security Lake**
- C. CloudTrail Lake migrates automatically to QuickSight
- D. CloudTrail Lake is replaced by CloudWatch Logs Insights

**Answer:** B

**Explanation:** AWS announced **CloudTrail Lake stops accepting new customers on May 31, 2026**. Existing Lake event data stores remain available. New customers should use **Athena over CloudTrail S3 logs** (cheap, ad-hoc SQL) or **Amazon Security Lake** (OCSF-normalized, ingests from many sources). This is a likely exam fact for late-2026 sittings.

---

## Q412 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** SageMaker endpoint CloudWatch metrics

Which SageMaker CloudWatch metric does **NOT** exist on a real-time endpoint?

- A. `Invocations`
- B. `InvocationsPerInstance`
- C. `ModelLatency`
- D. **`TrainingJobStatus`**

**Answer:** D

**Explanation:** There is **no `TrainingJobStatus` CloudWatch metric** (and no `PipelineExecutionStatus` either). Job/pipeline lifecycle state changes are emitted as **EventBridge events**, not CloudWatch metrics. Real endpoint metrics include `Invocations`, `InvocationsPerInstance`, `ModelLatency`, `OverheadLatency`, `Invocation4XXErrors`, `Invocation5XXErrors`. Training job metrics are CPU/GPU/Memory/Disk Utilization.

---

## Q413 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Watching pipeline status correctly

A team wants to be paged when any SageMaker Pipelines execution **transitions to `Failed`**. Which is the correct implementation?

- A. CloudWatch alarm on the `PipelineExecutionStatus` metric
- B. **EventBridge rule on `SageMaker Pipeline Execution State Change` events with detail `currentPipelineExecutionStatus = Failed`** → SNS topic
- C. Lambda polling DescribePipelineExecution every 30 s
- D. CloudWatch Logs Insights query

**Answer:** B

**Explanation:** Because no `PipelineExecutionStatus` CloudWatch metric exists, the idiomatic AWS pattern is an **EventBridge rule** matching on the SageMaker Pipelines state-change event and routing to SNS (or Lambda, Step Functions). Lambda polling works but is wasteful and laggy.

---

## Q414 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Three-tier observability stack

The three-tier observability stack recommended in Chapter 50 layers AWS-native, OSS visualization, and APM. Which mapping matches?

- A. CloudWatch (collection) + **Grafana** (dashboards) + **Datadog** (APM/synthetic/RUM)
- B. CloudTrail + Athena + QuickSight
- C. X-Ray + CloudWatch + Splunk
- D. CloudWatch + Kibana + New Relic

**Answer:** A

**Explanation:** Chapter 50's recommended pattern: **CloudWatch** for AWS-native collection (metrics, logs, alarms), **Amazon Managed Grafana** for cross-source dashboards (mixes CloudWatch, Prometheus, Athena), and **Datadog** (or similar APM) for synthetic checks, real-user monitoring, and integrated trace/log correlation. Other combinations exist but this is the textbook recommendation.

---

## Q415 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Container Insights

A team runs SageMaker endpoints on EKS and needs node-level CPU, memory, network metrics with pre-built dashboards. Which feature should they enable?

- A. **Container Insights** — managed CloudWatch agent collects cluster/node/pod metrics with curated dashboards
- B. Lambda Insights
- C. EMR Insights
- D. Trusted Advisor

**Answer:** A

**Explanation:** **Container Insights** (ECS/EKS/Lambda variant for containers) provides node/pod/container-level metrics, performance logs, and curated CloudWatch dashboards. **Lambda Insights** is the equivalent for Lambda (cold starts, init duration). Both are opt-in and incur per-resource costs.

---

## Q416 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** CloudWatch custom metric cost

A team plans to publish 1000 custom metrics. Approximate monthly cost (US East-1, on-demand) is:

- A. ~$0.30 — flat fee
- B. **~$300/month — $0.30 per custom metric per month**
- C. ~$30/month
- D. Free (under 1M data points)

**Answer:** B

**Explanation:** CloudWatch custom metrics are billed at **~$0.30 per metric per month** in US East-1, regardless of data point count. 1000 metrics ≈ $300/month. PutMetricData API calls add cost. EMF helps reduce *API* cost but each unique metric still counts. Knowing this rough number matters for cost-optimization questions.

---

## Q417 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Model Registry hierarchy

Match the SageMaker Model Registry hierarchy.

- A. **Model Package Group → Model Package (Version) → ModelApprovalStatus**
- B. Model → Variant → Endpoint
- C. Repository → Branch → Commit
- D. Catalog → Schema → Model

**Answer:** A

**Explanation:** A **Model Package Group** logically holds all versions of a model (e.g., `churn-classifier`). Each registered model is a **Model Package** with a `ModelPackageVersion`. Each version carries a `ModelApprovalStatus` of `PendingManualApproval`, `Approved`, or `Rejected`. EventBridge emits `SageMaker Model Package State Change` events on every transition — the hook for CT/CD pipelines.

---

## Q418 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** ModelApprovalStatus valid values

Which is **NOT** a valid value of `ModelApprovalStatus`?

- A. `PendingManualApproval`
- B. `Approved`
- C. `Rejected`
- D. **`InReview`**

**Answer:** D

**Explanation:** The three valid values are `PendingManualApproval` (default at registration), `Approved`, and `Rejected`. There is no `InReview`. Transitions emit EventBridge events that downstream pipelines (CodePipeline, Lambda, Step Functions) consume.

---

## Q419 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Cross-account Model Registry

Your platform team runs a **central model hub account** that needs to share approved models with three spoke account environments (dev/stage/prod). The recommended GA approach since June 2024 is:

- A. S3 bucket replication of `model.tar.gz` between accounts
- B. **Share the Model Package Group cross-account via AWS Resource Access Manager (RAM)** — spoke accounts can deploy directly from the shared group
- C. Re-register the model in each account
- D. Use STS AssumeRole on every deploy

**Answer:** B

**Explanation:** Since **June 2024 GA**, SageMaker Model Registry supports **cross-account sharing via AWS RAM**. The hub account shares the Model Package Group resource; spoke accounts gain read/deploy access without copying the artifact. This is the canonical hub-and-spoke MLOps pattern and replaces the older bucket-replication workarounds.

---

## Q420 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Nov 2024 staging-construct migration

In November 2024 AWS introduced a new staging construct (`ModelDeploymentStage`) for Model Registry. Which statement is TRUE?

- A. It replaces and deletes legacy approval workflows; teams must migrate immediately
- B. **It is additive to the legacy `ModelApprovalStatus` workflow; both can coexist while teams migrate**
- C. It only works in `us-east-1`
- D. It requires Managed MLflow to be enabled first

**Answer:** B

**Explanation:** The Nov 2024 staging construct is **additive** — `ModelApprovalStatus` and the new staging concept coexist so teams can migrate gradually. Pipelines built around the original `Approved`/`Rejected` EventBridge events keep working.

---

## Q421 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** EventBridge integration for CT/CD

Which EventBridge event source triggers an automated deployment when a model version is approved?

- A. `aws.sagemaker` source, detail-type `SageMaker Endpoint State Change`
- B. **`aws.sagemaker` source, detail-type `SageMaker Model Package State Change`, with `ModelApprovalStatus == Approved`**
- C. `aws.s3` source, detail-type `Object Created`
- D. `aws.codepipeline` source, detail-type `Stage Execution State Change`

**Answer:** B

**Explanation:** Every `ModelApprovalStatus` transition emits a `SageMaker Model Package State Change` event. An EventBridge rule filters for `Approved` and routes to a Lambda or CodePipeline that performs the canary deploy. This is the canonical CT/CD trigger.

---

## Q422 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Model Cards — purpose and schema

Which best describes a SageMaker **Model Card**?

- A. A versioned binary artifact stored in ECR
- B. **A structured JSON document attached to a model version capturing intended uses, risk rating, training/evaluation details, and lifecycle status (Draft → PendingReview → Approved → Archived); auto-populated from Clarify and Model Monitor where available**
- C. A read-only billing summary
- D. A SageMaker Pipeline step type

**Answer:** B

**Explanation:** **Model Cards** are structured governance documents per model version. The schema includes `intended_uses`, `risk_rating`, `training_details`, `evaluation_details`, owners, and references to bias/explainability reports. Lifecycle: `Draft → PendingReview → Approved → Archived`. SageMaker can auto-populate fields from Clarify (bias/explainability) and Model Monitor (production metrics). They link **at the version level** to the corresponding Model Package.

---

## Q423 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Model Card compliance use cases

Which regulation / framework is NOT typically cited as a driver for Model Card adoption?

- A. **GDPR Article 22** (automated decision-making transparency)
- B. **FDA SaMD** (Software-as-a-Medical-Device)
- C. **NIST AI RMF** + **EU AI Act** + **NYC Local Law 144** (hiring algorithm bias audits) + **ISO 42001** (AI management systems)
- D. **PCI-DSS 4.0** card-data tokenization rules

**Answer:** D

**Explanation:** Model Cards are an AI governance artifact. They map directly to GDPR Art. 22, FDA SaMD, NIST AI RMF, EU AI Act (high-risk system documentation), NYC LL 144 (mandatory audits for AEDTs in hiring), and ISO 42001 (AI Management System). **PCI-DSS 4.0** concerns payment-card data security and is unrelated to model documentation.

---

## Q424 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Lineage Tracking entity types

Which is NOT one of the SageMaker ML Lineage Tracking entity types?

- A. Artifact
- B. Action
- C. Context
- D. Association
- E. TrialComponent
- F. **Pipeline**

**Answer:** F

**Explanation:** The **five entity types** are `Artifact`, `Action`, `Context`, `Association`, and `TrialComponent`. The **five association types** are `Produced`, `ContributedTo`, `AssociatedWith`, `DerivedFrom`, and `SameAs`. `Pipeline` is a separate SageMaker concept, not a lineage entity type.

---

## Q425 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Lineage opt-in

Which statement about SageMaker ML Lineage Tracking is TRUE?

- A. Must be explicitly enabled via `CreateLineageConfig`
- B. **Auto-enabled — every SageMaker training, processing, transform, and pipeline action automatically writes lineage entities**
- C. Requires Managed MLflow
- D. Only available in `us-east-1`

**Answer:** B

**Explanation:** **Lineage Tracking is auto-enabled** with no opt-in for native SageMaker actions. Customers can also create custom lineage entities. Lineage queries use the `LineageQuery` API with `ASCENDANTS` / `DESCENDANTS` directions to traverse upstream/downstream from any starting entity (e.g., from a deployed Model Package walk up to the training data and code Git ref).

---

## Q426 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Managed MLflow on SageMaker

Which is TRUE about Managed MLflow on SageMaker?

- A. Generally available since March 2024; in December 2025 SageMaker introduced a **serverless free tier** for low-traffic MLflow servers
- B. Available only inside SageMaker Studio Classic
- C. Replaces the SageMaker Model Registry entirely
- D. Cannot sync to the SageMaker Model Registry

**Answer:** A

**Explanation:** **Managed MLflow on SageMaker went GA in March 2024** and **Dec 2025 added a serverless free option** for cost-sensitive teams. The MLflow Model Registry **auto-syncs with the SageMaker Model Registry**, letting teams keep MLflow's logging UX while gaining SageMaker's governance (RAM sharing, EventBridge, etc.). ModelBuilder simplifies deploying an MLflow-tracked model.

---

## Q427 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Bad-model rollback runbook

A model version was approved and deployed in error; production metrics tank. Which sequence is the *correct* rollback runbook?

- A. Delete the endpoint and re-create it from CloudFormation
- B. **`UpdateEndpointWeightsAndCapacities` to shift 100% traffic back to the previous variant → mark new Model Package `ModelApprovalStatus = Rejected` → CloudWatch alarm clears → post-mortem ticket with Model Card update**
- C. Manually restore the previous model artifact from S3 versioning
- D. Roll back IAM policies

**Answer:** B

**Explanation:** The canonical bad-model rollback runbook is endpoint-level traffic shift first (zero downtime), then registry status update (`Rejected`), then governance update (Model Card). Endpoint deletion causes downtime; S3 restore doesn't update the registry; IAM rollback is unrelated. Teams pre-build this as a Lambda runbook tied to a CloudWatch alarm.

---

## Q428 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** DIY vs Registry tradeoffs

Which is the strongest reason to prefer the SageMaker Model Registry over a DIY S3+DynamoDB tracking solution?

- A. Cheaper storage
- B. **Built-in EventBridge integration, RAM cross-account sharing, Model Card linkage, Lineage auto-population, and a managed approval workflow — replicating each in DIY is multi-engineer-quarters of work**
- C. Required for Bedrock
- D. Required for IAM

**Answer:** B

**Explanation:** The Model Registry's value is the *ecosystem integration* — EventBridge events for every state change, RAM-based cross-account sharing, automatic Lineage entities, Model Card linkage at the version level, and a built-in approval workflow. DIY can match some pieces but at significant engineering cost. Storage cost is roughly equivalent.

---

## Q429 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Production Variants API basics

Which call shifts 10% of traffic from variant A (current 100%) to variant B on an existing endpoint?

- A. `CreateEndpointConfig` with new weights, then `UpdateEndpoint`
- B. **`UpdateEndpointWeightsAndCapacities(EndpointName=…, DesiredWeightsAndCapacities=[{VariantName:A, DesiredWeight:0.9}, {VariantName:B, DesiredWeight:0.1}])`** — applies live without downtime
- C. `InvokeEndpoint(TargetVariant=B, weight=0.1)`
- D. `UpdateEndpointConfig` with new weights

**Answer:** B

**Explanation:** **`UpdateEndpointWeightsAndCapacities`** changes weights (and instance counts) in place with no endpoint replacement — the canonical mechanism for canaries and A/B ramps. `UpdateEndpoint` is for swapping endpoint configurations (heavier op). `InvokeEndpoint` has a `TargetVariant` parameter to *force* a specific variant for a single call (testing), not to control traffic split.

---

## Q430 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Shadow Variant key constraints

Which statements about SageMaker Shadow Variants are TRUE? **(Select TWO)**

- A. The shadow variant's response is returned to the client alongside the production response
- B. **The shadow variant receives a copy of production traffic but its response is DISCARDED — the client only sees the production response**
- C. **At most 1 production variant and 1 shadow variant per endpoint**
- D. Shadows can be configured with `ShadowProductionVariants[]` (up to 5 shadows)
- E. Shadow variants are billed as a free preview feature

**Answer:** B, C

**Explanation:** Shadows mirror traffic but never reach the client — perfect for comparing predictions and operational metrics (latency, errors) **without changing user experience**. The current limits are **1 production + 1 shadow** per endpoint. Shadows are billed at standard instance hourly rates.

---

## Q431 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Choose A/B vs Shadow

A team wants to validate a new ranking model before exposing it to users. Ground-truth (engagement) is *delayed by hours*, but they have an offline "agreement-with-current-model" check and operational metrics (latency, error rate). Which deployment strategy fits best?

- A. A/B test with 50/50 weights for one week
- B. **Shadow Variant** — compare predictions and operational metrics without affecting users; ground-truth not needed
- C. Multi-armed bandit
- D. Direct cut-over

**Answer:** B

**Explanation:** Shadow Variants fit perfectly when the candidate must be evaluated **operationally and prediction-wise without changing user-facing behavior**, especially when ground-truth lags. A/B testing requires labeled engagement to make a decision. Once shadow validates basics (latency, prediction agreement), promote to a small A/B for the engagement-quality call.

---

## Q432 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Trap — InitialVariantWeight=0.1 is not Shadow

A team sets `InitialVariantWeight=0.1` on a new production variant "to test it without impact." Why is this potentially dangerous?

- A. It actually serves 100% of traffic to the new variant
- B. **10% of *real users* receive the candidate's response — any bug, latency spike, or bad prediction directly impacts them. To avoid user impact entirely, use a Shadow Variant instead**
- C. CloudWatch metrics aren't published for 10% weight variants
- D. It violates SageMaker quota limits

**Answer:** B

**Explanation:** `InitialVariantWeight=0.1` is a real **production weight** — 10% of users *get* that response and experience whatever the candidate does. This is fine when you want experimental exposure with measurable user impact, but it is **not** "zero-impact testing." For true zero-user-impact validation, use a **Shadow Variant** (responses discarded).

---

## Q433 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Statistical sample size

A team wants to detect a 1% lift on a baseline conversion rate of 5% with 80% power and α = 0.05 (two-sided). Approximate per-arm sample size using `n ≈ 16·σ²/MDE²` (Bernoulli σ²≈p(1−p)):

- A. ~500
- B. ~7,600
- C. **~76,000**
- D. ~760,000

**Answer:** C

**Explanation:** Bernoulli variance = 0.05 × 0.95 ≈ 0.0475. MDE = 0.01 → MDE² = 0.0001. `n ≈ 16 × 0.0475 / 0.0001 ≈ 7,600` per arm at α = 0.05, 50% power. For 80% power the multiplier is ~16 → **~76,000 per arm** (some books simplify to "you need tens of thousands"). The instructive point: small lifts on common base rates need huge samples.

---

## Q434 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Peeking inflates Type I error

A PM monitors the experiment dashboard hourly and stops the test the *first* time p < 0.05. The true Type I error rate is:

- A. Still ~5%
- B. **Inflated to roughly 25% (and approaches 100% as peek count grows) — this is the "peeking" or "optional-stopping" problem**
- C. Drops to ~1%
- D. Undefined

**Answer:** B

**Explanation:** Continuous "peek-and-stop" on a single α = 0.05 test inflates false-positive rate to ~20–25% for typical experiment lengths and toward 1.0 as you peek more. Mitigations: pre-register a single look, use **group-sequential** (O'Brien-Fleming) boundaries, **always-valid p-values** (mSPRT), or Bayesian decision rules. This is the most common cause of "we shipped the loser."

---

## Q435 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Multiple comparisons in A/B

A team measures 10 metrics on the same A/B test, each at α = 0.05, and declares the test a win if *any* moves significantly. The family-wise false-positive rate is approximately:

- A. 0.05
- B. **0.40 (close to 1 − (1−0.05)^10 ≈ 0.40); use Bonferroni (α/m = 0.005) or Benjamini-Hochberg FDR control**
- C. 0.005
- D. 1.00

**Answer:** B

**Explanation:** Under independence, `1 − (1−α)^m` with m = 10 gives ≈ 0.40 — roughly an 8× inflation. **Bonferroni** sets a per-test α of α/m for strict FWER control; **Benjamini-Hochberg** instead controls the **False Discovery Rate** and is less conservative for many metrics. A disciplined alternative: declare a single **OEC** (Overall Evaluation Criterion) up front; everything else is exploratory.

---

## Q436 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** OEC vs guardrail vs proxy

In experimentation parlance, which is the **OEC**?

- A. A short-term metric correlated with the outcome but easy to game
- B. **The single primary success metric chosen up front — typically a composite balancing long-term value, immediate engagement, and quality**
- C. Any metric that must not regress (e.g., latency, error rate)
- D. The runtime engineering metric for an experiment

**Answer:** B

**Explanation:** The **Overall Evaluation Criterion (OEC)** is the *single* primary metric used to declare an experiment a winner — often a composite (e.g., "long-term-value-adjusted clicks per session"). **Proxy metrics** are short-term stand-ins (clicks, watch time) that may not reflect long-term value. **Guardrail metrics** must not regress (latency, crash rate, fairness) regardless of OEC outcome. Distinguishing the three is canonical experimentation discipline (Kohavi, Microsoft ExP).

---

## Q437 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** SUTVA violation

A ride-sharing app A/B tests a new pricing model. Treatment users and control users *share the same drivers and surge market*. The independence-of-units assumption breaks. The threat is:

- A. Simpson's paradox
- B. **SUTVA violation (Stable Unit Treatment Value Assumption) — interference between units makes the difference of means a biased estimate of the causal effect**
- C. Sample Ratio Mismatch (SRM)
- D. Peeking

**Answer:** B

**Explanation:** **SUTVA** requires that a unit's outcome depends only on its own treatment, not other units' treatments. Two-sided marketplaces (rides, ads, social) routinely violate SUTVA because treatment and control compete for the same supply. Fixes: **cluster randomization** (whole cities), **switchback / time-split designs**, or **synthetic-control** evaluations. This is one of the ten "we shipped the loser" pathologies.

---

## Q438 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Sample Ratio Mismatch

A 50/50 A/B test was configured, but after a week control has 51,200 users and treatment has 48,800. Which problem does this signal?

- A. Statistical fluke; ignore
- B. **Sample Ratio Mismatch (SRM)** — a chi-squared test on the assignment counts rejects the 50/50 split; usually a bug in randomization, bot filtering, or logging that biases all downstream results — halt the experiment and diagnose
- C. Peeking
- D. Network effect

**Answer:** B

**Explanation:** **SRM** is the canonical "the experiment was broken before it started" check: if the actual split deviates from intended at p < 0.001, the randomizer or instrumentation is corrupted, and *no* metric on the experiment is trustworthy. Standard practice: every dashboard runs an SRM check, halts the experiment, and notifies the experimenter.

---

## Q439 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** A/B vs Multi-Armed Bandit

When should a team prefer a **multi-armed bandit (MAB)** over a fixed-horizon A/B test?

- A. When the goal is a *clean causal estimate* of treatment effect for an external audit
- B. **When the goal is to minimize regret (maximize cumulative reward) during the experiment — e.g., headline selection, ad creative rotation — and a precise unbiased effect estimate is not required**
- C. When SUTVA is violated
- D. When sample sizes are very small

**Answer:** B

**Explanation:** MABs (e.g., Thompson sampling, UCB) **dynamically reallocate traffic to better-performing arms during the experiment** — great for revenue-maximizing settings (headlines, recommendations) with many arms and quick feedback. They sacrifice a clean causal estimate (continuous reallocation biases naive difference-in-means). A/B tests are the right tool for **decision questions** that need an unbiased effect for governance, regulatory, or causal-inference reasons.

---

## Q440 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Auto-rollback wiring

Which auto-rollback wiring is the canonical AWS-native pattern?

- A. CodeDeploy hooks only
- B. **CloudWatch alarm on guardrail metric → EventBridge → Lambda → `UpdateEndpointWeightsAndCapacities` to shift weight back to the prior variant**
- C. SNS notification only (manual)
- D. Step Functions polling DescribeEndpoint every 10 s

**Answer:** B

**Explanation:** The canonical AWS-native auto-rollback for a SageMaker endpoint: **guardrail-metric CloudWatch alarm** (e.g., `Invocation5XXErrors > 1%` or `ModelLatency` p99 spike) **→ EventBridge rule** matching the ALARM state-change **→ Lambda** that calls **`UpdateEndpointWeightsAndCapacities`** to shift traffic back. CodeDeploy hooks work for some deployment styles but are not necessary; manual SNS is too slow; polling is wasteful.

---
# MLA-C01 Practice Question Bank — Domain 4 Half B (Part J, Ch 53-58)

> **Scope:** 60 exam-realistic questions (Q441-Q500) covering Domain 4 — ML Solution Monitoring, Maintenance, and Security, half B: IAM least-privilege execution roles, network isolation, KMS encryption lifecycle, compliance & data residency, cost optimization, and cost observability.
>
> **Source chapters:**
> - Ch 53 — Least-privilege SageMaker execution role
> - Ch 54 — Network isolation (VPC, endpoints, EnableNetworkIsolation, ICTE)
> - Ch 55 — KMS encryption end-to-end
> - Ch 56 — Compliance & data residency (HIPAA, GDPR, SR 26-2, EU AI Act)
> - Ch 57 — Cost optimization (Spot, Savings Plans, right-sizing)
> - Ch 58 — Cost observability (Cost Explorer, CUR, Budgets, CAD)
>
> **Format:** Each question is single-answer multiple choice (A-D) unless prefixed with "(Select TWO)" or "(Select THREE)". The real MLA-C01 exam is 65 questions in 130 minutes (2m per question).

---

## Q441 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Distinguish the two-role pattern (user role vs SageMaker execution role)

A platform team is onboarding a new data-science squad into a shared SageMaker Studio domain. They need to design IAM so that engineers can launch Studio, but the actual training jobs run with a different, restricted identity. Which design correctly implements the two-role pattern that AWS recommends?

- A. Assign `AmazonSageMakerFullAccess` to the engineers' SSO permission set and reuse the same role as the execution role on `CreateTrainingJob`.
- B. Use one IAM **user role** (assumed via SSO) that grants `sagemaker:CreatePresignedDomainUrl` and `iam:PassRole` on a separate **execution role** that the SageMaker control plane assumes for training, processing, and endpoint runtime.
- C. Have engineers create access keys, embed them in notebooks, and let SageMaker use those keys to run jobs.
- D. Give the execution role `sts:AssumeRole` on the user role so SageMaker can impersonate the engineer at job-launch time.

**Answer:** B

**Explanation:** The recommended two-role pattern separates the **user role** (humans assuming via SSO for Studio login + job submission) from the **execution role** (assumed by `sagemaker.amazonaws.com` to run training containers, mount EBS, write to S3, pull from ECR). The user role only needs `iam:PassRole` on the execution role; the execution role never gets `sagemaker:*` (privilege escalation). A is the AWS-anti-pattern of one fat role. C uses long-lived static creds. D inverts the trust direction — SageMaker assumes the execution role, not the user role.

---

## Q442 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recognize `AmazonSageMakerFullAccess` and the verbatim ARN-naming trap

An engineer creates an IAM role named `MLOpsRunner` and attaches `AmazonSageMakerFullAccess`. They then try to pass this role into `CreateTrainingJob` via the user role and get `User is not authorized to perform iam:PassRole`. Why?

- A. `AmazonSageMakerFullAccess` does not include `iam:PassRole`; you must add it explicitly.
- B. The `iam:PassRole` allow in `AmazonSageMakerFullAccess` only grants PassRole for roles whose **name contains `SageMaker`** (case-insensitive) and where `iam:PassedToService` equals `sagemaker.amazonaws.com`.
- C. The role must be in the same OU as the user.
- D. SageMaker only accepts roles created by Service Catalog.

**Answer:** B

**Explanation:** This is the verbatim AWS-managed-policy trap. `AmazonSageMakerFullAccess` scopes its `iam:PassRole` statement with a `StringLike` on `iam:AssociatedResourceArn` of `arn:aws:iam::*:role/*SageMaker*` plus `iam:PassedToService = sagemaker.amazonaws.com`. A role called `MLOpsRunner` doesn't match. Fix: rename to `MLOpsSageMakerRunner`, or attach a custom inline policy with explicit PassRole. A is false — PassRole **is** in the managed policy but is narrowly scoped. C/D are invented.

---

## Q443 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Identify privilege-escalation risk of `sagemaker:*` on an execution role

A security reviewer flags the production SageMaker execution role for granting `sagemaker:*`. Why is this dangerous even though the role is only assumed by `sagemaker.amazonaws.com`?

- A. It allows the role to delete CloudTrail trails.
- B. A compromised training container can call `sagemaker:CreateTrainingJob` (or `CreateNotebookInstance`) passing **a different, more privileged role** that the execution role can already PassRole to, escalating privileges across the account.
- C. `sagemaker:*` grants root access to the account.
- D. It bypasses KMS encryption on volumes.

**Answer:** B

**Explanation:** The classic SageMaker privilege-escalation chain: container exfils execution-role creds via SSRF/RCE, calls `CreateTrainingJob` with `RoleArn` of a higher-priv role (admin, finance), and the new job runs as that role. AWS guidance: **never grant `sagemaker:*` on the execution role**. Limit it to read-only API needed by the job (e.g., `sagemaker:DescribeTrainingJob` for self-introspection). Keep `sagemaker:Create*`, `PassRole`, and admin actions on the **user role** only.

---

## Q444 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Apply S3 read/write split prefixes in execution-role policy

You want the execution role to **read** raw training data from `s3://corp-ml/raw/*` but **only write** artifacts to `s3://corp-ml/artifacts/${aws:PrincipalTag/Project}/*`. Which is the correct minimal split?

- A. One statement granting `s3:*` on `arn:aws:s3:::corp-ml/*`.
- B. Two statements: (1) `s3:GetObject`, `s3:ListBucket` on `corp-ml/raw/*`; (2) `s3:PutObject`, `s3:AbortMultipartUpload`, `s3:GetObject` on `corp-ml/artifacts/${aws:PrincipalTag/Project}/*` — plus bucket-level `s3:ListBucket` with `s3:prefix` conditions.
- C. Grant `s3:PutObject` on both prefixes — SageMaker will figure out which is which.
- D. Use a bucket policy only; the execution role needs no S3 permissions.

**Answer:** B

**Explanation:** Least-privilege S3 access requires **prefix-scoped statements** with the right verbs per prefix and tag-based segmentation via `${aws:PrincipalTag/Project}`. You also need bucket-level `ListBucket` with `s3:prefix` condition keys so list calls are scoped. A is a wide-open anti-pattern. C grants write to raw (bad — corrupts training data). D ignores that the execution role is the principal SageMaker uses.

---

## Q445 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Pin ECR image pulls in execution-role policy

To prevent a compromised execution role from pulling arbitrary public images, you want to restrict ECR pulls to a specific account's registry and a specific repo. Which condition keys are correct?

- A. `aws:SourceAccount` and `aws:SourceArn`.
- B. `ecr:ResourceAccount` and `ecr:RepositoryName` (or scope the `Resource` ARN to `arn:aws:ecr:us-east-1:111111111111:repository/ml-training-images`).
- C. `kms:ViaService = ecr.amazonaws.com`.
- D. `aws:RequestedRegion` only.

**Answer:** B

**Explanation:** ECR supports resource-level permissions, so the cleanest pin is `Resource: arn:aws:ecr:{region}:{accountId}:repository/{repoName}` plus condition `ecr:ResourceTag/Approved = true` if you tag images. A's keys exist but are for resource-based policies, not the identity policy of a puller. C is for KMS ViaService — not ECR. D scopes region but not registry/repo.

---

## Q446 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Use `kms:ViaService` to restrict KMS use to specific service principals

You want to ensure the execution role can decrypt with `arn:aws:kms:us-east-1:111:key/abc` **only when the call originates from S3 or SageMaker** (not arbitrary services). Which condition do you add?

- A. `aws:SourceIp` of the VPC endpoint CIDR.
- B. `kms:ViaService` IN `["s3.us-east-1.amazonaws.com", "sagemaker.us-east-1.amazonaws.com"]` on the `kms:Decrypt` statement.
- C. `kms:GrantConstraintType = EncryptionContextEquals`.
- D. `sts:ExternalId`.

**Answer:** B

**Explanation:** `kms:ViaService` is the canonical KMS condition key for restricting which AWS service can broker the KMS call on behalf of the principal. List the regional service principal names. This is how you enforce "this CMK only ever gets used from S3 or SageMaker" — it blocks lateral exfil through, say, EBS or Glue if those weren't allowed.

---

## Q447 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Configure tag-based ABAC on a SageMaker execution role

Your platform wants execution roles to access only resources tagged with the same `Project` and `Environment` as the principal. (Select TWO)

- A. Add `Condition: { "StringEquals": { "aws:ResourceTag/Project": "${aws:PrincipalTag/Project}", "aws:ResourceTag/Environment": "${aws:PrincipalTag/Environment}" } }` to identity policies.
- B. Tag the execution role with `Project` and `Environment`, and ensure SageMaker propagates these via **source identity** (`sts:SourceIdentity`) when assuming the role.
- C. Use `aws:SourceAccount` instead — ABAC isn't supported in SageMaker.
- D. Put the tags only in the trust policy.
- E. Use `kms:EncryptionContext` for ABAC.

**Answer:** A, B

**Explanation:** ABAC uses `aws:PrincipalTag/X` matched against `aws:ResourceTag/X` in identity policies. SageMaker honors role tags and can propagate **source identity** through `sts:AssumeRole` so that downstream calls preserve attribution. C is wrong — SageMaker fully supports ABAC. D — trust policy controls who can assume; ABAC enforcement happens in identity/resource policies. E — encryption context is unrelated to ABAC on resources.

---

## Q448 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Mitigate confused-deputy attacks on SageMaker execution roles

How do you harden the **trust policy** of a SageMaker execution role against the confused-deputy problem?

- A. Add `aws:SourceAccount` (and optionally `aws:SourceArn`) conditions to the `sts:AssumeRole` statement so only requests originating from your account/resource can let SageMaker assume the role.
- B. Remove the `sagemaker.amazonaws.com` principal entirely.
- C. Set `MaxSessionDuration = 1` second.
- D. Encrypt the trust policy with KMS.

**Answer:** A

**Explanation:** The confused-deputy pattern: a service (SageMaker) in account A could be tricked by a request crafted in account B into using account A's credentials. Mitigation: add `aws:SourceAccount = ${accountA}` (and optionally `aws:SourceArn = arn:aws:sagemaker:...:*` patterns) to the AssumeRole condition. This is the same pattern as `s3.amazonaws.com` → `aws:SourceAccount`. B breaks SageMaker. C breaks all jobs. D — trust policies aren't encrypted.

---

## Q449 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Apply permissions boundaries for delegated role creation

A central security team wants to let ML platform engineers create their own SageMaker execution roles, but never grant `s3:*` outside `corp-ml-*` buckets and never grant `iam:*`. Which mechanism is purpose-built for this?

- A. Service Control Policies on the OU.
- B. A **permissions boundary** attached to roles the platform team creates — the effective permissions are the intersection of the identity policy and the boundary, and IAM blocks any role-creation that doesn't attach the boundary.
- C. A bucket policy on `corp-ml-*`.
- D. AWS Config rules.

**Answer:** B

**Explanation:** Permissions boundaries are the IAM primitive for **delegated role creation** — you give engineers `iam:CreateRole` only if they attach `PermissionsBoundary = SecurityBoundaryPolicy`. The effective permissions become `Identity ∩ Boundary`. SCPs (A) apply at the org level and would block the platform team too. Bucket policies (C) and Config (D) don't prevent over-permissive role creation at the IAM layer.

---

## Q450 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Use Service Catalog + SageMaker Projects to mint compliant roles

What is the operational advantage of using **AWS Service Catalog + SageMaker Projects** to provision execution roles instead of letting teams create them ad-hoc?

- A. Service Catalog roles get free AWS support.
- B. The launch constraint pins a CloudFormation template that bakes in the approved trust policy, permissions boundary, naming convention (so PassRole works), tags, and KMS key references — teams get a one-click compliant role without IAM expertise.
- C. SageMaker Projects bypass IAM entirely.
- D. Service Catalog auto-rotates roles every 24 hours.

**Answer:** B

**Explanation:** Service Catalog products are how regulated orgs ship "golden roles": pre-baked CFN with the right name (matches `*SageMaker*` for PassRole), permissions boundary, tag schema, and KMS references. The portfolio launch constraint runs CFN as a high-privilege role so the developer never needs `iam:CreateRole`. SageMaker Projects extend this with MLOps pipelines wired to the role.

---

## Q451 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Use IAM Access Analyzer to find unused permissions and generate policies

A compliance lead wants three deliverables from IAM Access Analyzer for SageMaker execution roles. Which mapping is correct? (Select THREE)

- A. **External access analyzer** — flags roles whose trust policy is assumable from outside the account/org.
- B. **Unused access analyzer** — identifies actions and services that the role hasn't used in N days, so you can prune.
- C. **Policy generation from CloudTrail** — generates a least-privilege policy from observed CloudTrail events over a time window.
- D. **Macie integration** — scans S3 for PII.
- E. **Cost Anomaly Detection** — finds expensive roles.

**Answer:** A, B, C

**Explanation:** Access Analyzer has three flavors covering external trust, unused permissions, and CloudTrail-driven policy generation — exactly the three IAM lifecycle questions: who can assume me, what do I actually need, what should my policy be. D is Macie (data-layer). E is cost — wrong domain.

---

## Q452 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Debug `AccessDenied` on `iam:PassRole`

A training job submission returns `User: arn:aws:sts::111:assumed-role/MLEng/alice is not authorized to perform: iam:PassRole on resource: arn:aws:iam::111:role/MLOpsRunner`. Which is the **fastest** correct diagnostic step?

- A. Look up the `AssumeRole` event in CloudTrail.
- B. Look up the **failed `iam:PassRole` event** (or `CreateTrainingJob` `errorCode = AccessDenied`) in CloudTrail, then inspect the user role's policies — most likely the PassRole condition restricts to names containing `SageMaker` and `MLOpsRunner` doesn't match, **or** `iam:PassedToService` isn't `sagemaker.amazonaws.com`.
- C. Reboot the Studio app.
- D. Recreate the KMS key.

**Answer:** B

**Explanation:** The error message is explicit: the user role lacks PassRole on `MLOpsRunner`. CloudTrail `errorCode = AccessDenied` events show the principal, action, resource, and conditions evaluated. The classic root cause is the `AmazonSageMakerFullAccess` PassRole condition not matching the role name (must contain `SageMaker`). Rename to `MLOpsSageMakerRunner` or add a custom PassRole statement. A/C/D are unrelated.

---

## Q453 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Design ML-relevant SCPs at the org level

Which four Service Control Policies should the org apply to **all** SageMaker accounts to enforce a baseline? (Select THREE that match what the brief calls out, plus the "all of the above" trap)

- A. Deny actions in any region except an approved allow-list (use `aws:RequestedRegion`).
- B. Deny `s3:PutObject` unless `s3:x-amz-server-side-encryption = aws:kms` (require KMS encryption).
- C. Deny `iam:CreateUser` (force SSO/Identity-Center federation only).
- D. Deny `s3:PutBucketAcl` and `s3:PutObjectAcl` that grant public access (no public S3).
- E. Allow `sagemaker:*` to everyone in dev.

**Answer:** A, B, C, D

**Explanation:** These are the four ML-relevant SCPs from the chapter: region restriction (residency + cost), KMS-encryption mandate, no-IAM-users (force federation), and no-public-S3 (data exfil prevention). E violates least-privilege. *Note: multi-correct intentionally to validate SCP literacy; the answer is A,B,C,D.*

---

## Q454 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Identify the PassRole tag trap from AWS docs

You try to attach a condition like `iam:ResourceTag/Project = ${aws:PrincipalTag/Project}` to your `iam:PassRole` statement. AWS documentation warns against this. Why?

- A. Tags on IAM roles cannot be set.
- B. `iam:PassRole` does **not** support tag-based conditions on the role being passed — AWS docs explicitly warn this trap because the action operates on the role's ARN at submission time, and tag mutations on the role can bypass the check. AWS recommends scoping PassRole by role ARN/name patterns instead.
- C. Tags propagate too slowly.
- D. PassRole only works in us-east-1.

**Answer:** B

**Explanation:** The chapter and AWS IAM documentation flag this: `iam:PassRole` is a special action that doesn't reliably honor `aws:ResourceTag` on the role being passed because tag conditions can be circumvented if a separate identity can mutate the role's tags. Use **role name patterns** (matching `*SageMaker*` to compose with managed policies) or explicit ARN allow-lists. D — region-agnostic. A/C — false.

---

## Q455 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recognize SR 11-7 / SR 26-2 banking model risk guidance

For a US national bank deploying SageMaker-trained credit decisioning models, which regulatory guidance is the binding model-risk framework as of April 17, 2026?

- A. SR 11-7 (the original 2011 OCC/Fed interagency guidance), still primary.
- B. **SR 26-2** — the April 17, 2026 revised interagency guidance that updates SR 11-7 with explicit AI/ML lifecycle, third-party model, and generative AI provisions.
- C. NIST SP 800-53 Rev 5.
- D. ISO 27001:2022.

**Answer:** B

**Explanation:** SR 26-2 (April 17, 2026) is the revised interagency model-risk-management guidance that supersedes SR 11-7 for federally supervised banks, adding explicit treatment of AI/ML model validation, third-party (foundation) model oversight, and ongoing performance monitoring. SR 11-7 is still cited but is the legacy version. NIST/ISO are referenced controls but not banking-specific MRM.

---

## Q456 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recall the Capital One IMDSv1 SSRF as canonical network-isolation motivation

The 2019 Capital One breach is taught as the canonical motivation for which combined SageMaker controls? (Select THREE)

- A. **Network isolation** of compute (no direct egress, no metadata service abuse).
- B. **Least-privilege execution role** (limit blast radius if creds exfil'd).
- C. **IMDSv2** enforcement (session tokens defeat SSRF that exfilled IMDSv1 creds).
- D. **Spot instance preference** to reduce attacker dwell time.
- E. Bucket Keys on S3 to reduce KMS cost.

**Answer:** A, B, C

**Explanation:** The Capital One breach combined an SSRF flaw with IMDSv1 (no session token) on a misconfigured WAF EC2, plus an over-permissive IAM role that could `s3:Get*` 100M+ customer records. The lesson for SageMaker: enforce IMDSv2 on training/processing/endpoint containers, run them in a VPC with no egress (or only via interface endpoints), and scope the execution role tightly. D/E are unrelated.

---

## Q457 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Architect a no-egress SageMaker reference

Which combination correctly describes the no-egress reference architecture for SageMaker?

- A. Public Studio + NAT Gateway + SSE-S3.
- B. **Full private VPC** + **interface endpoints** for SageMaker/STS/CloudWatch/ECR/KMS + **VPC-only Studio** (`AppNetworkAccessType: VpcOnly`) + **KMS-CMK** for all volumes/outputs + **S3 gateway endpoint** for bulk data.
- C. Public Studio + VPC-only training jobs.
- D. Direct Connect only, no endpoints needed.

**Answer:** B

**Explanation:** The no-egress reference is: Studio in `VpcOnly` mode (no public ingress URL escape), private subnets with **interface endpoints** for every AWS service the workload calls (SageMaker API/Runtime/FeatureStore-Runtime/Notebook/Studio + STS + CloudWatch Logs/Monitoring + ECR API+DKR + KMS), an **S3 gateway endpoint** for bulk data (cheap, no per-GB), and customer-managed KMS keys on every encryption surface. NAT (A) means egress. C leaves Studio public. D — even with DX you still need endpoints for AWS-API routing.

---

## Q458 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Distinguish `EnableNetworkIsolation` from `VpcConfig`

What is the precise behavior of `EnableNetworkIsolation = true` on a `CreateTrainingJob` call?

- A. Same as `VpcConfig` — places the container in your VPC.
- B. Disables **all** network I/O from inside the container (no egress, no inbound), and the **container does not receive AWS credentials** from the SageMaker control plane. It composes with `VpcConfig`: you can have a job in your VPC and still mark it network-isolated, in which case the ENI gets no route out.
- C. Disables encryption.
- D. Restricts the job to one AZ.

**Answer:** B

**Explanation:** `EnableNetworkIsolation` is a stronger sibling to `VpcConfig`. It says: even though the container may have an ENI in your VPC, the runtime drops all network and refuses to inject the execution-role credentials into the container's environment. This is for scenarios where the container itself must not call AWS (e.g., scoring with a model that should not exfil). `VpcConfig` only places the ENI; it doesn't strip credentials.

---

## Q459 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Set up `VpcConfig` cross-account two-ENI model

A SageMaker training job uses `VpcConfig`. How many ENIs are created and in whose account?

- A. One ENI in your account.
- B. **Two ENIs**: one in the SageMaker service account (managing the training container) and a **hyperplane ENI in your account's VPC subnet** that the service-account ENI tunnels through — this is what bills your IP space and shows up in your VPC flow logs.
- C. Three ENIs across three accounts.
- D. Zero — SageMaker uses a shared NLB.

**Answer:** B

**Explanation:** SageMaker (like Lambda VPC, RDS, etc.) uses a hyperplane ENI in your VPC subnet that's owned by your account but driven by the service account. The cross-account model means flow logs/ENI counts/IP consumption are yours. The training container itself runs in the service-managed plane.

---

## Q460 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Choose Studio `AppNetworkAccessType` mode

A financial-services team requires Studio traffic to never traverse the public internet. Which Studio domain setting is required?

- A. `PublicInternetOnly` — Studio defaults are sufficient.
- B. `AppNetworkAccessType: VpcOnly` — all Studio app traffic flows through ENIs in your VPC, requiring you to provision interface endpoints for **all** services Studio calls (SageMaker API + runtime + featurestore-runtime + notebook + studio + ECR + STS + CloudWatch + S3 gateway + 7+ more, totaling 16+).
- C. `IsolatedSubnet`.
- D. `OnPremOnly`.

**Answer:** B

**Explanation:** `VpcOnly` is the contract that disables Studio's public internet egress; the cost is that you must inventory and provision every endpoint Studio depends on (16+ services per the chapter). `PublicInternetOnly` is the default — fine for non-regulated workloads. C/D are invented.

---

## Q461 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Solve "pip install fails" in a VpcOnly Studio

A data scientist in a `VpcOnly` Studio domain runs `pip install scikit-learn==1.5.0` and it fails. Which three fixes does AWS recommend? (Select THREE)

- A. **CodeArtifact PyPI upstream mirror** with VPC endpoint — Studio resolves `pip` against CodeArtifact, which proxies PyPI through AWS.
- B. **Bandersnatch** to maintain an on-prem PyPI mirror reachable over Direct Connect/VPN.
- C. **Custom ECR kernel images** that bake all needed wheels at image-build time (no pip at runtime).
- D. Add `0.0.0.0/0` to the security group egress.
- E. Disable IMDSv2.

**Answer:** A, B, C

**Explanation:** Three sanctioned patterns: CodeArtifact (managed, easy), self-hosted Bandersnatch (full mirror, complex), or bake-everything-in-the-image (immutable, requires CI). D defeats the entire isolation posture. E weakens metadata service security and doesn't help pip.

---

## Q462 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recall CodeArtifact token TTL gotcha

A team configures Studio to use CodeArtifact for pip. Their long-running training job starts succeeding `pip install` calls, then 12+ hours later fails. What's the cause?

- A. CodeArtifact has a regional outage.
- B. The **CodeArtifact authorization token has a maximum 12-hour TTL**; long-running jobs need to refresh via `aws codeartifact get-authorization-token` on a schedule, or set the token to be re-fetched at each `pip` call.
- C. PyPI throttles after 12 hours.
- D. The job's KMS key was rotated.

**Answer:** B

**Explanation:** This is a textbook CodeArtifact gotcha: tokens issued by `get-authorization-token` expire after at most 12 hours. Jobs longer than that (multi-day training, persistent endpoints baking new packages) need a refresh loop. C/D are unrelated.

---

## Q463 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Configure `EnableInterContainerTrafficEncryption` for distributed training

A distributed training job (`InstanceCount = 16`) handles PHI and requires inter-node encryption. Which two changes are required? (Select TWO)

- A. Set `EnableInterContainerTrafficEncryption = true` on `CreateTrainingJob`.
- B. Open **UDP/500** and **IP protocol 50 (ESP)** between training-node SGs (IPsec).
- C. Set `KmsKeyId = alias/sagemaker/sagemaker.amazonaws.com`.
- D. Disable `VpcConfig`.
- E. Use `c5n` instance type only.

**Answer:** A, B

**Explanation:** ICTE wraps inter-node traffic in IPsec. The toggle is `EnableInterContainerTrafficEncryption = true`, **and** the security groups must allow UDP/500 (IKE) and IP protocol 50 (ESP) between nodes — without these SG rules the IPsec association can't form and the job fails. D would remove the VPC entirely. C — the encryption is on the wire, not S3. E is not required.

---

## Q464 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Name the 5 SageMaker interface endpoint DNS names

Which set is the correct list of SageMaker-specific interface endpoint service names? (Select TWO)

- A. `com.amazonaws.{region}.sagemaker.api`, `com.amazonaws.{region}.sagemaker.runtime`, `com.amazonaws.{region}.sagemaker.featurestore-runtime`.
- B. `com.amazonaws.{region}.sagemaker.notebook`, `com.amazonaws.{region}.sagemaker.studio`.
- C. `com.amazonaws.{region}.sagemaker.s3`.
- D. `com.amazonaws.{region}.sagemaker.kms`.
- E. `com.amazonaws.{region}.sagemaker.iam`.

**Answer:** A, B

**Explanation:** Exactly five SageMaker-namespaced interface endpoints: `.api` (control plane CreateTrainingJob etc.), `.runtime` (invoke endpoint), `.featurestore-runtime` (online FS GetRecord/PutRecord), `.notebook` (notebook instance IDE), `.studio` (Studio app stream). S3/KMS/IAM are their own namespaces (`com.amazonaws.{region}.s3`, `.kms`, etc.).

---

## Q465 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recognize FIPS endpoint-policy limitation

A FedRAMP-High workload requires FIPS 140-2 validated endpoints. Which is a real limitation of the FIPS-enabled SageMaker interface endpoint?

- A. FIPS endpoints don't support TLS.
- B. **FIPS-runtime endpoint policies cannot enforce custom resource-level conditions** the same way non-FIPS endpoints can — endpoint policy support and condition coverage on FIPS endpoints is reduced; teams typically pair with SCPs/IAM for fine-grained control.
- C. FIPS endpoints are only available in us-east-2.
- D. FIPS endpoints disable KMS.

**Answer:** B

**Explanation:** The chapter flags that FIPS-runtime endpoints have reduced endpoint-policy expressiveness (some condition keys not honored); for fine-grained per-action/per-resource control, teams supplement with SCPs and identity policies. C — FIPS endpoints are in multiple GovCloud and commercial regions. A/D are false.

---

## Q466 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Block cross-account exfiltration via endpoint policy

You want to ensure that the S3 gateway endpoint in your VPC can **only** be used to access buckets in your AWS organization. Which endpoint-policy condition expresses this?

- A. `aws:SourceVpc` equals your VPC ID.
- B. `aws:ResourceOrgID` equals your organization ID on `s3:*` actions (also `aws:PrincipalOrgID` for cross-account principals).
- C. `aws:SourceIp` 10.0.0.0/8.
- D. `kms:ViaService = s3.amazonaws.com`.

**Answer:** B

**Explanation:** `aws:ResourceOrgID` is the org-scoped condition that ensures the **target resource** belongs to your organization — perfect for preventing exfil to attacker buckets. Pair with `aws:PrincipalOrgID` to ensure callers are also from your org. A scopes source, not destination.

---

## Q467 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Choose PrivateLink Pattern A vs B

A SaaS team exposes a custom anomaly-detection model to enterprise customers' VPCs. They want their customers to invoke via PrivateLink without traversing the internet. Which is correct?

- A. Pattern A — point customers at `com.amazonaws.{region}.sagemaker.runtime` directly.
- B. Pattern B — front the SageMaker endpoint with **NLB + ECS/Lambda proxy**, publish a **custom VPC endpoint service**, and let customers create interface endpoints to your service.
- C. Use S3 gateway endpoint.
- D. Direct Connect only.

**Answer:** B

**Explanation:** Pattern A (the public SageMaker Runtime endpoint) leaks tenancy and forces customers to use your IAM realm. Pattern B is the multi-tenant SaaS pattern: your custom **VPC Endpoint Service** in front of an NLB → Lambda/ECS proxy → SageMaker Runtime. Customers see only your endpoint service name (`com.amazonaws.vpce.{region}.vpce-svc-xxxx`), get private DNS, and you mediate auth.

---

## Q468 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Design centralized PrivateLink hub with Transit Gateway + RAM

An enterprise has 40 VPCs across 8 accounts. They want to centralize interface-endpoint costs. Which architecture is recommended and what's the rough break-even?

- A. One interface endpoint per VPC; no central hub.
- B. **Centralized endpoint VPC** sharing endpoints via **Transit Gateway** + **RAM** to other VPCs; break-even occurs around **~7 VPCs** consolidating, with reported savings around **$119K/yr** at AllCloud-scale.
- C. NAT Gateway in each VPC.
- D. Direct Connect-only.

**Answer:** B

**Explanation:** The centralized-endpoint-VPC pattern uses a hub VPC with one set of interface endpoints, attached to a Transit Gateway, with Resource Access Manager sharing the private hosted zones. The chapter cites ~7 VPCs as the break-even where central wins (per-AZ interface costs amortize), and AllCloud's published savings of ~$119K/yr. Per-AZ math: $7/mo interface vs $32/mo NAT GW.

---

## Q469 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Pick the right endpoint type for on-prem S3 access

An on-prem data center connects via Direct Connect to a private VPC. Users on-prem need to read S3 directly without going through a NAT or proxy. Which is correct?

- A. Use the **S3 gateway endpoint** in the VPC — on-prem routes through DX into the VPC and uses the gateway endpoint.
- B. Use an **S3 interface endpoint (PrivateLink)** — gateway endpoints are not reachable from on-prem (they're route-table-based and only valid for traffic from inside the VPC). Interface endpoints have ENIs with IPs that on-prem can resolve and route to.
- C. NAT Gateway.
- D. Public S3 endpoint over the internet.

**Answer:** B

**Explanation:** The gateway-vs-interface trap. **Gateway endpoints** (S3, DynamoDB) are route-table prefixes inside the VPC — on-prem traffic via DX/VPN can't use them. **Interface endpoints** have actual ENIs with IP addresses inside your VPC CIDR, so on-prem traffic can resolve and route to them through DX. The cost trade is real: interface endpoints have per-hour and per-GB fees that gateway endpoints lack.

---

## Q470 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Design CMK alias/naming taxonomy

The chapter's CMK matrix is **environment × classification × workload**. What is the recommended alias schema?

- A. `alias/{random-uuid}`.
- B. `alias/cmk/{env}/{class}/{workload}` (e.g., `alias/cmk/prod/pii/risk-model`) — produces 20-40 production CMKs per account, predictable, greppable.
- C. `alias/aws/sagemaker` (use the AWS-managed key).
- D. `alias/default`.

**Answer:** B

**Explanation:** A 3-axis matrix (env: dev/uat/prod × class: public/internal/conf/pii/phi × workload: per project) produces 20-40 CMKs in a mature prod account — enough granularity to crypto-shred a tenant or revoke a class without halting unrelated workloads. The hierarchical alias is human-readable and policy-greppable. C is the AWS-managed key (no rotation control, no cross-account grant, no service-principal restrictions).

---

## Q471 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recall full `KmsKeyId` map across SageMaker API surface

Which SageMaker resource accepts a `KmsKeyId` parameter to encrypt its associated data at rest? (Select THREE)

- A. `CreateTrainingJob` (`OutputDataConfig.KmsKeyId` for S3 outputs + `ResourceConfig.VolumeKmsKeyId` for EBS).
- B. `CreateEndpointConfig` (`KmsKeyId` for endpoint EBS volumes + `AsyncInferenceConfig.OutputConfig.KmsKeyId` + `DataCaptureConfig.KmsKeyId`).
- C. `CreateFeatureGroup` (`OnlineStoreConfig.SecurityConfig.KmsKeyId` + `OfflineStoreConfig.S3StorageConfig.KmsKeyId`).
- D. `InvokeEndpoint` (per-request CMK).
- E. `DescribeTrainingJob` (`KmsKeyId`).

**Answer:** A, B, C

**Explanation:** SageMaker exposes `KmsKeyId` on practically every resource that persists data: training (output + volume), endpoint config (volume + async + data capture), feature store (online + offline), processing, transform, notebook/studio, model registry, AutoML, Ground Truth, Neo edge. `InvokeEndpoint` (D) doesn't take a per-request CMK — encryption is configured on the endpoint config. `DescribeTrainingJob` (E) is read-only.

---

## Q472 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Apply envelope encryption + S3 Bucket Keys for cost

A 100-TB S3 bucket using SSE-KMS with a CMK is generating $40K/month in KMS API costs. What does enabling **S3 Bucket Keys** do?

- A. Replaces KMS with SSE-S3 (loses CMK).
- B. Adds a **bucket-level data key** that the bucket caches and uses to encrypt individual object data keys, reducing KMS `GenerateDataKey`/`Decrypt` API calls by **~99%**, while preserving CMK encryption.
- C. Doubles KMS cost.
- D. Disables encryption.

**Answer:** B

**Explanation:** S3 Bucket Keys are an envelope-encryption optimization: the bucket maintains a short-lived data key (the "bucket key") and uses it to wrap individual object keys, dramatically reducing per-object KMS calls. AWS publishes ~99% reduction in KMS API costs as the marketing figure. CMK is still used at the top of the chain (bucket-key generation), so audit, rotation, and grants still work.

---

## Q473 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Avoid KMS throttling at training-job scale

A 64-node distributed training job is hitting KMS `ThrottlingException` on data-key generation. What are the relevant per-region per-account KMS limits?

- A. There are no KMS limits.
- B. KMS aggregates RPS over a one-minute window: ~**10,000 RPS for symmetric crypto** and ~**5,500 RPS for asymmetric**; mitigations include S3 Bucket Keys, data-key caching in the SDK, and spreading load across multiple CMKs.
- C. Limits are 100 RPS hard.
- D. Limits are per-key not per-account.

**Answer:** B

**Explanation:** KMS exposes shared throughput limits per region per account (around 10K/5.5K depending on op class) with one-minute averaging. Big distributed jobs that issue a `GenerateDataKey` per shard can saturate. Fixes: Bucket Keys at S3 layer, SDK data-key caching (e.g., AWS Encryption SDK with caching CMM), or partition load across multiple CMKs / accounts.

---

## Q474 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Model CMK sprawl economics

What is the rough on-AWS sticker cost for **200 CMKs** with **annual rotation** kept active for 5 years (each rotation creates a new "key material version" billed at $1/mo)?

- A. $1/mo total.
- B. ~**$200/mo for the keys** + ~**$1,000/mo for the cumulative rotation versions by year 5** (each key accumulates ~5 versions × $1/mo). Aggregate annual cost reaches the low-five-figures range, plus API call costs.
- C. Free.
- D. $0.001/key/mo.

**Answer:** B

**Explanation:** KMS pricing: $1/CMK/mo + $1/key-material-version/mo. Annual rotation keeps prior versions (for decryption of old ciphertexts) → linear growth in version count. Sprawl is real; teams consolidate keys via taxonomy and lifecycle/retirement.

---

## Q475 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Use Multi-Region Keys (MRK) for DR / cross-region inference

A team replicates an S3 bucket of model artifacts cross-region via S3 CRR using a Multi-Region Key (MRK). They expect MRK to "just work" for the replicated objects. What's the gotcha?

- A. MRK replicates the key material to other regions, so the same key ID can decrypt in any region — but **S3 Cross-Region Replication does NOT auto re-encrypt** with the destination MRK replica; replicated objects keep their original key references and rely on the MRK replica having the **same key ID** to decrypt locally.
- B. MRK rotates daily.
- C. MRK only works in GovCloud.
- D. MRK is the same as SSE-S3.

**Answer:** A

**Explanation:** MRKs share a key ID across regions (same key material, different ARN). For cross-region reads, the destination region's MRK replica decrypts ciphertext encrypted by its sibling — no re-encryption needed. But **S3 CRR itself does not re-encrypt** by default; if you replicate an object encrypted under a single-region key, the destination object still references that single-region key and may be undecryptable in the destination region. Pre-encrypt with an MRK on the source so the destination replica can decrypt.

---

## Q476 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Map the 5-leg cross-account KMS grant chain

For Account A's SageMaker job to read S3 from Account B encrypted with Account B's CMK, what is the **5-leg policy chain** that must align?

- A. Only the bucket policy matters.
- B. (1) **B's bucket policy** allows A's role; (2) **B's CMK policy** allows A's role to `kms:Decrypt`; (3) **A's IAM policy** allows the role to call `s3:GetObject` and `kms:Decrypt` on B's resources; (4) optionally a **KMS grant** from B to A's role; (5) the role's **trust policy** allows SageMaker to assume.
- C. KMS doesn't support cross-account.
- D. Only IAM identity policy matters.

**Answer:** B

**Explanation:** Cross-account encrypted-S3 access requires all five legs to align: target resource policies (S3 bucket + KMS key), source IAM identity policy, optional KMS grant for finer-grained delegation, and a working trust path for the principal. Missing any leg → `AccessDenied`. This is one of the most common cross-account ML data-sharing footguns.

---

## Q477 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recognize ignored `VolumeKmsKeyId` on Nitro instance-store families

A training job on a `p4d.24xlarge` (Nitro, instance-store NVMe) sets `VolumeKmsKeyId = alias/cmk/prod/training-vol`. Why does it have no effect?

- A. p4d is unsupported by SageMaker.
- B. Instance-store volumes on Nitro families are **already hardware-encrypted with an instance-bound key managed by AWS** that's not exposed via KMS; `VolumeKmsKeyId` is silently ignored because there is no attached EBS volume to encrypt under your CMK.
- C. The role lacks `kms:Decrypt`.
- D. p4d only supports SSE-S3.

**Answer:** B

**Explanation:** This is a published trap: Nitro instance-store NVMe is hardware-encrypted with a per-instance key, not via KMS. `VolumeKmsKeyId` only applies when SageMaker provisions an EBS volume (most instance types) — on instance-store families it has no effect. Audit teams that "require CMK on all volumes" need to recognize Nitro instance-store as already-encrypted-at-rest by AWS hardware.

---

## Q478 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Configure offline Feature Store KMS via `kms:ViaService`

Offline Feature Store writes Parquet to S3. To restrict the CMK so it can **only** be used by SageMaker Feature Store via S3 (not by direct user calls), what's the cleanest condition on the key policy?

- A. `kms:ViaService = s3.{region}.amazonaws.com` with `aws:CalledViaLast = featurestore.sagemaker.amazonaws.com` (or equivalent service-principal restriction on the SageMaker Feature Store service principal).
- B. Remove all conditions.
- C. `kms:GrantConstraintType = AllowList`.
- D. `aws:SourceIp = 10.0.0.0/8`.

**Answer:** A

**Explanation:** Restrict CMK use via `kms:ViaService` so the decrypt call only succeeds when brokered by S3 (the storage layer Feature Store writes to), and pair with `aws:CalledVia` chain checking the SageMaker Feature Store service principal. This prevents principals from calling `kms:Decrypt` directly on Parquet data keys outside of FS reads.

---

## Q479 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Choose DSSE-KMS for federal CNSSP-15

A FedRAMP-High workload requires double-layer server-side encryption for DAR (data-at-rest) confidentiality per CNSSP-15. Which S3 SSE option satisfies this?

- A. SSE-S3 (single-layer AES-256).
- B. **DSSE-KMS** — Dual-layer Server-Side Encryption with KMS, applying two independent encryption layers, meeting CNSSP-15 / federal DAR-CP profile.
- C. CSE-C (client-side custom).
- D. SSE-KMS with a single CMK.

**Answer:** B

**Explanation:** DSSE-KMS was released specifically for CNSSP-15 / federal high-assurance DAR profiles, applying two layers of envelope encryption with KMS — auditable, AWS-side, and meets the "double encryption" requirement. SSE-KMS is single-layer; SSE-S3 is single-layer non-CMK; CSE-C is client-side and harder to operate at scale.

---

## Q480 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Use CloudHSM XKS for FIPS 140-2 Level 3

A defense customer requires their key material to live in **FIPS 140-2 Level 3** validated hardware that they control. Which AWS configuration meets this?

- A. KMS with the AWS-managed CMK.
- B. KMS with a customer-managed CMK in `Origin = AWS_KMS`.
- C. **External Key Store (XKS) backed by CloudHSM** — the KMS key has `Origin = EXTERNAL_KEY_STORE` and the cryptographic operations are proxied to the customer's CloudHSM, which is FIPS 140-2 Level 3 validated; key material never leaves customer hardware.
- D. SSE-S3.

**Answer:** C

**Explanation:** AWS KMS itself is FIPS 140-2 **Level 2** (or Level 3 in specific regions/HSMs). For Level 3 with customer-managed key material, the **External Key Store** pattern lets KMS proxy crypto ops to CloudHSM (or a third-party HSM). The KMS APIs remain the integration surface; the actual keys live outside KMS.

---

## Q481 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Implement GDPR crypto-shredding

A SaaS ML platform with per-tenant CMKs needs to honor GDPR Article 17 (right to erasure) for a customer. Their data is encrypted on S3, Feature Store, and training artifacts under a per-tenant CMK. What's the fastest compliant deletion?

- A. Iterate every S3 object and `DeleteObject`.
- B. **Schedule the tenant's CMK for deletion** (`kms:ScheduleKeyDeletion` with 7-30 day pending-deletion window); once the key is deleted, all ciphertexts under it become unrecoverable — this is **crypto-shredding**. Then run async deletion of the now-unreadable objects for cleanliness.
- C. Disable the bucket.
- D. Change the bucket name.

**Answer:** B

**Explanation:** Crypto-shredding is the per-tenant-CMK pattern that makes GDPR erasure cheap and verifiable. Destroying the key destroys the ability to read all ciphertext encrypted under it. KMS enforces a 7-30 day pending-deletion window (cancellable) before the destruction is irrevocable, which doubles as a safety/legal-hold buffer.

---

## Q482 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recognize CloudWatch Logs grant gap

A training job fails with `User: arn:aws:iam::...:role/SageMakerExecRole is not authorized to perform: kms:GenerateDataKey on resource: arn:aws:kms:...`. The role has KMS permissions for S3. Why is CloudWatch failing?

- A. CloudWatch Logs requires a separate **grant** on the CMK to the `logs.{region}.amazonaws.com` service principal (or a key-policy statement allowing it). Without it, CloudWatch can't write encrypted training logs and the job fails.
- B. CloudWatch doesn't use KMS.
- C. The role needs `logs:*`.
- D. Restart the job.

**Answer:** A

**Explanation:** CloudWatch Logs encryption with a CMK requires the **service principal** `logs.{region}.amazonaws.com` to be granted `kms:GenerateDataKey*`/`Decrypt` via the key policy (or a KMS grant). Identity-policy permissions on the user role aren't enough — the service itself does the encryption call. This is a common cross-service KMS gap.

---

## Q483 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Distinguish Macie / Comprehend / DataBrew / Glue DQ / Bedrock Guardrails

For each tool, pick the canonical PII/PHI scope. (Select TWO correct pairings)

- A. **Macie** — managed PII discovery for **S3 only**.
- B. **Amazon Comprehend `DetectPiiEntities`** — text-document PII detection, returns offsets and entity types.
- C. **DataBrew** — full SQL transformation engine for any data store.
- D. **Glue Data Quality** — built on Macie; finds PII in S3 only.
- E. **Bedrock Guardrails** — only filters profanity, not PII.

**Answer:** A, B

**Explanation:** A and B are correct. Macie is the S3-specific PII discovery service (no RDS, no DynamoDB scanning). Comprehend's DetectPiiEntities returns entity types + offsets for text. C — DataBrew is visual data-prep, not a SQL engine. D — Glue DQ uses DQDL, separate from Macie. E — Bedrock Guardrails filter PII, profanity, denied topics, content policy, prompt attacks.

---

## Q484 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Use Macie managed vs custom identifiers

Macie can detect PII via two identifier types. Which description is correct?

- A. Macie has only one identifier type.
- B. **Managed identifiers** cover ~100 patterns across credentials, financial, and PHI/PII categories (SSN, IBAN, credit cards, AWS keys, NPI, etc.); **custom identifiers** combine a **regex + supporting keywords + proximity (chars)** to reduce false positives — e.g., a regex for an account number that requires the word "Account" within 50 chars.
- C. Macie only supports regex with no keywords.
- D. Macie identifiers are written in Python.

**Answer:** B

**Explanation:** Managed identifiers are pre-built and updated by AWS — three buckets (credentials, financial, PHI/PII). Custom identifiers let you express domain-specific patterns with proximity-constrained keywords to drastically cut false positives. Macie also distinguishes **automated discovery** (sampling-based, always-on) from **classification jobs** (full-scan, scheduled).

---

## Q485 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Build a PII anonymization pipeline (Macie → EventBridge → Lambda → redaction)

You want PII findings on S3 to auto-trigger redaction. Which pipeline is correct?

- A. Macie classification job → finding to **EventBridge** → Lambda invokes **DataBrew/Glue** redaction job → writes sanitized output to a separate bucket.
- B. Macie writes directly to S3 with redaction inline.
- C. Macie triggers SageMaker training to redact.
- D. Macie has no event integration.

**Answer:** A

**Explanation:** Macie findings are surfaced via EventBridge events (`Macie Finding`), which downstream Lambda or Step Functions can route to DataBrew/Glue redaction jobs (column-level mask/hash/encrypt/replace), producing a sanitized copy in a separate prefix/bucket. Macie itself only detects — it doesn't redact in place.

---

## Q486 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Handle GDPR right-to-erasure with Iceberg deletion vectors

A data lake on Iceberg v2 needs to honor right-to-erasure. The team plans to add position-delete files (deletion vectors). What operational gotcha do they need to remember?

- A. Iceberg doesn't support deletes.
- B. Iceberg deletion vectors mark rows as deleted, but **snapshot retention** keeps prior table snapshots that still contain the data — to truly erase, you must also **expire snapshots** older than the erasure SLA and rewrite affected files (partition rewrites), or the data resurrects from any time-travel query.
- C. Deletion vectors auto-rewrite all files immediately.
- D. Iceberg v3 has no deletion.

**Answer:** B

**Explanation:** GDPR-compliant erasure on Iceberg requires expiring all snapshots that still reference the deleted rows and rewriting files (Iceberg `rewrite_data_files` + `expire_snapshots`). Otherwise time-travel queries can resurrect erased data and you've failed Article 17. This is "the right to erasure broke our model" operational story.

---

## Q487 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recall HIPAA BAA scope for AWS ML services

Which of these is **NOT** HIPAA-eligible (in scope of the AWS BAA) as of the chapter's published cut?

- A. Amazon SageMaker (standard).
- B. Amazon Bedrock (added in 2024).
- C. Amazon Macie.
- D. **SageMaker Ground Truth Plus** (Ground Truth standard IS eligible; Ground Truth Plus is NOT).
- E. Amazon Comprehend.

**Answer:** D

**Explanation:** The HIPAA-eligible list expanded considerably (Bedrock added 2024, Macie has always been eligible), but **Ground Truth Plus** (the managed-workforce version) is **not** HIPAA-eligible — only the self-serve **Ground Truth** is. Other non-HIPAA-eligible ML-adjacent services include **Q Developer**, **Fraud Detector**, and **Lookout for Vision** (no longer offered). Always check the AWS BAA list current at the time.

---

## Q488 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Enforce CMK + CloudTrail Data events for PHI buckets

A HIPAA workload stores PHI on S3. Which two controls are required (not optional)? (Select TWO)

- A. **Customer-managed KMS CMK** for encryption (SSE-S3 alone is not sufficient for HIPAA BAA evidence).
- B. **CloudTrail Data events** enabled for the PHI bucket(s) — object-level read/write logging — for audit-evidence.
- C. Public bucket access enabled.
- D. SSE-S3 is acceptable.
- E. CloudTrail Management events alone suffice.

**Answer:** A, B

**Explanation:** PHI buckets require a CMK (auditable rotation, scoped grants, crypto-shredding) and **Data events** (object-level CloudTrail) — Management events log API calls on the bucket itself but not per-object access patterns required by HIPAA audit. SSE-S3 is single-tenant AWS-managed and doesn't satisfy BAA evidence requirements.

---

## Q489 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Enforce data residency via SCP

A bank requires that no SageMaker resource be created outside `eu-west-1` and `eu-central-1`. Which SCP enforces this?

- A. `Effect: Deny`, `Action: "*"`, `Resource: "*"`, `Condition: { StringNotEquals: { "aws:RequestedRegion": ["eu-west-1", "eu-central-1"] } }` (with carve-outs for global services like IAM and CloudFront).
- B. A bucket policy on the data bucket.
- C. KMS key policy alone.
- D. A tag policy.

**Answer:** A

**Explanation:** Residency is most reliably enforced at the **org level via SCP** using `aws:RequestedRegion`. Global services (IAM, CloudFront, Route 53, Support, Organizations) need carve-outs since their APIs run in us-east-1. SCPs apply at OU/account level and supersede identity policies.

---

## Q490 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recognize Bedrock cross-region inference residency risk

A team enables **Bedrock cross-region inference** to get higher availability for a critical Claude workload. Why does compliance flag this as residency-risky and what SCP pattern is recommended?

- A. Cross-region inference can route requests to **any region in the geography (e.g., US system)** which violates strict single-region residency commitments; AWS recommends using SCPs that constrain `aws:RequestedRegion` (and `bedrock:*` action) to specific regions, and **denying the "unspecified" region pattern** that cross-region inference uses internally.
- B. Bedrock cross-region is FIPS-only.
- C. Bedrock cross-region is free, no risk.
- D. Bedrock doesn't support cross-region.

**Answer:** A

**Explanation:** Bedrock cross-region inference profiles route requests across regions inside a geography for resilience/throughput. This **breaks strict residency** because a request submitted in eu-west-1 might be served by eu-central-1 or beyond. The mitigation is an SCP that denies `bedrock:*` when the inference-profile is a cross-region one (the "unspecified region" pattern) — for residency-sensitive workloads, use **single-region inference profiles** only.

---

## Q491 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Calculate Managed Spot training savings and constraints

A training job runs 8 hours on $5/hr instances on-demand. Managed Spot Training quotes 70-90% savings. Which constraints apply? (Select TWO)

- A. `MaxWaitTime` must be **greater than** `MaxRuntime` (so SageMaker can wait for capacity).
- B. **Mandatory checkpointing** for jobs > 1 hour; without checkpoints the cap is **3600 seconds** before interruption costs you the whole run.
- C. Managed Spot is supported on **real-time endpoints**.
- D. Managed Spot stacks with SageMaker Savings Plans.
- E. Managed Spot supports **Warm Pools** for fast iteration.

**Answer:** A, B

**Explanation:** MaxWaitTime > MaxRuntime is the API contract — the wait window must exceed run window. Checkpointing is mandatory for resumable progress; the documented cap without checkpoints is 3600s. C — Spot is **NOT** supported on real-time endpoints, serverless inference, async endpoints, or Studio apps. D — Spot and SP **don't stack** (you pick one). E — Managed Spot is **incompatible with Warm Pools** and heterogeneous clusters.

---

## Q492 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Choose Savings Plan type for a SageMaker fleet

A team runs $200K/yr of training + real-time endpoints in SageMaker. They want to commit. Which Savings Plan applies?

- A. Compute Savings Plan (66% discount) — applies to all AWS compute.
- B. **SageMaker Savings Plan** (~64%) — the only SP that covers SageMaker (Training, Studio, Real-Time, Async, Batch, Processing, Data Wrangler); Compute SP **excludes** SageMaker; there are **no Reserved Instances for SageMaker**.
- C. EC2 Reserved Instances at 75% discount.
- D. There's no SP for SageMaker.

**Answer:** B

**Explanation:** SageMaker SP is purpose-built; Compute SP covers EC2/Fargate/Lambda but **excludes SageMaker**. There are no SageMaker RIs (only SP). 1-yr or 3-yr terms, all-upfront / partial / no-upfront. SP doesn't stack with Managed Spot — pick SP for predictable baseline and Spot for bursty/interruptible.

---

## Q493 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Right-size endpoints with Inference Recommender (not Compute Optimizer)

A platform team wants automated instance-size recommendations for their SageMaker endpoints. Which tool gives that?

- A. **AWS Compute Optimizer** — covers EC2, EBS, Lambda, Fargate, RDS, Aurora, NAT — but **NOT SageMaker** (recap exam trap).
- B. **SageMaker Inference Recommender** — purpose-built for endpoint right-sizing, runs load tests across instance families and recommends $/throughput optima. For training, use **CloudWatch metrics** (CPU/GPU/memory utilization).
- C. Cost Explorer.
- D. Trusted Advisor.

**Answer:** B

**Explanation:** Compute Optimizer's expanding service list still excludes SageMaker — this is a high-frequency exam trap. **Inference Recommender** is the SageMaker-native equivalent: deploys candidate configs, benchmarks, returns Pareto frontier of cost vs latency. For training right-sizing, watch CloudWatch utilization metrics and adjust instance class manually.

---

## Q494 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Pick a Graviton / Inferentia / Trainium target

A bursty ARM-friendly inference workload wants 20-40% cost reduction. Which is the immediate option?

- A. Move to x86 c7i.
- B. **Graviton (g4-class endpoints with Graviton processors)** — 20-40% cheaper for ARM-compatible workloads. For maximum $/throughput on transformer inference, **Inferentia2**; for training large models, **Trainium2** (Anthropic trains on Trainium2).
- C. Move all workloads to Lambda.
- D. Disable autoscaling.

**Answer:** B

**Explanation:** Three AWS silicon families on the cost/performance frontier: **Graviton** (general ARM, 20-40% discount), **Inferentia 2** (purpose-built inference, best $/throughput for many transformer/CNN workloads), **Trainium 2** (training accelerator; Anthropic publicly trains on Trainium2). Migration requires recompilation/quantization but the unit economics flip dramatically.

---

## Q495 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Avoid the "$50K Memorial Day disaster" pattern

A team left a Studio domain and an idle real-time endpoint running over a long weekend; cost was $50K. Which set of guardrails would have prevented this? (Select THREE)

- A. **Studio idle shutdown** policy at the domain (auto-terminate idle apps after N minutes).
- B. **Inference Components scale-to-zero** for the endpoint (or async/serverless if traffic permits).
- C. **`MaxRuntimeInSeconds`** on all training/processing jobs.
- D. Disable CloudWatch.
- E. Disable IAM.

**Answer:** A, B, C

**Explanation:** Three baseline auto-stop controls every SageMaker account should have. Idle shutdown stops Studio cost when nobody's working. IC scale-to-zero (newer endpoints) bills nothing when there's no traffic. `MaxRuntimeInSeconds` caps runaway training. D/E are unrelated and harmful.

---

## Q496 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Apply the SP-vs-Spot decision tree

A team has predictable Studio + real-time-endpoint usage plus bursty experimentation training jobs. What's the optimal commit strategy?

- A. **SP for floor, Spot for ceiling** — buy a SageMaker SP covering the predictable Studio + endpoint baseline (1-yr partial-upfront), and use Managed Spot Training for the bursty experimentation (70-90% off). They don't stack on the same hour but they cover non-overlapping workload classes.
- B. Spot everything.
- C. All-upfront 3-yr SP at peak demand.
- D. No commit.

**Answer:** A

**Explanation:** The chapter's 4-quadrant playbook: predictable + non-interruptible → SP; bursty + interruptible → Spot. Real-time endpoints can't use Spot (not supported), so endpoint baseline is SP-only. Training experiments can use Spot. Cover the predictable floor with SP first; let Spot pick up burst. Don't over-commit (3-yr all-upfront at peak demand strands money if usage drops).

---

## Q497 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Distinguish Cost Explorer / CUR / FOCUS / Budgets / CAD

Map each tool to its primary capability. (Select THREE correct pairings)

- A. **Cost Explorer** — interactive UI for filtering by service/region/tag/account, with forecast and SP recommendations.
- B. **Cost & Usage Report (CUR / CUR 2.0 / FOCUS 1.0)** — detailed hourly billing data exported to S3, queryable via Athena/QuickSight.
- C. **AWS Budgets** — alert thresholds with **Budget Actions** to apply SCP, stop EC2/RDS via SSM, etc.
- D. **Cost Anomaly Detection** — static threshold alarms only.
- E. **Compute Optimizer** — covers SageMaker right-sizing.

**Answer:** A, B, C

**Explanation:** A/B/C are correct. **CAD** is **ML-based** (not static) — that's its whole differentiator vs Budgets. **Compute Optimizer** does **not** cover SageMaker (use Inference Recommender). 2025 added Budget Actions for SageMaker notebooks, but there's still no native action for stopping training jobs — that requires a Lambda subscribed to the budget alarm.

---

## Q498 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Recall the Cost Allocation Tag activation trap

A team has been tagging resources with `Project` for 6 months but Cost Explorer doesn't show `Project` as a filter dimension. Why?

- A. Tags propagate instantly to Cost Explorer.
- B. **Cost Allocation Tags must be explicitly activated** in the Billing console; tagging alone doesn't make them appear in CUR/Cost Explorer. After activation, there's a propagation delay (~24h) and only post-activation usage gets tagged in the billing data. Limit: **500 active keys**.
- C. Cost Explorer doesn't support tag filtering.
- D. They need to upgrade to Enterprise Support.

**Answer:** B

**Explanation:** This is the classic Cost Allocation Tag trap. Resources can be tagged forever, but until the **tag key is activated** in Billing > Cost Allocation Tags, it doesn't show in CUR or Cost Explorer. There's a propagation delay and a hard cap of 500 active keys. Activate early and standardize on a mandatory schema: `Project`, `Environment`, `Owner`, `CostCenter`.

---

## Q499 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Use Bedrock Application Inference Profiles for tenant cost attribution

A SaaS using Amazon Bedrock needs per-tenant token-level cost attribution. Which AWS-native primitive is purpose-built for this?

- A. CUR by account ID.
- B. **Bedrock Application Inference Profiles** with **IAM principal-based attribution** — invocations log the inference profile + principal, enabling token-level cost tracking per tenant, surfaced via CloudWatch metrics and CUR.
- C. Cost Anomaly Detection.
- D. Tag the model.

**Answer:** B

**Explanation:** Application Inference Profiles let you create logical inference identities per tenant/app, then attribute input/output tokens by the invoking IAM principal. Combined with CUR + QuickSight (or CID dashboards), this gives per-tenant $/1K-tokens economics. CAD finds anomalies but doesn't attribute per-tenant.

---

## Q500 — Domain 4: ML Solution Monitoring, Maintenance, and Security
**Objective:** Operate the FinOps lifecycle: Inform → Optimize → Operate

A FinOps lead asks where SageMaker chargeback fits in their maturity model. Which mapping is correct?

- A. **Inform** — CUR + Cost Explorer + tag-activated dashboards visible to every team (showback). **Optimize** — Inference Recommender, SP/Spot decisions, idle-shutdown automation. **Operate** — chargeback (cost lands in business-unit P&L), automated budget actions, anomaly response runbooks. Maturity progresses **Stages 0-5** from no tagging to fully automated chargeback.
- B. FinOps only matters at Stage 5.
- C. Chargeback is the same as showback.
- D. Showback always precedes Optimize and never returns.

**Answer:** A

**Explanation:** The FinOps Foundation lifecycle: **Inform** (visibility), **Optimize** (savings actions), **Operate** (institutionalize). Chargeback ≠ showback: showback is reporting cost to teams without billing; chargeback moves cost into their P&L (creates incentive but requires accurate allocation). Tag-based chargeback maturity stages 0-5 progress from no tagging → mandatory tags → automated enforcement → activated cost-allocation tags → chargeback dashboards → automated chargeback with budget actions. The cycle isn't linear; teams iterate.

---
