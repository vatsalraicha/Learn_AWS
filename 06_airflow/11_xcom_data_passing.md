# 11 — XCom & data passing: limits, custom XCom backend, anti-patterns

## Why this module exists

XCom is for **small** task-to-task data. Use it wrong and you DDoS your metadata DB.

---

## 1. XCom mechanics

`@task` return values → stored in metadata DB `xcom` table → next task reads.

```python
@task
def a() -> dict:
    return {"count": 1234, "checksum": "abc"}

@task
def b(stats: dict):
    log.info(stats["count"])

b(a())
```

Under the hood: `a` writes `{"count":1234,"checksum":"abc"}` to xcom; `b` reads it via the `task_instance.xcom_pull()` API.

Default backend: metadata DB, serialized as JSON.

---

## 2. Size limits

| Backend | Soft warning | Practical max |
|---|---|---|
| Postgres `bytea` | 48 KB | ~1 GB (but DB-slow) |
| MySQL `LONGBLOB` | 48 KB | ~4 GB (very slow) |
| SQLite | 48 KB | ~1 GB |

**Production target: keep XCom < 1 MB. Ideal: < 100 KB.**

Logs warn at 48 KB; `enable_xcom_pickling=False` (default) blocks pickle.

---

## 3. Custom XCom Backend

For data > 100 KB, write a custom backend that stages data to object storage:

```python
# my_xcom.py
from typing import Any
import json, uuid
from airflow.models.xcom import BaseXCom
import boto3

class S3XComBackend(BaseXCom):
    PREFIX = "xcom://"
    BUCKET = "myorg-airflow-xcom"

    @staticmethod
    def serialize_value(value, **kwargs) -> str:
        # Small values: native serialization
        if isinstance(value, (int, float, str, bool)) or (isinstance(value, dict) and len(json.dumps(value)) < 1024):
            return BaseXCom.serialize_value(value)
        # Large: stage to S3
        key = f"xcom/{uuid.uuid4()}.json"
        boto3.client("s3").put_object(
            Bucket=S3XComBackend.BUCKET, Key=key,
            Body=json.dumps(value).encode(),
            ServerSideEncryption="aws:kms",
        )
        return BaseXCom.serialize_value(f"{S3XComBackend.PREFIX}{key}")

    @staticmethod
    def deserialize_value(result) -> Any:
        v = BaseXCom.deserialize_value(result)
        if isinstance(v, str) and v.startswith(S3XComBackend.PREFIX):
            key = v[len(S3XComBackend.PREFIX):]
            obj = boto3.client("s3").get_object(Bucket=S3XComBackend.BUCKET, Key=key)
            return json.loads(obj["Body"].read())
        return v
```

Configure:

```ini
[core]
xcom_backend = my_xcom.S3XComBackend
```

Now any return value larger than a threshold is staged to S3 transparently; smaller stays in metadata DB. Apps don't change.

Built-in alternatives:
- **Airflow's S3 XCom backend** in `apache-airflow-providers-amazon` (since 2.7).
- **GCS XCom backend** in providers-google.
- **Azure Blob XCom backend** in providers-microsoft-azure.

For Airflow 2.8+ the Object Storage abstraction makes this simpler.

---

## 4. Anti-patterns

| Anti-pattern | Why bad | Fix |
|---|---|---|
| Returning a Pandas DataFrame | Blows up metadata DB | Write to S3/Parquet; return path |
| Returning a NumPy array | Same | Write to S3; return path |
| Returning a Pickled custom class | Security + version-skew risk | JSON-serializable types only |
| `xcom_push` of secrets | Logged + visible in UI | Use Secrets Backend |
| Chaining many tasks with growing XCom payloads | Each task duplicates the data | Stage to S3 once; downstream tasks read from path |
| XCom as a queue | Wrong primitive; use Pool or message queue | Pool / external queue |

---

## 5. The data-flow design pattern

For a pipeline processing 100K records → 10K aggregations → final report:

**Anti-pattern**:
```python
records = extract()       # 100K rows in XCom — disaster
agg     = aggregate(records)
report  = build(agg)
```

**Right pattern**:
```python
@task
def extract() -> str:
    # write to S3, return path
    path = f"s3://myorg-pipelines/{{ run_id }}/records.parquet"
    write_parquet(records, path)
    return path

@task
def aggregate(input_path: str) -> str:
    # read from S3, write to S3
    df = pd.read_parquet(input_path)
    out_path = f"s3://myorg-pipelines/{{ run_id }}/agg.parquet"
    df.groupby(...).agg(...).to_parquet(out_path)
    return out_path

@task
def report(agg_path: str): ...
```

XCom carries S3 paths (a few hundred bytes). Data lives in S3. Scales.

---

## 6. The Object Storage abstraction (2.8+)

Airflow now ships a portable `ObjectStoragePath`:

```python
from airflow.io.path import ObjectStoragePath

base = ObjectStoragePath("s3://myorg-pipelines/", conn_id="aws_default")

@task
def write(data):
    path = base / "{{ run_id }}" / "records.parquet"
    with path.open("wb") as f:
        f.write(serialize(data))
    return str(path)
```

Works with `s3://`, `gs://`, `abfs://` (Azure Data Lake Gen2), `file://`. Avoids hard-coupling to one cloud provider in DAG code.

---

## 7. Datasets vs XCom

For larger inter-DAG data flow, **Datasets are the right primitive** (module 06). XCom is for within-a-DAG-run task communication; Datasets are for cross-DAG dataflow with built-in triggering.

---

## Sanity check

1. The 48 KB threshold is what — a hard limit or a warning?
2. Why does returning a Pandas DataFrame via XCom hurt?
3. Custom XCom backend — what's the canonical pattern for "small values inline, large values to object storage"?
4. Object Storage abstraction (2.8+) — what does it give you over hard-coded S3 SDK?
5. Datasets vs XCom — when do you reach for each?

---

## Sources

- [XCom docs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html)
- [Custom XCom Backends](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html#custom-backends)
- [Object Storage](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/objectstorage.html)
- [Airflow Improvement Proposal AIP-58 (Object Storage)](https://cwiki.apache.org/confluence/display/AIRFLOW/AIP-58+Airflow+Object+Storage)

→ Next: [12 — Data-flow design](12_data_flow_design.md)
