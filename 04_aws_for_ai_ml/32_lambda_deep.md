# Module 32 — AWS Lambda Deep

> **What this is:** Lambda execution model, cold-start mechanics, SnapStart, container images, layers, concurrency, event sources, observability, and the Capital One serverless-first pattern.

---

## 1. Execution model

Lambda runs on **Firecracker microVMs**. The lifecycle:

1. **Init phase** — microVM boot, runtime init, code load, module imports. *This is the cold-start cost.*
2. **Invocation phase** — handler executes.
3. **Frozen** — microVM held warm; subsequent invocations skip init.
4. **Reclaimed** — eventually killed (typically after several minutes idle).

**Cold start = init phase**. Typical: 100-500 ms for Python/Node; 500-3000 ms for Java/.NET.

## 2. SnapStart (the cold-start killer)

**SnapStart** snapshots a fully-initialized microVM and restores from snapshot on cold start, dramatically reducing init time.

| Runtime | SnapStart status |
|---|---|
| **Java** | GA 2022, free |
| **Python** | GA Nov 2024 (paid: $0.0000015625 per request restoration) |
| **.NET 8+** | GA Nov 2024 (paid) |

**Java with SnapStart**: 80%+ cold-start reduction, free. The killer feature for Lambda-heavy shops.

## 3. Container images

Up to **10 GB container images** (vs 250 MB zip layers). Useful for:
- Heavyweight ML inference workloads.
- Custom runtimes with proprietary dependencies.
- Workloads that need specific OS libraries.

## 4. Layers and Extensions

**Layers** — shared zip artifacts (libraries, custom runtimes). Up to 5 per function.

**Extensions** — managed processes that run alongside your function. Common uses:
- Telemetry (Datadog, New Relic).
- Secrets caching.
- Parameter Store caching.

## 5. Concurrency

| | Description |
|---|---|
| **Account concurrency** | Default 1,000 concurrent executions per region (raisable) |
| **Reserved concurrency** | Reserve a slice for one function (also caps it) |
| **Provisioned concurrency** | Pre-warmed instances; no cold start; pay per instance-hour |

**When to use provisioned concurrency:** latency-critical workloads where cold start matters more than cost.

## 6. Destinations

For async invocations, route success/failure events to:
- SQS, SNS, EventBridge, another Lambda.

Cleaner than the older "DLQ" pattern.

## 7. Event sources

Lambda has built-in integration with:
- **API Gateway** (HTTP).
- **Function URLs** (direct HTTPS without API Gateway).
- **S3, EventBridge, CloudWatch Events**.
- **SQS, SNS, MSK, Kinesis, DynamoDB Streams**.
- **Application Load Balancer**.

## 8. Lambda + VPC

Initially (pre-2019) putting Lambda in VPC added ~10s cold-start latency. AWS rebuilt the ENI model as **Hyperplane ENIs** (Sep 2019): ENI is pre-created and shared across invocations, eliminating the per-cold-start ENI cost.

**Lambda + VPC is now a non-issue** for cold start.

## 9. NAT GW cost trap

Lambda in VPC reaching the internet typically goes through NAT GW. At scale, NAT GW data-processing charges dominate.

**Fix:** VPC endpoints for AWS services. The big ones — S3 (gateway, free), DynamoDB (gateway, free), SQS, SNS, Kinesis, MSK, KMS, Secrets Manager — all have Interface endpoints. The bill drops significantly.

## 10. Observability

- **Lambda Insights** (CloudWatch agent) — per-invocation memory, duration, init time.
- **X-Ray** for distributed tracing.
- **Structured logging** to CloudWatch Logs.
- **Lambda Telemetry API** (extensions consume it for third-party APM).

## 11. Capital One serverless-first patterns

Per their re:Invent 2024 talk *"Celebrating 10 years of pioneering serverless"* (Catherine McGarvey):

- **Lambda is the centerpiece** of the architecture.
- **CodeDeploy gradual traffic shifting** — 2%/min canary deploys on Lambda.
- **Internal Kinesis SDK pattern** — Producer Lambda → KDS → Processor Lambda → KDS or DDB → Sink Lambda → S3 / Firehose.
- **Step Functions for orchestration**, Lambda for individual steps.
- **80% latency reduction** on check-processing pipeline via Step Functions + Lambda.

**Talking point:** *"Coming from an Azure-heavy shop, I see the Lambda serverless-first culture as the operational backbone — Lambda + Step Functions + DynamoDB + Kinesis is the platform default and ML pipelines integrate into it rather than replacing it."*

## 12. Pricing

- **Per request**: $0.20 per 1M requests.
- **Per duration**: $0.0000166667 per GB-second.
- **Provisioned concurrency**: $0.0000041667 per GB-second (~25% of execution price for warm capacity).
- **SnapStart restore for Python/.NET**: $0.0000015625 per request restoration.

**Example**: 1B invocations/month × 100ms duration × 256MB → ~$575/month execution + $200 request fee = ~$775/month.

## 13. Pitfalls

- **NAT GW cost** from Lambda in VPC to public internet.
- **Reserved concurrency = 0** accidentally → all invocations throttled.
- **Provisioned concurrency on rarely-invoked functions** → wasted spend.
- **Long-running Lambda** (15 min max) — graduate to Fargate or Step Functions.
- **Cold start in latency-critical paths** → use SnapStart or provisioned concurrency.

## 14. Sanity check

1. What does SnapStart do, and which runtimes are supported in 2026?
2. When does provisioned concurrency pay off?
3. Why is Lambda + VPC no longer a cold-start problem?
4. What's the NAT GW trap, and what's the fix?
5. Walk through the Capital One Kinesis SDK pattern.

## 15. Cross-references

- **Module 15** — Step Functions (Lambda's natural orchestrator)
- **Module 18** — DynamoDB (Lambda + DDB Streams)
- **Module 29** — Kinesis (Lambda processor pattern)
- **Module 8** — VPC endpoints (Lambda NAT cost fix)

## Primary sources

- [`Lambda_Operator_Guide.html`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/Lambda_Operator_Guide.html)
- Research report: [`08_compute_for_ml.md`](../../research_inputs/04_aws_for_ai_ml/08_compute_for_ml.md)
