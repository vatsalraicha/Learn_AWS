# 37 — Compliance as Code — AWS Config + CIS Benchmarks

## Why this module exists

Compliance frameworks (SOC 2, PCI-DSS, HIPAA, SR 11-7) require **continuous evidence** that controls are in place. Manual screenshots once a year don't scale; you'd spend half your engineering time on audit. **Compliance as code** automates evidence collection and remediation.

## 1. The compliance landscape (regulated finance)

| Framework | Scope | Capital One? |
|---|---|---|
| **SOC 2 Type II** | SaaS controls + 12-month period | Yes |
| **PCI-DSS v4** | Card data | Yes (issuer) |
| **HIPAA** | US health PHI | No (different industry; Optum yes) |
| **GLBA** | US financial services | Yes |
| **SR 11-7** | US bank model risk | Yes |
| **FFIEC** | Federal financial inst. | Yes |
| **ISO 27001** | Global infosec | Yes |
| **NIST CSF** | US infosec voluntary | Yes (mapped) |
| **FedRAMP** | US federal cloud | No (not federal-direct) |
| **GDPR / CCPA** | Privacy | Yes (where data scope) |

## 2. CIS Benchmarks — the operational baseline

CIS (Center for Internet Security) publishes hardening checklists per platform:
- **CIS AWS Foundations Benchmark** v3.0 (Jan 2024) — ~50 checks
- **CIS Kubernetes Benchmark** — per K8s minor version
- **CIS Docker Benchmark**
- **CIS Linux Benchmark** (per distro)
- **CIS Azure / GCP Benchmarks**

These map into SOC 2 / PCI / HIPAA controls. Pass CIS = pass ~80% of compliance controls.

Tools to scan against CIS:
- **AWS Security Hub** — has the CIS standard built in
- **Prowler** — OSS multi-cloud scanner
- **ScoutSuite** — OSS multi-cloud
- **CloudSploit / Aqua Trivy** — multi-cloud
- **kube-bench** — K8s CIS
- **CIS-CAT Pro** — CIS's own tool (paid)
- **OpenSCAP** — Linux SCAP scanner

## 3. AWS Config — resource configuration history + rules

AWS Config:
1. **Records** the configuration of every supported resource (~250+ types)
2. **Stores history** in S3
3. **Evaluates rules** continuously (or on-change)
4. **Triggers remediation** via SSM Automation

```hcl
resource "aws_config_configuration_recorder" "main" {
  name     = "default"
  role_arn = aws_iam_role.config.arn
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "main" {
  name           = "default"
  s3_bucket_name = aws_s3_bucket.config.id
  depends_on     = [aws_config_configuration_recorder.main]
}
```

## 4. Config Rules

```hcl
# Managed rule — AWS provides 200+ pre-built
resource "aws_config_config_rule" "s3_public_read" {
  name = "s3-bucket-public-read-prohibited"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }
}

resource "aws_config_config_rule" "iam_password_policy" {
  name = "iam-password-policy"
  source {
    owner             = "AWS"
    source_identifier = "IAM_PASSWORD_POLICY"
  }
  input_parameters = jsonencode({
    MinimumPasswordLength      = "14"
    RequireSymbols             = "true"
    RequireNumbers             = "true"
    RequireUppercaseCharacters = "true"
    RequireLowercaseCharacters = "true"
    PasswordReusePrevention    = "24"
    MaxPasswordAge             = "90"
  })
}

# Custom Lambda-backed rule
resource "aws_config_config_rule" "custom" {
  name = "my-custom-rule"
  source {
    owner             = "CUSTOM_LAMBDA"
    source_identifier = aws_lambda_function.config_rule.arn
  }
}
```

## 5. Conformance Packs — bundled rules

A conformance pack = many rules + remediation actions, packaged together:

```hcl
resource "aws_config_conformance_pack" "cis_v3" {
  name          = "cis-aws-foundations-v3"
  template_body = file("conformance-packs/cis-aws-foundations-v3.yaml")
}
```

AWS publishes ~30 sample packs (CIS, PCI-DSS, HIPAA, NIST 800-53, FedRAMP, etc.). Apply one, get a hundred rules.

## 6. Auto-Remediation

```hcl
resource "aws_config_remediation_configuration" "sg_open" {
  config_rule_name           = "restricted-ssh"
  target_type                = "SSM_DOCUMENT"
  target_id                  = "AWS-DisablePublicAccessForSecurityGroup"
  automatic                  = true
  maximum_automatic_attempts = 5

  parameter {
    name           = "GroupId"
    resource_value = "RESOURCE_ID"
  }

  parameter {
    name         = "AutomationAssumeRole"
    static_value = aws_iam_role.config_remediation.arn
  }
}
```

When a security group with 0.0.0.0/0 SSH is detected → Config Rule fires NON_COMPLIANT → SSM Automation runs → removes the rule.

Capital One: similar pattern via **Cloud Custodian** which combines policy + remediation in Python.

## 7. Auto-Remediation example for CloudTrail logging

Common: detect when someone disables CloudTrail logging:

```yaml
# CIS rule: ensure CloudTrail logging is enabled
- rule: cloudtrail-enabled
  source: AWS
  identifier: CLOUD_TRAIL_ENABLED
- remediation:
    SSMDocument: AWS-EnableCloudTrail
    automatic: true
```

If anyone disables CloudTrail → Config detects → SSM re-enables. Within minutes, attacker loses their attempt to hide.

## 8. Cloud Custodian — Capital One's tool

Cloud Custodian (YAML-based policy framework, Python under the hood, CNCF Sandbox 2018):

```yaml
policies:
  - name: encrypt-unencrypted-volumes
    resource: ebs
    filters:
      - Encrypted: false
    actions:
      - snapshot
      - delete

  - name: detect-public-s3
    resource: s3
    filters:
      - type: global-grants
    actions:
      - type: remove-statements
        statement_ids: matched
      - type: notify
        to: [security@example.com]
        transport:
          type: sns
          topic: arn:aws:sns:us-east-1:1234:security-alerts

  - name: stop-unused-rds
    resource: rds
    filters:
      - type: metrics
        name: DatabaseConnections
        days: 7
        statistics: Sum
        value: 0
    actions:
      - stop
```

Custodian's strengths:
- **Single YAML covers detection + remediation** (Config separates)
- **Filters compose** declaratively (and/or/not)
- **Pluggable actions** (notify, tag, delete, modify, snapshot, etc.)
- **Multi-cloud** (AWS deepest, Azure + GCP supported)

## 9. Compliance dashboards

| Tool | What |
|---|---|
| **AWS Security Hub** | Aggregates Config + GuardDuty + Inspector + Macie; CIS/PCI/AWS-Foundational standards built in |
| **AWS Audit Manager** | Auto-collects evidence mapped to framework controls; PDF export for auditors |
| **Wiz / Lacework / Orca / Sysdig** | Commercial CSPMs; multi-cloud; better UX than Hub |
| **Drata / Vanta / Secureframe** | Compliance-program platforms — gather evidence across SaaS too |
| **Splunk / Datadog Compliance** | If you already have the SIEM |

## 10. Compliance Rules for AWS EKS

EKS-specific compliance:
- **EKS audit logs enabled** (CW)
- **Public endpoint disabled OR restricted CIDR**
- **Latest K8s minor version**
- **Secrets envelope-encrypted with KMS**
- **Node group security groups restricted**
- **IRSA / Pod Identity used (not long-lived keys)**

Plus K8s-level via kube-bench / Polaris / Trivy K8s.

## 11. The compliance-as-code playbook

1. **Map your obligations** — which frameworks apply, which controls
2. **Pick benchmarks** that satisfy them (CIS AWS, CIS K8s, NIST 800-53)
3. **Implement scanners** that evaluate continuously (Config, Security Hub, Custodian)
4. **Set up auto-remediation** for low-risk findings
5. **Workflow for high-risk findings** — DefectDojo / Jira / Slack
6. **Dashboards + reports** for management + auditors
7. **Drift detection** + alarms (CloudTrail metric filters)
8. **Annual penetration test** + control review

## 12. Quick self-check

1. What does AWS Config do that CloudTrail doesn't?
2. What's a Conformance Pack?
3. What's Cloud Custodian and what Capital One contributed it?
4. Why is auto-remediation valuable beyond just detection?
5. How does CIS map to SOC 2 / PCI compliance?

(Answers: records resource configuration history + evaluates compliance rules — CloudTrail is API-call audit, Config is resource-state audit; bundle of Config Rules + remediations packaged for a framework (CIS, PCI, HIPAA, etc.); declarative Python policy framework for AWS resources — detection + filters + actions in one YAML — Capital One built it, CNCF Sandbox since 2018; closes the window between detection and human response — many findings should be auto-fixed in seconds, not days; CIS Benchmarks define operational hardening that maps to ~80% of SOC 2 / PCI controls — pass CIS, pass most of those.)
