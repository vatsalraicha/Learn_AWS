# 49 — ⭐ Jenkins architecture + Jenkinsfile (declarative vs scripted)

> *"Capital One runs ~500,000 Jenkins pipelines. Knowing Jenkins is not optional for the Sr Lead role, even if GitHub Actions is the future-tense answer."*

## Why this module exists

Capital One has been on Jenkins since their cloud migration. While GitHub Actions is encroaching for new workloads, Jenkins remains the backbone for many existing CI/CD pipelines — especially anything that needs deep VPC access, GPU-heavy training, or complex multi-stage promotion. This module covers Jenkins' architecture + the Jenkinsfile (the unit of pipeline code).

---

## 1. Jenkins architecture

```
                          ┌───────────────────────────┐
                          │      Jenkins Controller   │
                          │  (master / UI / scheduler)│
                          └───────────────┬───────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
       ┌──────▼─────┐             ┌───────▼─────┐             ┌───────▼─────┐
       │  Agent #1  │             │  Agent #2   │             │  Agent #N   │
       │ (Linux x64)│             │ (Win)       │             │ (Linux GPU) │
       └────────────┘             └─────────────┘             └─────────────┘
```

Components:
- **Controller** (formerly "master") — schedules jobs, hosts UI, persists configuration. Should NOT run builds (security + reliability).
- **Agents** (formerly "slaves") — execute builds. Connected via SSH, JNLP, or Kubernetes plugin (dynamically provisioned).
- **Plugins** — Jenkins's extensibility. 1,800+. Half your day-2 ops is plugin management.

**Capital One's scale**: ~7,000 engineers, >500k pipelines, ~50k actions/day. Agents are likely Kubernetes-provisioned ephemeral pods (same pattern as ARC for Actions).

---

## 2. The Jenkinsfile

A Jenkinsfile is the pipeline definition, lives in the repo at root.

```groovy
// Jenkinsfile (declarative)
@Library('capital-one-pipeline@stable') _

pipeline {
    agent { label 'docker-build' }

    options {
        timeout(time: 30, unit: 'MINUTES')
        ansiColor('xterm')
        buildDiscarder(logRotator(numToKeepStr: '50'))
    }

    environment {
        AWS_REGION = 'us-east-1'
        PYTHON_VERSION = '3.11'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh 'python -m venv .venv && .venv/bin/pip install -e ".[dev]"'
            }
        }

        stage('Lint + Test') {
            parallel {
                stage('Lint') {
                    steps {
                        sh '.venv/bin/ruff check src tests'
                    }
                }
                stage('Test') {
                    steps {
                        sh '.venv/bin/pytest --junitxml=junit.xml'
                    }
                    post {
                        always {
                            junit 'junit.xml'
                        }
                    }
                }
            }
        }

        stage('Build + Push') {
            when { branch 'main' }
            steps {
                script {
                    cls.buildAndPushDocker(
                        imageName: 'fraud-detector',
                        tag: "${env.BUILD_NUMBER}-${env.GIT_COMMIT}"
                    )
                }
            }
        }

        stage('Deploy Staging') {
            when { branch 'main' }
            steps {
                script {
                    cls.deployToEks(
                        cluster: 'staging',
                        service: 'fraud-detector',
                        image: "fraud-detector:${env.BUILD_NUMBER}-${env.GIT_COMMIT}"
                    )
                }
            }
        }

        stage('Deploy Prod') {
            when { branch 'main' }
            input {
                message "Deploy to prod?"
                ok "Yes"
                submitter "capitalone/ml-ops-leads"
            }
            steps {
                script {
                    cls.deployToEks(cluster: 'prod', ...)
                }
            }
        }
    }

    post {
        success {
            slackSend(color: 'good', message: "Build #${env.BUILD_NUMBER} succeeded")
        }
        failure {
            slackSend(color: 'danger', message: "Build #${env.BUILD_NUMBER} failed")
        }
    }
}
```

Capital One service teams write ~30 lines like this — most logic is in the `@Library('capital-one-pipeline')` shared library (see [module 50](50_jenkins_multibranch_shared_libs.md)).

---

## 3. Declarative vs scripted

Two Jenkinsfile syntaxes:

| | Declarative | Scripted |
|---|---|---|
| Top-level | `pipeline { ... }` block | `node { ... }` Groovy script |
| Structure | Enforced (stages, steps, etc.) | Free-form Groovy |
| Readability | High — structured | Lower — Groovy heavy |
| Power | Limited but covers 90% | Full programming language |
| Validation | Lintable via `jenkins-cli validate-jenkinsfile` | Runtime errors only |
| When | **Default for new code** | Edge cases requiring complex logic |

**Always use declarative** unless you have a specific reason. Scripted creeps in via legacy + via people who learned Jenkins pre-2017.

You can mix: declarative wrapping a `script { ... }` block for occasional Groovy.

---

## 4. Stages, steps, post

Anatomy:

```groovy
pipeline {
    stages {
        stage('Stage name') {           // appears in Blue Ocean / Stage View
            agent { ... }                // optional per-stage agent
            when { ... }                 // conditional execution
            environment { ... }          // stage-level env
            steps {
                sh '...'                 // shell command
                bat '...'                // Windows command
                powershell '...'
                checkout scm
                docker.image('python:3.11').inside { sh '...' }
                input message: "Continue?"
                timeout(time: 5, unit: 'MINUTES') { ... }
                retry(3) { ... }
                catchError(buildResult: 'UNSTABLE') { ... }
                script {                  // escape hatch to scripted
                    if (params.SKIP_TEST) {
                        echo "Skipping"
                    }
                }
            }
            post {
                always { ... }
                success { ... }
                failure { ... }
                unstable { ... }
                cleanup { ... }
            }
        }
    }
    post { ... }                         // pipeline-level post (runs after all stages)
}
```

---

## 5. Parameters

```groovy
pipeline {
    agent any
    parameters {
        string(name: 'VERSION', defaultValue: '1.0.0', description: 'Version to deploy')
        choice(name: 'ENV', choices: ['dev', 'staging', 'prod'])
        booleanParam(name: 'DRY_RUN', defaultValue: true)
        text(name: 'NOTES', defaultValue: '')
    }
    stages {
        stage('Deploy') {
            steps {
                echo "Deploying ${params.VERSION} to ${params.ENV}, dry-run: ${params.DRY_RUN}"
            }
        }
    }
}
```

Build with params via UI or CLI: `jenkins-cli build my-job -p VERSION=1.2.3 -p ENV=staging`.

---

## 6. Agents — where stages run

```groovy
agent any                                // any available agent
agent none                                // no default; each stage declares its own
agent { label 'linux && python3.11' }    // labeled agents
agent { node { label 'gpu' } }           // explicit node selection
agent {
    docker {
        image 'python:3.11'
        args '-v /var/cache:/cache'
    }
}
agent {
    kubernetes {                          // K8s plugin spawns a pod
        yaml '''
        apiVersion: v1
        kind: Pod
        spec:
          containers:
          - name: python
            image: python:3.11
          - name: kubectl
            image: bitnami/kubectl:latest
            command: ['sleep', '99d']
        '''
    }
}
```

For Capital One: K8s-provisioned agents per build are the modern pattern (same shape as ARC).

```groovy
agent {
    kubernetes {
        defaultContainer 'python'
        yamlFile 'k8s-agent.yaml'
    }
}
```

Per-stage `agent` overrides pipeline-level. Useful for fan-out: build on one agent type, deploy on another.

---

## 7. Credentials

NEVER bake credentials into Jenkinsfile. Use the Credentials plugin:

```groovy
environment {
    AWS_CREDENTIALS = credentials('aws-prod-deployer')
    // Auto-populates AWS_CREDENTIALS_USR and AWS_CREDENTIALS_PSW
}

steps {
    withCredentials([
        usernamePassword(credentialsId: 'aws-prod', usernameVariable: 'AWS_KEY', passwordVariable: 'AWS_SECRET'),
        string(credentialsId: 'slack-webhook', variable: 'SLACK_WEBHOOK')
    ]) {
        sh 'aws s3 cp ./artifact.zip s3://...'
    }
}
```

Credentials are scoped: System (whole controller), Global (controller + all agents), per-Folder (only jobs in this folder). Use Folder-scoped for least privilege.

For AWS: Jenkins supports IRSA on K8s agents (the agent pod has its own IAM role via ServiceAccount) — same pattern as ARC. This is the OIDC-equivalent for Jenkins.

---

## 8. Triggers

```groovy
triggers {
    cron('0 6 * * 1-5')                    // weekdays 6am
    pollSCM('H/15 * * * *')                // poll SCM every ~15 min (DEPRECATED — use webhooks)
    githubPush()                           // GitHub push event (via GitHub plugin)
    upstream(upstreamProjects: 'other-job', threshold: hudson.model.Result.SUCCESS)
}
```

Modern pattern: **GitHub webhooks** (via GitHub Branch Source plugin in multibranch pipelines) → no polling needed. Push to GitHub → webhook to Jenkins → job triggered immediately.

---

## 9. The Blue Ocean UI

Blue Ocean is Jenkins's modern UI for pipeline visualization. Shows stage-by-stage progress with parallel branches rendered as a tree. Heavily used; most engineers spend more time in Blue Ocean than the classic UI.

Classic UI for: admin / config / plugin management.
Blue Ocean for: viewing builds, debugging failures, manual approvals.

---

## 10. Cross-references

- Multibranch pipelines + shared libraries → [module 50](50_jenkins_multibranch_shared_libs.md).
- Credentials + GitHub→Jenkins→AWS handoffs → [module 51](51_jenkins_credentials_ghaws.md).
- Jenkins on Kubernetes (Capital One pattern) → analogous to ARC, [module 28](28_actions_self_hosted_arc_gpu.md).
- Capital One's "singular pipeline" → [module 56](56_capital_one_devops_deep.md).
