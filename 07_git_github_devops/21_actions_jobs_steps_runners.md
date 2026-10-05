# 21 — GitHub Actions: jobs, steps, runners (hosted vs self-hosted)

> *"Jobs run on runners. Steps run sequentially within a job. Runners are where the constraints — and the security boundary — live."*

## Why this module exists

The "where does this actually execute?" question matters for cost, performance, security, and access to private resources (VPCs, GPUs, large data). This module covers the runner taxonomy + the job/step model.

---

## 1. Jobs and steps

```yaml
jobs:
  test:                                # job ID
    name: "Test on Python 3.11"        # display name
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout
        uses: actions/checkout@v6      # `uses:` step — calls an action
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install
        run: pip install -e ".[dev]"   # `run:` step — runs a shell command
      - name: Test
        run: pytest -v
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}

  lint:                                # second job — runs in parallel with `test` by default
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
      - run: pip install ruff
      - run: ruff check src tests
```

Rules:
- Jobs in the same workflow run **in parallel** by default. Use `needs:` to serialize (see [module 24](24_actions_outputs_needs_concurrency.md)).
- Steps in a job run **sequentially**. If one fails, subsequent steps are skipped unless `continue-on-error: true` or `if: always()`.
- Each job runs on its own **fresh runner instance** — no shared state between jobs. To pass data, use **artifacts** (see [module 25](25_actions_cache_artifacts_matrix.md)) or **outputs** (see [module 24](24_actions_outputs_needs_concurrency.md)).
- A job has its own filesystem, network, processes. Job-level `env:`, `defaults:`, `permissions:` apply to all its steps.

---

## 2. Runners — the taxonomy

| Type | Where | Pros | Cons |
|---|---|---|---|
| **GitHub-hosted (standard)** | GitHub's infrastructure | Zero ops, regular updates, included minutes | Public IPs only, no VPC access, generic hardware |
| **GitHub-hosted (larger)** | GitHub, beefier | More CPU/RAM (up to 64 vCPU + 256GB), more $ | Same network constraints |
| **GitHub-hosted ARM64** | GitHub | ARM64 native (no QEMU) | Lower availability in some regions |
| **GitHub-hosted GPU** | GitHub, NVIDIA T4 | Native GPU access, no driver setup | very expensive, limited availability |
| **GitHub-hosted macOS** | GitHub, mac mini infra | macOS for iOS/Mac builds | Expensive — 10× minute multiplier |
| **GitHub-hosted Windows** | GitHub | Windows builds | 2× minute multiplier |
| **Self-hosted (VM)** | Your infra | VPC access, custom HW, private network | You own ops |
| **Self-hosted ARC (K8s)** | Your K8s cluster | Ephemeral, autoscaling, isolated per job | K8s expertise required |
| **Self-hosted GPU** | Your infra (or ARC) | A100/H100, multi-GPU, custom CUDA | very expensive, ops burden |

For Capital One: standard GitHub-hosted for most CI; **ARC on EKS** for jobs needing VPC access, custom hardware, or GPU. ARC is covered in [module 28](28_actions_self_hosted_arc_gpu.md).

---

## 3. GitHub-hosted runner specs

| OS image | vCPU | RAM | Storage | Minute multiplier |
|---|---|---|---|---|
| `ubuntu-22.04`, `ubuntu-24.04`, `ubuntu-latest` (=24.04) | 4 | 16 GB | 14 GB SSD | 1× |
| `windows-2022`, `windows-2025` | 4 | 16 GB | 14 GB SSD | 2× |
| `macos-13`, `macos-14`, `macos-15` | 3 | 7 GB | 14 GB SSD | 10× |
| `macos-14-xlarge` (Apple Silicon) | 6 | 14 GB | 14 GB SSD | 10× |
| Larger Linux (4/8/16/32/64 vCPU) | configurable | up to 256 GB | up to 2 TB SSD | scales with size |
| Linux ARM64 | 4/8/16/32 | configurable | configurable | depends on plan |
| GPU (NVIDIA T4) | 4 vCPU + 16 GB + T4 | — | — | 1.5× (or per-minute pricing) |

Standard `ubuntu-latest` runner has roughly:
- Preinstalled: git, gh, docker, kubectl, helm, python (3.9–3.13), node (current LTS + others), Java JDKs, Go, Ruby, Rust, .NET SDK, Azure CLI, gcloud CLI, AWS CLI, Terraform, Pulumi, etc.
- Available CPU architectures: x86_64 (standard) or aarch64 (separate runner)
- IPv4 + IPv6 networking, no static IP (egress IPs change daily — published list at [actions/runner-images](https://api.github.com/meta))

Full image manifest: each ubuntu-latest run prints "Runner Image" at the top → links to GitHub's [actions/runner-images](https://github.com/actions/runner-images) repo where every release's tool versions are listed.

---

## 4. Runner selection patterns

```yaml
# Single runner
runs-on: ubuntu-latest

# OS choice
runs-on: ubuntu-22.04
runs-on: macos-14
runs-on: windows-2025

# Pinning to specific architecture
runs-on: ubuntu-24.04-arm

# Larger GitHub-hosted runner (configured at org level)
runs-on: org-large-runner-16cpu

# Self-hosted runner with labels
runs-on: [self-hosted, linux, x64, gpu]
runs-on: self-hosted

# Multiple OS — needs the `strategy.matrix` (see module 25)
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
runs-on: ${{ matrix.os }}

# Group of runners (ARC scale set or org-level group)
runs-on:
  group: gpu-runners
  labels: [self-hosted, linux, gpu, a100]
```

**Self-hosted runners** are matched by labels. A workflow's `runs-on: [self-hosted, linux, x64, gpu]` matches the first runner offering ALL those labels. ARC scale sets register with a runner-set name plus standard labels — see [module 28](28_actions_self_hosted_arc_gpu.md).

---

## 5. Step types — `uses:` vs `run:`

```yaml
steps:
  # `uses:` — calls a reusable action
  - uses: actions/checkout@v6
  - uses: actions/setup-python@v5
    with:
      python-version: "3.11"
      cache: pip
  - uses: org/internal-action@v1.2

  # `run:` — shell command
  - name: Install deps
    run: pip install -e ".[dev]"

  # Multi-line `run:`
  - name: Build + test
    run: |
      pip install -e ".[dev]"
      pytest tests/ -v
      ruff check src

  # `run:` with shell selection
  - run: Write-Output "Hello PowerShell"
    shell: pwsh
  - run: Write-Output "Hello PSh on Linux"
    shell: pwsh         # PowerShell Core, also available on Linux
  - run: echo "Hello bash"
    shell: bash         # default on Linux/macOS

  # `run:` with working directory
  - run: pytest
    working-directory: ./services/api
```

Default shell on Linux/macOS is `bash --noprofile --norc -eo pipefail {0}`. The `-e` flag is critical — exit on first error. Without it, a `cmd1 && cmd2` style script may proceed past failures. Don't override the default unless you know why.

---

## 6. Conditional execution

```yaml
steps:
  - run: pytest tests/unit
  - run: pytest tests/integration
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

  - name: Notify Slack on failure
    if: failure()                       # only if previous step(s) failed
    run: curl -X POST $SLACK_WEBHOOK -d '{"text":"CI failed"}'

  - name: Always run cleanup
    if: always()
    run: rm -rf /tmp/build

  - name: Run if NOT cancelled
    if: ${{ !cancelled() }}
    run: echo "Cleanup"
```

Status functions:
- `success()` — true if all prior steps succeeded (default condition for non-`if` steps)
- `failure()` — true if any prior step failed
- `always()` — true regardless
- `cancelled()` — true if workflow was cancelled

`if:` can use full expressions — see [module 22](22_actions_marketplace_expressions.md) for the syntax.

---

## 7. `defaults:` and `env:`

```yaml
defaults:
  run:
    shell: bash
    working-directory: ./services/api

env:
  PYTHON_VERSION: "3.11"
  DEBUG: "false"

jobs:
  test:
    env:                                # job-level env (overrides workflow)
      DEBUG: "true"
    steps:
      - run: echo "Python: $PYTHON_VERSION, Debug: $DEBUG"
        env:                            # step-level env (overrides job + workflow)
          EXTRA: "something"
```

Scope: step `env:` > job `env:` > workflow `env:`.

---

## 8. `timeout-minutes`

```yaml
jobs:
  test:
    timeout-minutes: 30                 # job-level (cancels job after 30 min)
    steps:
      - run: long-running-thing
        timeout-minutes: 5              # step-level (cancels just this step after 5 min)
```

Defaults:
- Workflow: 6 hours
- Job: 6 hours (max on GitHub-hosted; max 35 days on self-hosted)
- Step: no default

**Set explicit `timeout-minutes` on every job.** A hung process at 5 hours and 59 minutes still bills you for 6 hours. Cap to your worst-case-reasonable time.

---

## 9. `continue-on-error`

```yaml
- name: Run flaky integration tests
  run: pytest tests/integration
  continue-on-error: true            # don't fail the job if this step fails

- name: Always-required step
  run: pytest tests/unit
  # No continue-on-error → if this fails, job fails
```

Use sparingly. Tests that are "OK if they fail sometimes" are tests that don't really mean anything. Better: fix flakiness; quarantine truly flaky tests in a separate workflow that doesn't gate merges.

---

## 10. `services:` — sidecar containers

Spin up containers alongside your job (e.g., a Postgres instance for integration tests):

```yaml
jobs:
  integration-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v6
      - run: pytest tests/integration
        env:
          DATABASE_URL: "postgresql://postgres:postgres@localhost:5432/testdb"
          REDIS_URL: "redis://localhost:6379"
```

Better than wrestling with `docker run` inline. The runner manages container lifecycle and health.

Works only on Linux runners (services use Docker; not supported on macOS/Windows GitHub-hosted).

---

## 11. The `container:` job-level

Run the entire job inside a container:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: python:3.11-slim
      credentials:
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
      env:
        FOO: bar
      volumes:
        - my-vol:/data
    steps:
      - run: python --version
```

The whole job runs `inside` the specified image. Useful for non-standard toolchains or pinning the exact build environment. **But**: slower (image pull), some actions don't work well inside containers, debugging is harder. Use only when you need it.

---

## 12. Cross-references

- Self-hosted runners + ARC + GPU → [module 28](28_actions_self_hosted_arc_gpu.md).
- Matrix builds (one job, many runner specs) → [module 25](25_actions_cache_artifacts_matrix.md).
- Job dependencies via `needs:` → [module 24](24_actions_outputs_needs_concurrency.md).
- Environments + manual approval gates → [module 30](30_actions_environments_protection.md).
