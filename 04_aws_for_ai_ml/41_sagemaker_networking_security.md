# Module 41 — SageMaker Networking & Security

> **What this is:** SageMaker VPC mode, no-internet mode, KMS encryption, private endpoints, IAM patterns, multi-account ML.

---

## 1. VPC mode

By default, SageMaker training/inference runs in **AWS-managed VPC** outside your VPC. For regulated workloads, **VPC mode** runs in **your** VPC:

- Training job ENIs live in your subnets.
- Inference endpoint ENIs live in your subnets.
- Studio Domains can also be VPC-only.

## 2. No-internet egress mode

**Studio Domain "VPC-only" + no NAT GW** = no internet access for the SageMaker workload. All AWS API calls must go via VPC endpoints.

**Required endpoints for typical workloads:**
- `s3` (Gateway)
- `sagemaker.api` (Interface)
- `sagemaker.runtime` (Interface)
- `kms` (Interface)
- `ecr.dkr` + `ecr.api` (Interface — for pulling container images)
- `sts` (Interface)
- `cloudwatch logs` (Interface)
- `secretsmanager` (Interface — if used)

**This is the regulated-finance default.** Capital One's SageMaker Studio Domains likely run in this mode.

## 3. KMS encryption

SageMaker uses KMS for:
- **Studio EFS** — Domain-level EFS that holds user-profile homes.
- **Training Job EBS** — local storage on training instances.
- **Inference endpoint EBS**.
- **S3 model artifacts** (when uploaded).
- **CloudWatch Logs** (optional).

Each can use **customer-managed KMS keys (CMKs)** for compliance.

## 4. Private SageMaker API endpoints

The SageMaker control plane API itself (creating training jobs, endpoints, etc.) can be reached via **VPC Interface endpoint** (`com.amazonaws.<region>.sagemaker.api`). Required for "no internet" Studio.

## 5. IAM execution roles

Every SageMaker resource has an **execution role**:
- Training job execution role: permissions to read input S3, write output S3, pull container.
- Endpoint execution role: similar.
- Studio Domain execution role: per-user-profile.

**Best practice:** scope each role narrowly — prefix-scoped S3 access, KMS decrypt on specific keys, no `s3:*`.

## 6. Cross-account ML patterns

**Cross-account Model Registry:**
- Producer account registers a model.
- Consumer accounts pull the model via cross-account model package share (RAM).

**Cross-account training:**
- Pull training data from a different account's S3 (resource policy + KMS grant).
- Run in your account's VPC.

**Cross-account inference:**
- Endpoint in your account.
- Invoked from another account via cross-account IAM.

## 7. Custom Studio images

Custom Docker images vendored to ECR can be used as Studio kernels:
- Pre-installed libraries.
- Org-mandated security tools.
- Pinned framework versions.

The path for "no `pip install` from public PyPI in regulated workloads."

## 8. Network restrictions for sensitive workloads

Beyond no-internet:
- **No public ALB** in front of endpoints — use API Gateway private endpoints.
- **PrivateLink to consumer accounts** for inference (vs cross-account TGW).
- **VPC Flow Logs** capturing all SageMaker ENI traffic.
- **Network Access Analyzer** scopes enforcing reachability invariants.

## 9. Internet-free Studio domains

When fully locked down:
- `pip install` only from a **private PyPI mirror** (AWS CodeArtifact, JFrog).
- Git only from a private repo via VPC endpoint or hosted internally.
- No npm / Maven from public — all proxied.

## 10. Multi-account ML topology

Typical regulated-finance pattern:
- **Training account** — runs Training Jobs, owns experiment data.
- **Model Registry account** — central registry, approval gates.
- **Serving accounts** (per LOB or per env) — deploy from Registry, run endpoints.
- **Audit account** — Lineage + CloudTrail aggregation.

## 11. 2024-2026 changes

- **SageMaker private endpoints** matured.
- **Studio Domain CMK** broadly supported.
- **Cross-account Model Registry** sharing improved.
- **Custom Studio images** for Code Editor too.

## 12. Pitfalls

- **Missing one VPC endpoint** → SageMaker job hangs.
- **KMS key policy** not granting SageMaker service principal → cryptic encryption failures.
- **VPC mode without enough subnet IPs** → distributed training fails.
- **NAT GW left on** in "no-internet" Studio → no actual isolation.

## 13. Capital One lens

- **VPC-only, no-internet Studio Domains** with all AWS service access via PrivateLink.
- **Custom Studio images** vendored with Databolt clients, internal libraries.
- **Cross-account Model Registry** centralized; per-LOB serving accounts.
- **CMK per LOB** with 90-day rotation.

## 14. Sanity check

1. What does "VPC-only, no-internet" SageMaker mean and what endpoints are required?
2. What does the SageMaker execution role typically need access to?
3. Multi-account ML topology — name the four account roles.
4. Why use custom Studio images in regulated finance?
5. What's the network architecture for serving SageMaker endpoints to other accounts?

## 15. Cross-references

- **Module 2** — IAM execution roles
- **Module 6, 8** — VPC + PrivateLink
- **Module 50** — KMS deep
- **Module 52** — compliance posture

## Primary sources

- SageMaker VPC Security docs (archived)
- Research report: [`09_sagemaker.md`](../../research_inputs/04_aws_for_ai_ml/09_sagemaker.md)
