# Module 28 — Amazon MSK Deep

> **What this is:** Apache Kafka managed by AWS — MSK Provisioned vs Serverless, KRaft mode, IAM auth, MSK Connect, MSK Replicator, Glue Schema Registry. The streaming backbone for event-driven architectures.

---

## 1. MSK Provisioned vs Serverless

| | **MSK Provisioned** | **MSK Serverless** |
|---|---|---|
| Sizing | You choose broker instance types (kafka.m5.*, kafka.m7g.*) | AWS sizes automatically |
| Pricing | Per broker-hour + storage + data | Per-partition-hour + per-message + storage |
| Cluster control | Full | Limited |
| Use case | Predictable throughput, custom Kafka config | Variable workloads, small teams |
| KRaft mode | Yes (replacing ZooKeeper) | Yes |

**MSK Serverless** (GA 2022) abstracts broker management. You define topics, MSK handles cluster scaling. Great for getting started; less control.

## 2. KRaft vs ZooKeeper

KRaft (Kafka Raft, GA in Apache Kafka 3.3+) **eliminates ZooKeeper** as the metadata coordinator. MSK now supports KRaft natively. New clusters should default to KRaft.

ZooKeeper-managed clusters still exist and AWS supports them, but the future is KRaft.

## 3. Authentication

Three options:

| | **IAM SASL/AWS_MSK_IAM** | **SASL/SCRAM** | **mTLS** |
|---|---|---|---|
| Mechanism | AWS IAM with SigV4 | Username/password in Secrets Manager | X.509 client certs |
| Easiest? | Yes for AWS workloads | Need creds store | Complex PKI |
| Cross-account | Yes via IAM trust | Manual | Manual |
| **AWS-native pick** | ✓ | | |

**IAM auth is the default pick** on AWS — no static creds, integrates with IRSA / Pod Identity / Lambda execution roles. Capital One almost certainly uses this exclusively given their "no static creds" policy.

## 4. MSK Connect

Managed Kafka Connect — connectors as fully managed workers.

- **Source connectors** — Debezium (CDC), JDBC, S3, Kinesis.
- **Sink connectors** — S3, OpenSearch, Redshift, Snowflake, JDBC.
- Custom plugins uploaded as JARs.

Used when you want CDC from Aurora/RDS into Kafka, or Kafka topic to S3 archive without a custom consumer.

## 5. Glue Schema Registry

The AWS-managed schema registry for Avro, JSON Schema, Protobuf.

- Schemas have versions; compatibility rules (BACKWARD, FORWARD, FULL, NONE) enforce contract evolution.
- Integration with MSK producers (`com.amazonaws.services.schemaregistry.serializers.avro.AWSKafkaAvroSerializer`) and Kinesis.
- **Serializer caches schemas client-side**, registers new schemas on first encounter.

## 6. MSK Replicator

Cross-region (and within-region) Kafka replication. Lower-overhead than MirrorMaker 2; AWS-managed; preserves consumer offsets for active-passive DR.

## 7. Producer/Consumer patterns

- **Idempotent producer** — `enable.idempotence=true`; safe retries without duplicates within a partition.
- **Exactly-once semantics (EOS)** via transactions (`initTransactions`, `beginTransaction`, `sendOffsetsToTransaction`, `commitTransaction`).
- **Consumer groups + offsets** — Kafka-managed offsets in `__consumer_offsets`. Partition assignment via strategies:
  - `RangeAssignor` — older default
  - `RoundRobinAssignor`
  - `CooperativeStickyAssignor` — **the modern pick**; cooperative rebalances avoid stop-the-world

## 8. MSK vs Self-managed Kafka vs Confluent Cloud on AWS

| | MSK | Self-managed (EC2/EKS) | Confluent Cloud on AWS |
|---|---|---|---|
| Ops effort | Low | High (you manage brokers) | Lowest |
| Cost (at scale) | Mid | Lowest (with engineer cost) | Highest |
| Feature parity with OSS Kafka | Latest stable Apache versions | Latest, including pre-releases | Confluent extensions (KSQL, Schema Registry, Cluster Linking) |
| Best for | AWS-native shops with mid-scale Kafka | Cost-sensitive scale, complex Kafka use | Heavy Kafka use needing Confluent features |

## 9. 2024–2026 changes

- **MSK Serverless GA** (2022, but feature-rich by 2024).
- **MSK Replicator GA** (2023).
- **KRaft on MSK** GA (2024).
- **IAM auth GA in all regions** (2022+, but now default).

## 10. Pitfalls

- **Partition rebalancing pain** — bad partition assignment strategies cause stop-the-world rebalances. Use `CooperativeStickyAssignor`.
- **Replication factor 1** — never. Default to 3 (one per AZ).
- **Acks=1 producer** — risk of data loss on broker failure. Use `acks=all` for durability.
- **Schema-less producers** — schema drift breaks downstream consumers. Use Glue Schema Registry.
- **MSK Serverless not appropriate** for high-fanout, ultra-low-latency workloads → use Provisioned.

## 11. Capital One lens

Capital One's public tech blog confirms **Kinesis** is the primary serverless event bus. MSK appears where Kafka-native consumers (Debezium CDC, acquired-company apps) already existed. The pattern: Kinesis for new internal services; MSK where Kafka was already in the picture.

If you're interviewing, ask: "What's the split between Kinesis and MSK across LOBs at Capital One? When do you pick MSK over Kinesis for new event buses?"

## 12. Sanity check

1. MSK Provisioned vs Serverless — when does Provisioned make sense?
2. What does KRaft replace and why does it matter?
3. Why is IAM SASL/AWS_MSK_IAM auth the AWS-native default?
4. What is `CooperativeStickyAssignor` and why is it preferred?
5. When is Confluent Cloud worth the premium over MSK?

## 13. Cross-references

- **Module 29** — Kinesis family (the AWS-native alternative)
- **Module 15** — orchestration (EventBridge Pipes can consume MSK)
- **Module 22** — Redshift Streaming Ingestion from MSK
- **Module 38** — SageMaker model inference triggered by Kafka events

## Primary sources

- [`MSK_Developer_Guide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/MSK_Developer_Guide.pdf)
- [`MSK_Best_Practices.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/MSK_Best_Practices.html)
- Research report: [`07_streaming.md`](../../research_inputs/04_aws_for_ai_ml/07_streaming.md)
