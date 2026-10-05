# CAPITAL_ONE.md — Topic 08 Interview-Ready Dossier

> Curated mapping from Topic 08 modules → Capital One Sr Lead AI/ML role conversations. Use this for the final week before an interview to refresh signal-dense points.

## The Capital One DevOps stack (public knowledge as of 2026-05)

| Layer | Tool |
|---|---|
| **SCM** | GitHub Enterprise Cloud (not GitLab) |
| **CI** | Jenkins (CloudBees CI Enterprise); ~500k pipelines, ~50k builds/day |
| **CD** | Internal pattern: Jenkins → ECR → EKS via custom IDP |
| **IaC** | Terraform + Cloud Custodian (their OSS) |
| **K8s** | EKS-dominant; Critical Stack (homegrown) deprecated ~2020 |
| **Model serving** | KServe on EKS (self-hosted; not SageMaker for inference) |
| **Service mesh** | Istio (ambient adoption in progress) |
| **Secrets** | AWS Secrets Manager + ESO |
| **Monitoring** | AMP + AMG + Datadog + X-Ray + rubicon-ml |
| **Governance** | Cloud Custodian (AWS API layer) + Kyverno (K8s API layer) |
| **Compliance** | SOC 2, PCI-DSS v4, SR 11-7, GLBA, FFIEC |

Reference: Topic 04 (AWS) Module 49 + 52-56 for the deep AWS-side dossier.

## Signal-dense talking points (10 things to say)

1. **"I know SR 11-7 model-risk compliance requires immutable audit trails for every model version + decision."** → Topic 07 Module 37 + this Topic Module 18.

2. **"Capital One built Cloud Custodian — Python declarative policy-as-code for AWS — and donated to CNCF in 2018."** → Module 37.

3. **"Their 2019 breach was SSRF + over-permissive IAM + IMDSv1. The fix path that became industry default: IMDSv2 hop-limit=1 + GuardDuty credential-exfiltration detection + Inspector v2."** → Module 18 + 25.

4. **"For K8s admission control they use Kyverno's YAML-policy model — simpler than OPA Gatekeeper for K8s-specific use cases. OPA still wins for cross-tool (TF + K8s + Envoy) Rego libraries."** → Module 34.

5. **"Their model serving runs on EKS via KServe, not SageMaker, because they need control of the serving stack for SR 11-7 audit + cost at scale."** → Module 12 + Topic 04 Module 54.

6. **"They use Jenkins on CloudBees CI Enterprise, not GitLab — air-gap support + the plugin ecosystem + 20-year track record. ~500k pipelines × ~50k builds/day."** → Module 9.

7. **"Their CI/CD uses GitHub Enterprise Cloud as SCM + Jenkins as the engine + OIDC + IAM Role chained to per-account IAM Roles in target accounts for deploy."** → Module 25 + 31.

8. **"For compliance: they pair AWS Config + Conformance Packs (CIS AWS, PCI-DSS) with Cloud Custodian for auto-remediation of low-risk findings."** → Module 37.

9. **"Their MLOps spine: SageMaker for some training, Glue/EMR for ETL, Step Functions for orchestration, EKS+KServe for serving, MLflow + rubicon-ml for tracking + lineage."** → Topic 04 Module 52-54.

10. **"They've been all-AWS since ~2015; closed last datacenter in 2020. Multi-account architecture via Organizations + Control Tower + SCPs at OU level."** → Module 10 + 25.

## Likely interview questions + framing

### "How would you secure a K8s model-serving cluster?"

Layered defense (Module 29):
- **Cloud layer**: VPC private subnets only; IAM least-privilege; KMS envelope encryption
- **Cluster layer**: EKS latest minor; control plane private endpoint; audit logs to CloudWatch
- **Workload layer**: Pod Security Standards `restricted`; NetworkPolicy default-deny per namespace; Kyverno policies enforced at admission
- **Image layer**: Trivy scans in CI, Cosign signed at build, Kyverno verifies signatures at admission
- **Identity layer**: IRSA or Pod Identity for pod IAM; ESO + AWS Secrets Manager
- **Mesh layer**: Istio STRICT mTLS; AuthorizationPolicy per workload-identity
- **Runtime layer**: Falco for anomaly detection; Container Insights
- **Compliance layer**: AWS Config + CIS K8s benchmark + Cloud Custodian remediation

### "Walk me through a model deploy pipeline at Capital One scale"

- Data engineer commits SQL to GHE → Jenkins → Glue ETL job updated
- ML engineer commits training code to GHE → Jenkins job → SageMaker training → MLflow registry
- Model evaluator (rubicon-ml) signs off → manual gate
- ML engineer commits inference container Dockerfile + Helm chart updates
- Jenkins → Trivy scan + Cosign sign → push to ECR
- Jenkins → GitOps repo update (image tag)
- ArgoCD (or KServe operator) syncs → KServe InferenceService updated → progressive canary via Argo Rollouts
- CloudWatch + AMP + Datadog → SLO monitoring → auto-rollback if error spike

### "How do you handle K8s secrets at scale?"

- AWS Secrets Manager as source of truth — single source, automatic rotation for DB creds
- External Secrets Operator in K8s syncs Secrets Manager → K8s Secrets (refresh every hour)
- ESO authenticates via IRSA — no long-lived credentials in cluster
- K8s Secrets use envelope encryption via KMS in EKS config
- Application reads from K8s Secret as env var or volume; rotates via pod restart or hot-reload

### "Tell me about a time you debugged a production K8s issue"

Walk through the diagnostic ladder (Module 66):
1. Pod status (Pending? CrashLoopBackOff? ImagePullBackOff?)
2. `kubectl describe` events
3. `kubectl logs --previous`
4. Service endpoints (selector match?)
5. NetworkPolicy (blocking traffic?)
6. DNS (CoreDNS healthy?)
7. Node (cordoned? resources?)
8. Control plane (apiserver healthy?)
9. CNI (pods getting IPs?)

Have a specific story ready. The framework is what matters.

## Certifications mapped to the role

- **CKA** — operational K8s competence. Required signal for "I can run a cluster, not just kubectl."
- **AWS SAA-C03** → **MLA-C01** (AI/ML Specialty) → **DEA-C01** (Data Engineering) → **SCS-C02** (Security) → **AIP** (AI Practitioner) — the AWS ladder. See Topic 04 Module 57.
- **CKS** — Kubernetes Security — natural follow-up after CKA + 6 months ops experience.
- **Optional**: PMP if pivoting toward EM track.

## What NOT to lead with

- Vague Agile certifications (PSM, CSM, etc.) — Cap One won't care
- HashiCorp certifications (Terraform, Vault) — nice-to-have, not signal
- Kubernetes Application Developer (CKAD) — too overlapping with day-job, weaker signal than CKA
- Cloud Foundation certifications without role-relevance

## After the interview

- LinkedIn add the panelists
- Send specific thank-you notes (not generic) within 24 hours
- Reference one specific topic from each conversation
- If pinged for additional rounds, brush up on the panelist's stated specialty (their LinkedIn)

---

This dossier pairs with Topic 04's CAPITAL_ONE.md and Topic 07's CAPITAL_ONE.md. Together they form the complete interview prep set.
