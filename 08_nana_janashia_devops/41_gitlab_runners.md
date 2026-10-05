# 41 — GitLab Architecture — Runners + Executors

## 1. The architecture

```
┌────────────────────────────┐
│   GitLab Server            │  (gitlab.com or self-hosted)
│   - SCM, MRs, Pipelines    │
│   - Job queue              │
│   - Artifacts + Registry   │
└────────────────────────────┘
           │
           │ long-poll for jobs
           ▼
┌────────────────────────────┐
│   GitLab Runner (process)  │  (registered to GitLab; runs as service)
│   - Token-authenticated    │
│   - Polls for jobs         │
│   - Dispatches to Executor │
└────────────────────────────┘
           │
           ▼
┌────────────────────────────┐
│       Executor              │  (where the actual job runs)
│   shell / docker / K8s /    │
│   ssh / custom              │
└────────────────────────────┘
```

**Runner** = process that picks up jobs.
**Executor** = where the job actually executes (shell, container, K8s pod).

## 2. Executors

| Executor | When | Job runs in |
|---|---|---|
| **Shell** | Simple; runner's host environment | Same machine as runner, no isolation |
| **Docker** | Most common | Docker container on runner host |
| **Docker-in-Docker (dind)** | Building images | Docker daemon inside a container |
| **Kubernetes** | Production at scale | Auto-spawned K8s pods per job |
| **Docker-Machine** | DEPRECATED — replaced by K8s + Fleet executors |
| **SSH** | Run on existing remote | SSHed to a managed box |
| **Instance / GitLab SaaS** | gitlab.com hosted | AWS/GCP/Azure instances |
| **VirtualBox / Parallels** | macOS / Windows VM-based isolation | Local VM |
| **Custom** | Roll your own | Anywhere via custom driver |

In 2026: **Kubernetes** executor dominates serious GitLab CI deployments. **Docker** for smaller teams. **Instance executor** is the AWS Fleet-style replacement for Docker-Machine.

## 3. Job execution flow

For a Docker-executor job:
1. Runner polls GitLab for a job
2. GitLab assigns: "run this job with these scripts in this image"
3. Runner pulls the image
4. Runner starts a container; clones the repo into it
5. Runs `before_script` + `script` + `after_script`
6. Captures logs + artifacts
7. Uploads artifacts back to GitLab
8. Reports status

## 4. Project Runners vs Group Runners vs Instance Runners

| Type | Scope | Set by |
|---|---|---|
| **Instance Runners** | All projects (admin-configured) | GitLab admin |
| **Group Runners** | All projects in a group | Group owner |
| **Project Runners** | One project only | Project maintainer |

For security: sensitive projects should use **Project Runners** they exclusively control. Shared instance runners run other people's jobs on the same host — risk of supply-chain attacks or noisy neighbors.

## 5. Tags + concurrency

Tag runners by capability:
```bash
gitlab-runner register --tag-list "linux,docker,aws,gpu"
```

Pipeline jobs request runners by tag:
```yaml
job:
  tags: [aws, gpu]
  script: ...
```

`concurrent` setting in `config.toml` defines max parallel jobs per runner. Don't oversaturate: a 4-CPU host running 8 concurrent jobs will be slower than 4.

## 6. Self-hosted runner on EC2

```bash
# Install on Ubuntu
curl -L --output /usr/local/bin/gitlab-runner \
  https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
chmod +x /usr/local/bin/gitlab-runner

# Create user
useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash

# Install service
gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
gitlab-runner start

# Register (new token-based flow since GitLab 16)
gitlab-runner register \
  --url https://gitlab.com \
  --token <authentication-token> \
  --executor docker \
  --docker-image alpine:3.20 \
  --description "ec2-aws-runner-1" \
  --tag-list "aws,docker"
```

Since GitLab 16 (2023), the runner registration uses an **authentication token** (per-runner) instead of the legacy registration token (per-project). The token flow is more secure: each runner has its own credential, revocable independently.

## 7. Kubernetes executor

```toml
# config.toml
[[runners]]
  name = "k8s-runner"
  url = "https://gitlab.com"
  token = "<auth-token>"
  executor = "kubernetes"
  [runners.kubernetes]
    namespace = "gitlab"
    image = "alpine:3.20"
    cpu_request = "500m"
    memory_request = "1Gi"
    service_account = "gitlab-runner"
    privileged = false
```

Each job → fresh K8s pod. Pod terminates after job. **Autoscaling for free** — the cluster's HPA + Karpenter handle node scale.

Image-build pattern: Kaniko or BuildKit (rootless) inside the K8s job, not DinD (DinD requires privileged, which violates Pod Security).

```yaml
build-image:
  image: gcr.io/kaniko-project/executor:debug
  script:
    - /kaniko/executor
        --context $CI_PROJECT_DIR
        --dockerfile $CI_PROJECT_DIR/Dockerfile
        --destination $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
        --cache=true
        --cache-repo $CI_REGISTRY_IMAGE/cache
```

## 8. GitLab SaaS Runners

For gitlab.com users without self-hosted:
- **Linux** (small, medium, large, x-large) — pay per minute beyond included tier
- **Linux GPU** — for ML training
- **macOS** — for iOS builds; $0.08/min in 2025
- **Windows** — for .NET builds
- **z-Linux + s390x** — for mainframe

Pricing (2026, gitlab.com):
- Free: 400 min/mo (Linux only)
- Premium: 10,000 min/mo
- Ultimate: 50,000 min/mo
- Additional units: $5/1000 compute units (varies by runner size)

## 9. Docker Runner on EC2

```toml
[[runners]]
  executor = "docker"
  [runners.docker]
    image = "alpine:3.20"
    privileged = false       # never true unless DinD specifically required
    pull_policy = ["if-not-present", "always"]
    volumes = ["/cache"]
    network_mode = "bridge"
    extra_hosts = []
    helper_image = "registry.gitlab.com/gitlab-org/gitlab-runner/gitlab-runner-helper:x86_64-latest"
```

Mount `/var/run/docker.sock` only when truly needed. Prefer Kaniko/BuildKit for builds.

## 10. Self-Managed GitLab Instance

For air-gap / regulated shops, host your own GitLab:
- Omnibus install (single host) — simplest
- Helm chart on K8s — for HA + scale
- Cloud-Native Helm (CNH) — newer; modular

GitLab.com vs self-managed:
- **Same software, different hosting**
- Self-managed = control + air-gap + custom integrations
- gitlab.com = no ops burden + SLAs

## 11. GitLab Runner versions compatibility

Runner version should match (or be one minor ahead of) GitLab Server version. Older runners may not support new pipeline features.

```bash
gitlab-runner --version
```

Update via package manager or container:
```bash
docker pull gitlab/gitlab-runner:latest
```

## 12. Quick self-check

1. What's the difference between a Runner and an Executor?
2. Why prefer Project Runners over Instance Runners for sensitive projects?
3. What replaced Docker-Machine executor for AWS auto-scaling?
4. Why is Kaniko preferred over DinD for image builds in K8s executor?
5. What changed in runner registration in GitLab 16?

(Answers: Runner is the process polling GitLab + dispatching; Executor is the actual environment (shell, docker, k8s pod) where the job runs; isolation — instance runners share host with other projects' jobs, risk of supply-chain or noisy neighbors; Instance executor (AWS Fleet-style) for auto-scaling on AWS; Kaniko doesn't need privileged pod or daemon socket — runs as rootless user; per-runner authentication tokens replaced per-project registration tokens — each runner now has its own revocable credential.)
