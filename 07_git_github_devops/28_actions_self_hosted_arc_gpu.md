# 28 — ⭐ Self-hosted runners + Actions Runner Controller (ARC) + GPU runners

> *"GitHub-hosted runners are great. Until you need VPC-only access to a Snowflake account, or a GPU for ML training, or a 64-core box for a Bazel build. Then you go self-hosted — and at Capital One scale, that means ARC on EKS."*

## Why this module exists

Self-hosted runners are the path to running Actions on your own infrastructure. **ARC (Actions Runner Controller)** is the production-grade Kubernetes operator for autoscaling self-hosted runners — and the reference pattern for Capital One-style organizations running CI/CD inside their VPC. This module covers the architecture, security, and GPU-runner specifics.

---

## 1. When you need self-hosted

| Reason | Self-hosted is the answer? |
|---|---|
| VPC-only resources (private RDS, internal APIs) | ✅ Yes |
| GPU for ML training | ✅ Yes (or GitHub-hosted GPU at very expensive) |
| Big machines (>64 vCPU, >256 GB RAM) | ✅ Maybe |
| Long-running jobs (>6h) | ✅ Yes |
| Compliance requires "compute in our cloud" | ✅ Yes |
| Custom hardware (FPGA, Apple Silicon, ARM) | ✅ Yes |
| Caching very large datasets on a persistent volume | ✅ Yes |
| Just want to save money | ❌ Usually not — TCO of self-hosted ops exceeds GitHub-hosted at small scale |

Capital One uses self-hosted (almost certainly ARC on EKS) for the VPC-access requirement primarily — Snowflake on private networking, internal APIs, model artifacts in private S3.

---

## 2. The three deployment models

| Model | What | Trade-off |
|---|---|---|
| **Standalone runner on a VM** | `./config.sh` + `./run.sh` on an EC2 instance | Simple; doesn't autoscale; one job at a time per instance |
| **Static pool on K8s (legacy ARC)** | Deployment of runner pods, fixed count | Wasteful (idle pods burn money); deprecated |
| **Ephemeral runner scale sets (ARC modern)** | Operator spins up one pod per job, deletes after | **The standard.** Autoscales to demand; clean state per job |

Modern ARC = ephemeral runner scale sets. The legacy "runner deployment" model is deprecated.

---

## 3. ARC architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Your K8s cluster (e.g., EKS in capital-one's CI account)    │
│                                                                │
│   ┌──────────────────────────────────────┐                    │
│   │  gha-runner-scale-set-controller     │  (1 pod, watches CRDs)
│   │  (the operator)                      │                    │
│   └──────────────────────────────────────┘                    │
│                  │                                              │
│                  │ creates                                       │
│                  ▼                                              │
│   ┌──────────────────────────────────────┐                    │
│   │  Listener pod (long-poll)            │  (1 per scale set)
│   │  HTTPS to GitHub Actions Service     │                    │
│   └──────────────────────────────────────┘                    │
│                  │                                              │
│                  │ when job available, patches:                 │
│                  ▼                                              │
│   ┌──────────────────────────────────────┐                    │
│   │  EphemeralRunnerSet CR               │                    │
│   └──────────────────────────────────────┘                    │
│                  │                                              │
│                  │ K8s reconciles                               │
│                  ▼                                              │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│   │ Runner   │  │ Runner   │  │ Runner   │  (N ephemeral pods)
│   │ pod #1   │  │ pod #2   │  │ pod #3   │                    │
│   └──────────┘  └──────────┘  └──────────┘                    │
└──────────────────────────────────────────────────────────────┘
                       │ HTTPS                       │
                       ▼                              ▼
                  ┌──────────────────────────────────┐
                  │  github.com Actions Service       │
                  └──────────────────────────────────┘
```

Lifecycle of a job:
1. Workflow with `runs-on: my-scale-set` queued at GitHub.
2. Listener pod (long-polling GitHub) sees the job available.
3. Listener patches `EphemeralRunnerSet` CR with `+1` desired runner.
4. Controller spawns a runner pod with a JIT (just-in-time) GitHub registration token.
5. Runner pod registers, accepts the job, executes it, reports back to GitHub.
6. Job completes → pod is deleted (ephemeral).

If no jobs are queued, no runner pods exist. **Zero idle cost.**

---

## 4. Installation

Pre-reqs: K8s cluster (EKS 1.28+ for ARC v0.10+), Helm 3, cert-manager (for webhook certs in some configurations).

```bash
# Controller
helm install arc \
  --namespace arc-systems \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller

# Runner scale set — one per "runner identity" you want
helm install arc-runner-set \
  --namespace arc-runners \
  --create-namespace \
  --set githubConfigUrl="https://github.com/capitalone" \
  --set githubConfigSecret.github_token="$GH_PAT" \   # or use App auth — preferred
  --set minRunners=0 \
  --set maxRunners=50 \
  --set runnerScaleSetName=ml-pool \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
```

Better — use **GitHub App auth** (no PAT):

```yaml
# values.yaml
githubConfigUrl: "https://github.com/capitalone"
githubConfigSecret:
  github_app_id: "12345"
  github_app_installation_id: "67890"
  github_app_private_key: |
    -----BEGIN RSA PRIVATE KEY-----
    ...
    -----END RSA PRIVATE KEY-----
```

The GitHub App needs `Actions: read`, `Self-hosted runners: write`, `Administration: read` for the org.

Workflows now reference:

```yaml
jobs:
  build:
    runs-on: ml-pool                # matches runnerScaleSetName
    steps: ...
```

---

## 5. Container modes

ARC runner pods need to run user-defined Docker images and commands. Two modes:

### `dind` (Docker-in-Docker)

Runner pod has its own Docker daemon. Privileged. Simple but security-concerning.

```yaml
containerMode:
  type: dind
```

### `kubernetes` (preferred)

Runner pod schedules sibling pods in the same namespace for each container/service the job needs. No privileged daemon. Requires the **container hooks** (built into the runner image).

```yaml
containerMode:
  type: kubernetes
  kubernetesModeWorkVolumeClaim:
    accessModes: [ReadWriteOnce]
    storageClassName: gp3
    resources:
      requests:
        storage: 20Gi
```

For Capital One regulated env: `kubernetes` mode is the safer choice.

---

## 6. GPU runners

ARC supports GPU pods natively — just declare GPU resources in the scale set:

```yaml
# values.yaml for gpu-pool scale set
runnerScaleSetName: gpu-pool
template:
  spec:
    nodeSelector:
      node.kubernetes.io/instance-type: g5.xlarge        # A10G GPU
    tolerations:
      - key: nvidia.com/gpu
        operator: Exists
    containers:
      - name: runner
        image: ghcr.io/actions/actions-runner:latest
        resources:
          limits:
            nvidia.com/gpu: 1
```

The runner pod claims 1 GPU. The base image is `ghcr.io/actions/actions-runner:latest` — for ML you'll likely build a custom image that includes CUDA toolkit, PyTorch, etc. (so jobs don't repeatedly pip-install).

Workflow:

```yaml
jobs:
  train:
    runs-on: gpu-pool
    timeout-minutes: 480
    steps:
      - uses: actions/checkout@v6
      - run: nvidia-smi
      - run: python train.py
```

GitHub Hosted GPU runners (T4) are an alternative if you don't want to run K8s. Trade-offs: $1.50/min vs spot GPU instance pricing; T4 only; no VPC access.

---

## 7. Security model

Self-hosted runners are a security risk surface that GitHub-hosted runners aren't. Key concerns:

### Runner sees the source code

Per-job ephemeral pods solve "runner has leftover state from previous job." But:
- Public-repo PRs from forks should NEVER target self-hosted runners. GitHub disallows this by default for public repos.
- For private repos: still configure `runs-on: ubuntu-latest` for PR builds; only use self-hosted for `push` events / merged code.

### Network egress

Self-hosted runners can reach into your VPC. If a job is compromised (malicious dep), it can:
- Hit internal APIs
- Exfiltrate secrets via DNS to attacker-controlled domains
- Lateral movement to other services in the VPC

Mitigations:
- **Egress allowlist** at K8s NetworkPolicy: runner pods can only reach github.com + ECR + a specific list.
- **No long-lived secrets** in runner pods. Use OIDC + AWS role assumption (see [module 29](29_actions_oidc_aws.md)).
- **Workload Identity** for K8s ServiceAccount → IAM role (IRSA on EKS).
- **Pod Security Standards** enforce non-root, read-only root filesystem where possible.

### Runner identity

Each scale set should have:
- A dedicated K8s ServiceAccount
- An IRSA-mapped IAM role with minimum permissions
- A dedicated GitHub App for that scale set (or per-tier of trust)
- Namespace isolation (runner pods in `arc-runners`, controller in `arc-systems`)

### Audit

- ARC controller logs: every runner pod creation/deletion.
- GitHub audit log: every job run, including self-hosted runner ID.
- Pair the two for compliance evidence.

---

## 8. Cost economics

GitHub-hosted standard runner: $0.008/min (Linux). 4 vCPU, 16 GB. Minimum 1-minute billing.

Self-hosted on EKS:
- m5.xlarge spot: ~$0.05/hr × (1 hr / 60 min) = $0.0008/min per node. With 4 vCPU per pod and bin-packing, ~$0.0002/min per pod-second of compute.
- Plus K8s overhead, plus persistent volume, plus the platform team's time.

Break-even: roughly 100k Actions-minutes/month. Below that, GitHub-hosted is cheaper. Above that, self-hosted wins on raw compute — but the ops team cost is real.

For Capital One scale (50k builds/day × avg several mins each = millions of minutes/month), self-hosted dominates on raw compute. The reason to do it isn't cost — it's **VPC access**.

GPU runners: GitHub-hosted T4 is convenient but very expensive for sustained workloads. Self-hosted on g5/p4d instances + spot is much cheaper for training.

---

## 9. Runner groups (org-level)

Group runners so different teams/repos have different pools:

- `ml-team-pool` — only ml-team repos can use
- `prod-deploy-pool` — only repos with prod environment access can use
- `default-pool` — everyone else

Configured at Org → Settings → Actions → Runner groups. Each group lists:
- Which repositories can use it (all / private / selected)
- Which workflows can use it
- The runners themselves (registered via ARC scale set name)

Workflows reference:

```yaml
runs-on:
  group: ml-team-pool
  labels: [self-hosted, linux, gpu]
```

The `group:` + `labels:` combo restricts: must be in `ml-team-pool`, AND have those labels.

---

## 10. The Capital One-shape playbook

1. **Tier the pools**:
   - `default` — small CPU runners for general CI
   - `large` — bigger instances for Bazel/Docker builds
   - `gpu` — GPU instances for ML training
   - `prod-deploy` — runners with OIDC trust to prod AWS accounts (restricted)
2. **App-per-pool**: each scale set has its own GitHub App, with minimum permissions.
3. **K8s namespace-per-pool**: isolation.
4. **OIDC-only**: no AWS credentials live on runners.
5. **NetworkPolicy egress allowlist**: enforce.
6. **Audit + alerting**: ARC controller logs to CloudWatch; abnormal pod-creation patterns alert SRE.
7. **Image hygiene**: monthly rebuild of custom runner images; scan for CVEs.

---

## 11. Cross-references

- OIDC trust for self-hosted runner identity → [module 29](29_actions_oidc_aws.md).
- Runner-pod identity via IRSA → Topic 04 module 02 (IAM deep) + module 33 (EKS foundations).
- Cost optimization of Actions overall → [module 31](31_actions_token_cost_templates.md).
- The role of self-hosted runners in Capital One's hybrid Jenkins+Actions reality → [module 56](56_capital_one_devops_deep.md).
