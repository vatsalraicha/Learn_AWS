# Module 51 — Governance & Policy-as-Code

> **What this is:** Control Tower, Landing Zone Accelerator, Organizations + SCPs + RCPs, **Cloud Custodian (Capital One's open-source)**, cfn-guard, cdk-nag, AWS Audit Manager.

---

## 1. The governance landscape

| Tool | What it does |
|---|---|
| **Control Tower / LZA** | Multi-account landing zone (Module 1) |
| **AWS Organizations** | Org tree, SCPs, RCPs |
| **Cloud Custodian** | YAML policy-as-code for runtime governance (the Capital One-built tool) |
| **cfn-guard** | CloudFormation policy-as-code (deploy-time) |
| **cdk-nag** | CDK construct guardrails (synth-time) |
| **CloudFormation Hooks** | Deploy-time policy enforcement |
| **AWS Audit Manager** | Regulatory framework attestation |

## 2. SCPs and RCPs (recap)

(Detailed in Module 1.)

- **SCPs** bound principal permissions.
- **RCPs** (GA Nov 2024) bound resource access — close the cross-org access gap that SCPs couldn't.

## 3. Cloud Custodian — the Capital One project

**Cloud Custodian** ([github.com/cloud-custodian/cloud-custodian](https://github.com/cloud-custodian)) is YAML-based policy-as-code for AWS, GCP, Azure.

- **Originally built by Capital One**.
- **CNCF Incubating** since Sep 2022.
- Apache 2.0.
- 2026: nearing ten-year anniversary.

### c7n architecture

Policies are YAML:

```yaml
policies:
  - name: terminate-untagged-ec2
    resource: ec2
    filters:
      - "tag:CostCenter": absent
    actions:
      - type: notify
        to: [security@example.com]
        transport:
          type: sns
          topic: arn:aws:sns:...:security-alerts
      - type: stop
```

Custodian discovers AWS resources via API, filters them, applies actions (tag, stop, terminate, notify).

### Common patterns

- **Tag enforcement** — find untagged resources, notify-then-act.
- **Encryption enforcement** — find unencrypted EBS, RDS, S3; remediate.
- **Public access prevention** — find S3 buckets with public ACLs; lock down.
- **Idle resource shutdown** — find EC2/RDS not used in 7 days; stop.
- **Cost guardrails** — find oversized instances; recommend right-sizing.

### Dry-run discipline

Always test policies in `--dryrun` mode first. Custodian's actions can be destructive (terminate, delete) — dry-run shows what would happen without doing it.

### Mode: deployment patterns

- **Pull mode** — Lambda triggered on schedule (EventBridge).
- **Event mode** — Lambda triggered on CloudTrail event (real-time enforcement).
- **CLI mode** — run from a CI/CD pipeline.

### Why Capital One built this

Custodian was Capital One's answer to **continuous, runtime, policy-as-code governance** — preventive measures (SCPs) plus detective + responsive measures (Custodian).

**Reading recommendation:** before any interview, spend 90 minutes reading the [Cloud Custodian docs](https://cloudcustodian.io/docs/) and three example policies. You will impress interviewers by referencing it by name and identifying which AWS APIs it wraps.

## 4. cfn-guard

CloudFormation policy-as-code. Written in Rust; declarative DSL:

```
let ec2_instances = Resources.*[ Type == 'AWS::EC2::Instance' ]

rule require_tags when %ec2_instances !empty {
  %ec2_instances.Properties.Tags[*].Key == /CostCenter/
}
```

Run in CI to block deployments that violate rules. Native CloudFormation Hooks integration.

## 5. cdk-nag

CDK construct that scans your CDK app at **synth time** for security issues:

```typescript
import * as cdkNag from 'cdk-nag';
cdk.Aspects.of(app).add(new cdkNag.AwsSolutionsChecks());
```

Catches: unencrypted resources, IAM wildcards, missing logging, public exposure.

**Capital One uses cdk-nag heavily** (per re:Invent 2024 talk by Ishu Gupta).

## 6. CloudFormation Hooks

**Pre-deployment policy enforcement** — fires before a stack creates/updates/deletes resources. Can block based on rules.

The "infra-level gatekeeper" — works even if someone bypasses your CI/CD.

## 7. AWS Audit Manager

Automated compliance evidence collection.

**Frameworks**:
- AWS Best Practices, CIS, NIST 800-53, NIST CSF.
- PCI-DSS, SOC 2, HIPAA, GDPR.
- **New 2024**: GenAI / AI-ML frameworks.

Audit Manager continuously collects evidence from CloudTrail, Config, etc., maps to control statements, produces reports for auditors.

## 8. The four pillars (when to use what)

1. **Preventive** — SCPs, RCPs, IAM permission boundaries.
2. **Deploy-time** — cdk-nag (synth), cfn-guard (template), CloudFormation Hooks (deploy).
3. **Detective + responsive** — Cloud Custodian.
4. **Audit/attestation** — Audit Manager + CloudTrail Lake + Config.

## 9. Pitfalls

- **Custodian without dry-run** — accidental terminations.
- **cfn-guard rules too loose** — gives false confidence.
- **Audit Manager unmapped controls** — incomplete evidence trail.
- **SCPs/RCPs only**, no runtime detection → drift accumulates.

## 10. Capital One lens

Capital One's governance stack (inferred from public talks and OSS):

```
SCPs/RCPs (preventive)
    ↓
cdk-nag (synth)
    ↓
cfn-guard / CloudFormation Hooks (deploy-time)
    ↓
Cloud Custodian (runtime detection + auto-remediation)
    ↓
Audit Manager + CloudTrail Lake (attestation)
```

This four-layer model is the regulated-finance posture.

## 11. Sanity check

1. SCPs vs RCPs — what gap does RCP close?
2. What is Cloud Custodian's project status (license, foundation)?
3. cfn-guard vs cdk-nag — when does each fire?
4. Audit Manager — what does it produce?
5. Why is dry-run discipline critical with Custodian?

## 12. Cross-references

- **Module 1** — Organizations, Control Tower, LZA
- **Module 2** — IAM (the permission layer)
- **Module 50** — security primitives (the data sources Custodian reads)
- **Module 52** — compliance frameworks (what Audit Manager attests against)

## Primary sources

- [`cloud_custodian_readme.md`](../../research_inputs/04_aws_for_ai_ml/downloads/oss_tooling/cloud_custodian_readme.md)
- [`cloud_custodian_aws_provider.html`](../../research_inputs/04_aws_for_ai_ml/downloads/oss_tooling/cloud_custodian_aws_provider.html)
- [`AWS_Audit_Manager_User_Guide.pdf`](../../research_inputs/04_aws_for_ai_ml/downloads/aws_whitepapers/AWS_Audit_Manager_User_Guide.pdf)
- Research report: [`12_security_compliance.md`](../../research_inputs/04_aws_for_ai_ml/12_security_compliance.md)
