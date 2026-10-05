# Module 29 — Kinesis Family + Flink

> **What this is:** Kinesis Data Streams (KDS), Amazon Data Firehose (formerly Kinesis Firehose), Managed Service for Apache Flink (formerly Kinesis Data Analytics), EventBridge, EventBridge Pipes. The decision matrix vs MSK.

---

## 1. Kinesis Data Streams (KDS)

Shard-based stream — the "Kafka, but serverless and AWS-native."

- **Shard** = unit of throughput: 1 MB/s in, 2 MB/s out (or with **Enhanced Fan-Out** 2 MB/s per consumer).
- **Capacity modes**: Provisioned (you size shards) and On-Demand (auto-scales).
- **Retention** — 24h default, configurable up to 365 days (long retention $$).
- **Pricing** — per shard hour + PUT payload units (25 KB each). On-Demand more expensive but auto-scales.

**Producer (KPL, Kinesis Producer Library)** vs **Consumer (KCL)** — high-level libraries with batching, retries, checkpointing.

**Enhanced Fan-Out (EFO)** — per-consumer dedicated 2 MB/s pipe. Solves the noisy-neighbor problem at the cost of $0.015/hr per consumer-shard.

## 2. Amazon Data Firehose (formerly Kinesis Firehose)

Fully managed delivery. **Source → buffer → optional transform → destination.**

- **Destinations**: S3, Redshift, OpenSearch, HTTP endpoint, Splunk, MongoDB, Snowflake, Datadog, New Relic.
- **Buffer hints**: by size (1-128 MB) or time (60-900 sec) — whichever first.
- **Transformations via Lambda**: per-record transform inline. Heavy use for PII redaction, format normalization.
- **Format conversion**: JSON → Parquet/ORC inline (using a Glue Catalog schema).
- **Dynamic partitioning** — keys from record content drive S3 path partitioning.

The "fire and forget" pattern — Firehose handles retry, buffering, format conversion, partitioning. **Capital One's pattern** per their tech blog: Kinesis → Lambda → S3, with Firehose for the simple straight-to-S3 sink.

## 3. Managed Service for Apache Flink (MSF, formerly Kinesis Data Analytics for Apache Flink)

Managed Flink for stream processing — windowing, joins, sessions, ML-via-PyFlink.

- **Flink jobs** run as Java/Scala/Python applications.
- **Studio notebooks** — Zeppelin-based interactive Flink for exploration.
- **Snapshots and savepoints** — versioned state for upgrade safety.
- **Autoscaling** — pay-per-KPU (Kinesis Processing Unit).
- **Flink SQL** for declarative stream processing.

When you need stateful stream processing (windows, sessions, exactly-once stream-stream joins) — MSF.

## 4. EventBridge

Default event bus (every account has one) + custom event buses + partner event buses (SaaS integrations).

- **Rules** match event patterns (JSON), route to up to 5 targets.
- **Schedules** (GA 2022) — cron + one-time scheduler, replaces CloudWatch Events scheduling.
- **API Destinations** — call external HTTP endpoints as targets.

## 5. EventBridge Pipes

Source → optional Filter → optional Enrich → Target. A serverless point-to-point pattern.

- **Sources**: SQS, Kinesis, MSK, DynamoDB Streams, Self-managed Apache Kafka.
- **Filter**: pattern match on event content (no compute).
- **Enrich**: Lambda, Step Functions, API Gateway, API Destinations.
- **Targets**: 14+ AWS services including Lambda, Step Functions, SQS, SNS, ECS, SageMaker pipelines.

Replaces the "SQS → Lambda → filter → transform → call SageMaker endpoint" boilerplate with declarative config.

## 6. Decision framework: Kinesis vs MSK vs EventBridge vs SQS/SNS

| Scenario | Pick |
|---|---|
| AWS-native event bus, no Kafka ecosystem need | **KDS** |
| Existing Kafka producers/consumers (Debezium, acquired company apps) | **MSK** |
| Just deliver records to S3/Redshift/OpenSearch | **Firehose** |
| Stateful stream processing (windows, joins, sessions) | **MSF (Flink)** |
| Cross-service event-driven architecture (S3 events, CloudWatch alarms, custom events) | **EventBridge** |
| One source → filter/enrich → one target | **EventBridge Pipes** |
| Queue with single consumer / pub-sub fanout | **SQS / SNS** |

## 7. Pricing comparison (rough)

For 100 MB/s sustained throughput:

- **KDS Provisioned** — ~100 shards × $0.015/hr = $1,100/mo + PUT payload + data egress
- **KDS On-Demand** — ~$0.04/GB ingest + $0.04/GB retrieval = ~$8k/mo at 100 MB/s
- **MSK Provisioned** — 3 kafka.m7g.large brokers ~$0.42/hr each = ~$900/mo + storage + data
- **Firehose** — $0.029/GB to S3 = ~$7.5k/mo at 100 MB/s
- **MSF** — per-KPU pricing; for a moderate Flink job ~$0.11/KPU-hr × 4 KPUs = $320/mo

## 8. Capital One serverless streaming SDK pattern

Per [their tech blog](https://www.capitalone.com/tech/cloud/serverless-streaming/), Capital One built an internal SDK abstracting Kinesis + Lambda source/processing/sink:

```
Producer Lambda → KDS → Processor Lambda → KDS or DDB → Sink Lambda → S3 / Firehose
```

- IAM-native auth (no static creds).
- Per-LOB shard isolation.
- 7-day retention covers replay window.
- Firehose to S3 closes the loop for cold storage.

This is the AWS-native pattern Capital One built into a reusable SDK. **Talking point:** *"I'd expect the serverless streaming SDK to default to Kinesis with IAM auth, Firehose for cold archive, and EventBridge Pipes for cross-account fan-in."*

## 9. Pitfalls

- **Hot shard** — bad partition key → one shard saturated. Use uniform-distribution keys.
- **Firehose buffer tuning** — too small → many small S3 files; too large → high end-to-end latency.
- **EventBridge throttle limits** — per-account quota; for high-throughput direct invocation, consider Kinesis.
- **MSF state size** — large state → slow snapshots → blocked deployments.

## 10. Sanity check

1. What's an EFO consumer and when do you need it?
2. When would you pick MSF over a simpler Lambda + DynamoDB stateful pattern?
3. EventBridge Pipes vs Lambda glue — what's the boilerplate it replaces?
4. Walk through the Capital One Kinesis SDK pattern.
5. Firehose dynamic partitioning — what does it do?

## 11. Cross-references

- **Module 28** — MSK (the Kafka alternative)
- **Module 22** — Redshift Streaming Ingestion (consume from KDS/MSK)
- **Module 32** — Lambda (the de-facto Kinesis processor)
- **Module 15** — EventBridge Pipes as orchestration glue

## Primary sources

- [`Kinesis_Data_Streams_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Kinesis_Data_Streams_Best_Practices.html)
- [`Firehose_Developer_Guide.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Firehose_Developer_Guide.html)
- [`MSF_Apache_Flink.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/MSF_Apache_Flink.html)
- [`Streaming_Data_Solutions_Whitepaper.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Streaming_Data_Solutions_Whitepaper.pdf)
- [`c1tech_serverless_streaming.html`](../../research_inputs/04_aws_for_ai_ml/downloads/capital_one/c1tech_serverless_streaming.html) — Capital One internal SDK pattern
- Research report: [`07_streaming.md`](../../research_inputs/04_aws_for_ai_ml/07_streaming.md)
