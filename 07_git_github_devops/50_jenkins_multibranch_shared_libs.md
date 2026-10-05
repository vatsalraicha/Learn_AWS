# 50 — ⭐ Jenkins multibranch + GitHub webhooks + shared libraries

> *"The Jenkins shared library is the unit of reuse. At Capital One, it's the InnerSource backbone of the 'singular pipeline' pattern."*

## Why this module exists

Two Jenkins concepts that scale to Capital One's 500k-pipeline reality: **multibranch pipelines** (one Jenkinsfile per branch, auto-discovered) and **shared libraries** (the Jenkins equivalent of GitHub Actions reusable workflows + composite actions). This module covers both with the InnerSource pattern.

---

## 1. Multibranch pipelines

A **multibranch pipeline** is a Jenkins job that auto-discovers branches AND PRs from a Git repo (or GitHub org), creating a sub-job per branch.

Setup:
- Jenkins → New Item → Multibranch Pipeline
- Branch source: GitHub
- Repo: `capitalone/cool-ml-service`
- Credentials for GitHub access
- Discover branches: All branches
- Discover pull requests from origin: All PRs (merge with current target)
- Build configuration: by Jenkinsfile

Result:
- Jenkins polls/webhooks the repo
- For each branch/PR found, creates a sub-job that runs `Jenkinsfile` from that branch/PR
- New branches auto-create jobs; deleted branches auto-clean
- Stage view shows all branches as columns

For Capital One: every service repo is a multibranch pipeline. Push to any branch → CI runs automatically. Open a PR → CI runs against the PR's merge commit.

---

## 2. GitHub webhook setup

For real-time triggers (vs polling):

1. **In Jenkins** (with GitHub plugin): per-job → "GitHub hook trigger for GITScm polling"
2. **In GitHub** (per repo): Settings → Webhooks → Add webhook
   - URL: `https://jenkins.capital-one.internal/github-webhook/`
   - Content type: `application/json`
   - Events: Just the push event (or "Send me everything")
   - Active: ✓

Webhook delivery: GitHub POSTs to Jenkins on push → Jenkins triggers the matching multibranch sub-job within seconds. No polling lag.

For org-level: register the webhook at the org level so every new repo gets the webhook automatically. Use a **GitHub App** instead of webhooks for permission scoping and rate-limit headroom.

---

## 3. Shared libraries — the structure

Shared library = a Git repo with a specific directory layout:

```
capital-one-pipeline/
├── vars/                                  ← global "steps" (called directly from Jenkinsfile)
│   ├── cls.groovy                          (e.g., cls.buildAndPushDocker(...))
│   ├── deployToEks.groovy
│   ├── runPyTests.groovy
│   └── notifySlack.groovy
├── src/                                    ← Groovy classes (called as classes)
│   └── com/
│       └── capitalone/
│           └── pipeline/
│               ├── DockerBuilder.groovy
│               ├── AwsAuth.groovy
│               └── Utils.groovy
├── resources/                              ← bundled files (templates, scripts)
│   ├── deploy-template.yaml
│   └── prometheus-config.yaml
└── README.md
```

Registration: Jenkins → Manage Jenkins → Configure System → Global Pipeline Libraries → add library named `capital-one-pipeline` with the Git repo URL.

Use in Jenkinsfile:

```groovy
@Library('capital-one-pipeline@stable') _

pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                cls.buildAndPushDocker(imageName: 'fraud-detector', tag: env.GIT_COMMIT)
            }
        }
        stage('Deploy') {
            steps {
                deployToEks(cluster: 'staging', service: 'fraud-detector')
            }
        }
    }
}
```

`@Library('name@ref')`: ref can be a branch, tag, or SHA. Use a tag for stability in prod jobs.

---

## 4. A `vars/` step example

`vars/deployToEks.groovy`:

```groovy
def call(Map args) {
    String cluster = args.cluster ?: error("cluster required")
    String service = args.service ?: error("service required")
    String namespace = args.namespace ?: 'default'

    withCredentials([
        string(credentialsId: "aws-${cluster}-deployer", variable: 'AWS_ROLE_ARN')
    ]) {
        sh """
            aws sts assume-role --role-arn \$AWS_ROLE_ARN --role-session-name jenkins-${env.BUILD_NUMBER} > creds.json
            export AWS_ACCESS_KEY_ID=\$(jq -r .Credentials.AccessKeyId creds.json)
            export AWS_SECRET_ACCESS_KEY=\$(jq -r .Credentials.SecretAccessKey creds.json)
            export AWS_SESSION_TOKEN=\$(jq -r .Credentials.SessionToken creds.json)

            aws eks update-kubeconfig --name ${cluster}

            kubectl rollout restart deployment/${service} -n ${namespace}
            kubectl rollout status deployment/${service} -n ${namespace} --timeout=10m
        """
    }
}
```

Now any consumer can `deployToEks(cluster: 'staging', service: 'foo')` in their Jenkinsfile. Logic lives in one place.

For Capital One: the centralized deploy step encodes security gates (assume-role with specific session name, tagging, etc.) that consumers don't have to think about.

---

## 5. A `src/` class example

`src/com/capitalone/pipeline/AwsAuth.groovy`:

```groovy
package com.capitalone.pipeline

class AwsAuth implements Serializable {
    def script
    String roleArn

    AwsAuth(script, String roleArn) {
        this.script = script
        this.roleArn = roleArn
    }

    def assumeAndExecute(Closure cl) {
        script.withCredentials([
            script.string(credentialsId: 'aws-base', variable: 'AWS_BASE_ARN')
        ]) {
            // ... assume role logic ...
            cl.call()
        }
    }
}
```

Used in Jenkinsfile:

```groovy
@Library('capital-one-pipeline') _
import com.capitalone.pipeline.AwsAuth

// ...
script {
    def auth = new AwsAuth(this, env.AWS_ROLE_ARN)
    auth.assumeAndExecute {
        sh 'aws s3 ls'
    }
}
```

The `Serializable` marker is required because Jenkins serializes pipeline state between stages.

`vars/*.groovy` cover most needs; `src/` is for richer class hierarchies.

---

## 6. The "Capital One singular pipeline" pattern

From their published [Building a Singular Software Delivery Pipeline](https://www.capitalone.com/tech/open-source/innersource-singular-software-delivery-pipeline/):

- One central shared library: `c1-pipeline-library`
- Versioned (semver tags)
- Encodes: lint, test, security scan, SBOM, build, push to Artifactory/ECR, deploy patterns (canary, blue/green, EKS, ECS, Lambda, SageMaker)
- Per-service Jenkinsfile is ~30 lines:

```groovy
@Library('c1-pipeline-library@v3') _

pipeline {
    agent { kubernetes { yamlFile 'k8s-agent.yaml' } }

    stages {
        stage('CI') {
            steps { c1.standardCI(language: 'python', extras: 'dev') }
        }
        stage('Build') {
            when { branch 'main' }
            steps { c1.buildAndPush(image: 'fraud-detector') }
        }
        stage('Deploy Staging') {
            when { branch 'main' }
            steps { c1.deploy(env: 'staging', service: 'fraud-detector') }
        }
        stage('Deploy Prod') {
            when { branch 'main' }
            steps { c1.promoteToProd(service: 'fraud-detector') }
        }
    }
}
```

The library handles: scanning, SBOM, signing, attestation, deploying, monitoring integration, ServiceNow CHG creation. Service team's Jenkinsfile just declares what kind of service they're shipping.

Updates to security gates: bump library version once → every consumer's next build picks up the change.

InnerSource: the library is in an internal repo; any team can contribute via PR; CODEOWNERS routes review to the platform team.

---

## 7. Multibranch + library = the full picture

```
GitHub repo (multibranch source)
   │
   ▼
Jenkins multibranch pipeline (one job per branch/PR)
   │
   ▼
Each sub-job reads its Jenkinsfile from the branch
   │
   ▼
Jenkinsfile @Library's the central library
   │
   ▼
Library invokes its own logic (potentially K8s pods, AWS calls, etc.)
   │
   ▼
Build/test/deploy completes
   │
   ▼
Status posted back to GitHub PR (via GitHub plugin)
```

Result: GitHub-native PR review experience with Jenkins as the orchestration backplane.

---

## 8. Library testing

You can't easily unit-test Jenkins shared libraries (Jenkins runs the Groovy script in a sandbox). Two patterns:

- **JenkinsPipelineUnit** — a Spock-based mock framework that runs Jenkinsfile + library code with mocked CPS environment. Good for `vars/` step testing.
- **Real Jenkins job** with a "self-test" Jenkinsfile that exercises every library step against fixtures.

For Capital One scale, the library has its own pipeline that runs JenkinsPipelineUnit tests on every PR. Library merges to `main` only when tests pass.

---

## 9. Library versioning

Tag library releases (`v1.0.0`, `v2.0.0`). Consumers pin:
- `@Library('lib@v3')` — major version (follows v3.x)
- `@Library('lib@v3.2.1')` — exact
- `@Library('lib@stable')` — moving "stable" tag (less common; consumers don't know what version they got)
- `@Library('lib@SHA')` — pin by commit (most robust for prod)

Breaking changes = major bump. Document in CHANGELOG. Use Conventional Commits + release-please for the library repo too.

---

## 10. Cross-references

- Jenkins architecture + Jenkinsfile syntax → [module 49](49_jenkins_architecture_jenkinsfile.md).
- Credentials + GitHub→Jenkins→AWS handoffs → [module 51](51_jenkins_credentials_ghaws.md).
- The GitHub Actions equivalent (reusable workflows) → [module 26](26_actions_reusable_workflows.md).
- InnerSource principles → [module 16](16_feature_flags_innersource.md).
- The Capital One DevOps deep dive → [module 56](56_capital_one_devops_deep.md).
