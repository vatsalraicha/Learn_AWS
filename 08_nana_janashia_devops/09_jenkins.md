# 09 — Jenkins — Build Automation & CI/CD

> Cross-link: [Topic 07 Modules 49–51](../07_git_github_devops/49_jenkins_architecture_jenkinsfile.md) cover Jenkins architecture, Jenkinsfile, multibranch + shared libraries, and credentials/GH→Jenkins→AWS pipelines.
>
> This module is the **Nana-flavored sweep**: every Jenkins concept she covers, in one tight pass.

## 1. Why Jenkins still matters in 2026

Despite Actions and GitLab CI eating share, Jenkins still runs ~50% of CI/CD globally and ~80% of regulated finance. Capital One: ~500k pipelines on CloudBees CI Enterprise. The reasons it survives:

- **Plugin ecosystem** — 1800+ plugins, every conceivable integration.
- **Self-hostable, air-gappable** — works in regulated/disconnected environments.
- **Battle-tested at scale** — runs 50k+ builds/day in big shops.
- **Familiar to senior engineers** — entrenched skill base.

Drawbacks: groovy DSL footguns, single-master scaling pain (mitigated by CloudBees CI multi-master), plugin churn + security CVEs.

## 2. Installing Jenkins

The modern way: **on Kubernetes** via the Helm chart or the JCasC + JenkinsFile approach.

The classroom way (Nana's): on Ubuntu via apt:
```bash
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | \
  sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/" | \
  sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install -y openjdk-17-jre jenkins
sudo systemctl enable --now jenkins
# Initial password:
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Java 17 is the minimum since LTS 2.452.x (April 2024). Java 21 supported.

## 3. Jenkins core concepts

- **Controller (formerly "master")** — runs the UI, schedules builds, stores config + history
- **Agent (formerly "slave")** — executes builds; can be ephemeral (Docker, K8s pods, EC2)
- **Job / Pipeline** — a unit of work
- **Build / Run** — execution of a job
- **Workspace** — directory on the agent where source is checked out + builds happen
- **Executor** — slot for running a build on an agent

## 4. Job types

| Type | When to use |
|---|---|
| **Freestyle** | Legacy; UI-driven; minimal scripting; avoid for new projects |
| **Pipeline (Jenkinsfile)** | The modern way; code-as-config in repo |
| **Multibranch Pipeline** | Auto-detects branches in a repo, runs Jenkinsfile per branch — modern default |
| **Folder / Organization Folder** | Scans whole GitHub org / GitLab group |
| **Maven / Gradle Project** | Specialized for those build tools; less common in 2026 |

Modern Jenkins = **Multibranch Pipeline** + **Jenkinsfile** in repo + **Shared Library** for common logic.

## 5. Jenkinsfile syntax — Declarative pipeline

```groovy
pipeline {
  agent { docker { image 'python:3.13-slim' } }
  options {
    timeout(time: 30, unit: 'MINUTES')
    timestamps()
    ansiColor('xterm')
  }
  environment {
    APP_NAME = 'myapp'
    REGISTRY = 'nexus.example.com:5000'
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Install') {
      steps { sh 'pip install -r requirements.txt' }
    }
    stage('Test') {
      steps { sh 'pytest --junitxml=test-results.xml' }
      post { always { junit 'test-results.xml' } }
    }
    stage('Build Image') {
      steps {
        sh "docker build -t ${REGISTRY}/${APP_NAME}:${env.BUILD_NUMBER} ."
      }
    }
    stage('Push Image') {
      when { branch 'main' }
      steps {
        withCredentials([usernamePassword(credentialsId: 'nexus-creds',
            usernameVariable: 'U', passwordVariable: 'P')]) {
          sh '''
            echo "$P" | docker login $REGISTRY -u "$U" --password-stdin
            docker push $REGISTRY/$APP_NAME:$BUILD_NUMBER
          '''
        }
      }
    }
    stage('Deploy') {
      when { branch 'main' }
      steps {
        input message: 'Deploy to prod?', ok: 'Go'
        sh "./deploy.sh ${BUILD_NUMBER}"
      }
    }
  }
  post {
    failure { slackSend(channel: '#deploys', color: 'danger', message: "FAILED ${env.JOB_NAME} #${env.BUILD_NUMBER}") }
    success { slackSend(channel: '#deploys', color: 'good', message: "OK ${env.JOB_NAME} #${env.BUILD_NUMBER}") }
  }
}
```

The two flavors:
- **Declarative** (`pipeline { ... }`) — opinionated, validated, easier — use this.
- **Scripted** (`node { ... }`) — Groovy script, more flexible, more rope. Only when declarative can't express what you need.

## 6. Multibranch pipelines

Configure a multibranch job pointing at a Git repo. Jenkins scans the repo, finds each branch with a `Jenkinsfile`, creates a sub-job per branch. PRs (in GitHub multibranch source plugin) also become sub-jobs. Each branch's Jenkinsfile runs that branch's pipeline.

This is how you get "every branch, every PR builds automatically" without manual job-per-branch config.

## 7. Credentials in Jenkins

Use the **Credentials Store** (built-in or HashiCorp Vault integration via plugin). Refer to credentials by **ID** in Jenkinsfile:

```groovy
withCredentials([
  string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY'),
  string(credentialsId: 'aws-access-key-id', variable: 'AWS_ACCESS_KEY_ID')
]) {
  sh 'aws s3 ls'
}
```

For AWS specifically, prefer **OIDC + IAM Role** (Jenkins agents assume role) over long-lived access keys. See [Topic 07 Module 51](../07_git_github_devops/51_jenkins_credentials_ghaws.md).

## 8. Jenkins Shared Library — DRY across pipelines

A Git repo with `vars/` (global pipeline steps) and `src/` (Groovy classes), referenced from any Jenkinsfile:

```groovy
@Library('my-org-library@v1.4') _

pipeline {
  agent any
  stages {
    stage('Build') { steps { myBuildStep() } }
    stage('Deploy') { steps { myDeployStep(env: 'prod') } }
  }
}
```

`myBuildStep()` is defined in the shared library's `vars/myBuildStep.groovy`. This is how big shops keep 1000 pipelines DRY.

## 9. Webhooks (auto-trigger pipelines)

Configure on the Git server: GitHub → Settings → Webhooks → URL = `https://jenkins.example.com/github-webhook/`. Push to repo → webhook fires → Jenkins multibranch detects new SHA → builds.

For self-hosted GitLab → Jenkins: `https://jenkins.example.com/project/<job-name>` with GitLab token.

## 10. Dynamic versioning in Jenkins

The pattern:
```groovy
def version = sh(returnStdout: true, script: 'git describe --tags --abbrev=7').trim()
echo "Building version ${version}"
```

Or auto-increment via Maven Release Plugin / npm version / `git tag` + push from pipeline. Tag-driven release pipelines are the modern norm; "build number" alone is fragile.

## 11. Docker-in-Jenkins (the agents-on-K8s pattern)

Jenkins on K8s with the **kubernetes plugin**: each build spins up a pod with whatever containers you need:

```groovy
pipeline {
  agent {
    kubernetes {
      yaml '''
        apiVersion: v1
        kind: Pod
        spec:
          containers:
          - name: python
            image: python:3.13-slim
            command: ["sleep","infinity"]
          - name: docker
            image: docker:27-cli
            command: ["sleep","infinity"]
            volumeMounts:
            - name: docker-sock
              mountPath: /var/run/docker.sock
          volumes:
          - name: docker-sock
            hostPath:
              path: /var/run/docker.sock
      '''
    }
  }
  stages { stage('Build') { steps { container('docker') { sh 'docker build ...' } } } }
}
```

This is the **autoscaling Jenkins** answer — no idle agents.

## 12. Jenkins anti-patterns

1. **Storing secrets in Jenkinsfile** — use Credentials Store
2. **Long-lived agents** — prefer ephemeral (K8s pods, EC2 ASG)
3. **`master` branch builds via cron only** — webhook + multibranch
4. **No shared library** — copy-paste pipelines breed bugs
5. **Plugin sprawl** — every plugin is attack surface; audit + prune
6. **Direct kubectl from pipeline** — prefer GitOps (push manifests, ArgoCD pulls)

## 13. Quick self-check

1. What's the difference between declarative and scripted pipeline syntax?
2. What does a multibranch pipeline give you over a regular Pipeline job?
3. Where do credentials live in Jenkins and how do you reference them?
4. What is a Shared Library and what problem does it solve?
5. Why is ephemeral K8s-pod agents preferred over long-lived EC2 agents?

(Answers: declarative is opinionated YAML-ish DSL, scripted is full Groovy; auto-discover branches and PRs, run Jenkinsfile per; in Credentials Store, by `credentialsId`; reusable steps + classes across many pipelines; cost + reproducibility + clean state every build.)
