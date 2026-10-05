# 51 — ⭐🏦 Jenkins credentials + GitHub→Jenkins→AWS + the Capital One pattern

> *"The end-to-end CI/CD picture: a GitHub PR triggers a Jenkins multibranch sub-job that runs through the central shared library that deploys to AWS via IRSA. Get this wired right and you've implemented Capital One's published architecture."*

## Why this module exists

This module ties the previous two together with the credentials story. The Capital One CI/CD reality is **GitHub for source + Jenkins for orchestration + AWS for runtime**. The handoffs between them are the credential-sensitive boundaries.

---

## 1. Jenkins Credentials plugin

Credentials in Jenkins are typed objects:

| Type | Use case |
|---|---|
| **Username/password** | Basic-auth APIs, SQL DBs |
| **SSH key** | Git over SSH (replaced by GitHub App in modern setups) |
| **Secret text** | API tokens, webhooks |
| **Secret file** | Cert bundles, kubeconfigs |
| **AWS credentials** | (Plugin-provided) AWS access key + secret |
| **Certificate** | mTLS client certs |
| **GitHub App** | Org-level GitHub App credentials |

Scopes:
- **System** — controller-only (used for Jenkins itself, e.g., LDAP bind)
- **Global** — controller + all agents (default for most credentials)
- **Per-Folder** — only jobs in this folder can read

Best practice: Folder-scoped per project. A "Fraud" folder has its own credentials; a "Recommendations" folder has different ones. Prevents lateral movement.

---

## 2. Using credentials in Jenkinsfile

Best: `withCredentials` block, automatic masking, scoped to the block:

```groovy
withCredentials([
    string(credentialsId: 'snowflake-key', variable: 'SF_KEY'),
    file(credentialsId: 'tls-cert', variable: 'CERT_PATH'),
    usernamePassword(credentialsId: 'jfrog', usernameVariable: 'JF_USER', passwordVariable: 'JF_PWD')
]) {
    sh '''
        export SF_KEY  # auto-masked in build log
        snowsql -c connection -q "SELECT 1"
    '''
}
```

Or via `environment` for credentials needed across all stages:

```groovy
environment {
    SLACK_WEBHOOK = credentials('slack-alerts-webhook')
}
```

`credentials('id')` returns the stringified credential. For username/password types, you get `SLACK_WEBHOOK_USR` and `SLACK_WEBHOOK_PSW` separately.

**NEVER `sh "echo $CREDS"`** — Jenkins masks credentials in logs, but only if you reference them as env vars, not Groovy strings.

---

## 3. The OIDC/IRSA path for Jenkins → AWS

Jenkins agents on Kubernetes (EKS) get IAM identity via **IRSA** (IAM Roles for Service Accounts) — same primitive as ARC.

Pattern:
1. Jenkins agent pod uses a Kubernetes ServiceAccount (e.g., `jenkins-ml-agent`).
2. The ServiceAccount is annotated with an IAM role ARN via `eks.amazonaws.com/role-arn`.
3. AWS SDK in the agent pod auto-discovers the role and assumes it via STS.
4. No long-lived AWS credentials in Jenkins credentials store.

```yaml
# K8s ServiceAccount with IRSA annotation
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jenkins-ml-agent
  namespace: jenkins
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/jenkins-ml-deployer
```

Jenkinsfile:

```groovy
agent {
    kubernetes {
        defaultContainer 'aws-cli'
        yaml '''
        apiVersion: v1
        kind: Pod
        spec:
          serviceAccountName: jenkins-ml-agent
          containers:
          - name: aws-cli
            image: amazon/aws-cli:latest
            command: ['sleep', '99d']
        '''
    }
}

stages {
    stage('Deploy') {
        steps {
            sh 'aws sts get-caller-identity'  // returns the assumed role identity
            sh 'aws s3 ls'
        }
    }
}
```

No AWS credentials in Jenkins. The pod's identity is the deploy role. **This is the modern Jenkins-on-EKS pattern, equivalent in spirit to GitHub Actions OIDC.**

---

## 4. The GitHub → Jenkins → AWS handoff

End-to-end flow for a deploy:

```
1. Dev opens PR on GitHub
   → GitHub webhook → Jenkins multibranch sub-job created/triggered

2. Jenkins agent spawned on EKS (per the Jenkinsfile's K8s agent spec)
   → Agent pod uses jenkins-ci-agent ServiceAccount (IRSA → CI IAM role)
   → CI role: read-only AWS perms (S3 read for tests, ECR pull for base images)

3. Build stage runs
   → Builds Docker image
   → Pushes to ECR (CI role has ecr:Push for specific repo)

4. PR review + approval (CODEOWNERS routed)
   → PR merged to main

5. Jenkins main-branch sub-job triggers
   → New agent pod with jenkins-deploy-agent ServiceAccount (IRSA → deploy IAM role)
   → Deploy role: scoped per-environment (staging vs prod)

6. Shared library deploys
   → cls.deployToEks(env: 'staging') → updates K8s manifests
   → Smoke test
   → Manual approval step (input { submitter 'capitalone/ml-ops-leads' })

7. Approval received → deploy to prod
   → Same library, prod env, separate role
   → Audit log captures: triggered by Jenkins, approved by alice@capitalone.com

8. Status posted back to GitHub PR + merge commit
   → GitHub PR shows "Jenkins / cool-ml-service / Deploy Prod ✓"

9. Slack notification to #ml-deploys
```

This is the standard shape. The credentials story:
- GitHub→Jenkins: GitHub App credentials in Jenkins (org-level App, not PATs)
- Jenkins→AWS: IRSA on agent pods
- Jenkins→Slack: stored as secret text in Jenkins credentials
- Jenkins→Snowflake/etc.: same — secret text scoped per folder

No long-lived AWS keys. No PATs. Just GitHub Apps + IRSA.

---

## 5. The audit trail across systems

For an SR 11-7 audit: "show me the chain for this prod deploy."

| Where to look | What you'll find |
|---|---|
| GitHub | PR opened, CODEOWNERS-approved, merged to main, status check from Jenkins green |
| GitHub audit log | PR merge by alice; signed commits verified |
| Jenkins build log | Build #1234, triggered by GitHub webhook on commit X |
| Jenkins build params | branch=main, image=fraud-detector:X |
| Jenkins "Deploy Prod" stage | Approved by bob@capitalone.com via input step |
| AWS CloudTrail (prod account) | `UpdateEndpoint` by `arn:aws:sts::PROD_ACCT:assumed-role/jenkins-prod-deployer/jenkins-1234` |
| SageMaker Model Registry | Model version Y deployed to endpoint Z at time T; approver = bob |
| Slack archive | Notification posted to #ml-deploys |
| Internal SIEM | All of the above retained per policy |

You can trace from any starting point to any other. Auditor satisfied.

---

## 6. GitHub Apps for Jenkins integration

The modern Jenkins-GitHub integration uses **GitHub App** credentials, not PATs:

1. Create a GitHub App at the org level: capitalone-jenkins-bot.
2. Permissions: `Contents: Read`, `Pull requests: Write`, `Statuses: Write`, `Checks: Write`, `Metadata: Read`.
3. Install on the org.
4. Generate private key; store in Jenkins credentials as "GitHub App credentials" type.
5. Configure GitHub Branch Source plugin to use this App credential.

Benefits over PATs:
- No personal account at risk
- Higher rate limits (5000/hr per installation, scales with repo count)
- Permission scoping per repo (App can be installed only on specific repos)
- Audit trail: actions attributed to the App, not a person

---

## 7. The Capital One pattern (synthesized)

From cross-referencing the public sources:

**GitHub layer**:
- GitHub Enterprise Cloud, SAML SSO + SCIM
- Rulesets enforcing signed commits + CODEOWNERS-required reviews + status checks
- GHAS for secret scanning + CodeQL
- Webhooks from every repo → Jenkins via GitHub App

**Jenkins layer**:
- Jenkins on EKS (K8s-provisioned agents)
- Central `capital-one-pipeline` shared library (versioned, InnerSource-contributed)
- One multibranch pipeline per service repo
- Agent pods use IRSA for AWS identity
- ServiceNow + Slack integrations baked into shared library

**AWS layer**:
- Multi-account (per-LOB, per-env)
- ECR for images; SageMaker for models; EKS+KServe for serving; Lambda for serverless paths
- Cloud Custodian enforcing policy continuously
- CloudTrail per-account; aggregated in central security account

**Cross-layer**:
- Audit log streaming: GitHub → Splunk; Jenkins logs → Splunk; CloudTrail → Splunk
- SR 11-7 evidence: GitHub PR + Jenkins approval + SageMaker registry + CloudTrail → one queryable trail per deploy

---

## 8. Migration: Jenkins → GitHub Actions (the future-tense angle)

Capital One isn't abandoning Jenkins overnight. But for new services / greenfield work, GitHub Actions is increasingly viable:

When Actions wins:
- Greenfield repos with no legacy Jenkinsfile
- Workflows that don't need deep VPC access (or where ARC-on-EKS provides it)
- Teams already heavily on GitHub for source

When Jenkins still wins:
- Existing 500k-pipeline reality (migration cost > value)
- Workflows depending on complex Jenkins plugins
- Specific shared-library functionality not yet replicated in reusable workflows

Hybrid pattern: new services try Actions; legacy stays on Jenkins; the platform team maintains both shared library + reusable workflows so feature parity stays close.

If you're asked "would you move everything off Jenkins?" — the right answer is "where it makes sense; not as a religious thing. Migration is expensive; existing pipelines work; new work goes on Actions. The discipline is the same in both."

---

## 9. The Sr Lead's view

You will operate in a Jenkins + Actions hybrid for the foreseeable future at Capital One. Be fluent in both:
- Jenkinsfile syntax and `@Library` usage
- Actions YAML and reusable workflows
- Credentials handling in both (Jenkins folder-scoped + IRSA; Actions environment-scoped + OIDC)
- Audit story across both
- Migration considerations

Interviewers will ask "have you used Jenkins?" — the right answer mentions Jenkinsfile, declarative pipelines, shared libraries, multibranch, and IRSA. Not just "I once ran a Jenkins job."

---

## 10. Cross-references

- Jenkins architecture + Jenkinsfile → [module 49](49_jenkins_architecture_jenkinsfile.md).
- Multibranch + shared libraries → [module 50](50_jenkins_multibranch_shared_libs.md).
- OIDC + AWS for Actions (the parallel) → [module 29](29_actions_oidc_aws.md).
- ARC on K8s (the Actions parallel to Jenkins on K8s) → [module 28](28_actions_self_hosted_arc_gpu.md).
- Capital One DevOps deep dive → [module 56](56_capital_one_devops_deep.md).
- SR 11-7 audit-trail expectations → [module 37](37_compliance_sr117_audit.md).
