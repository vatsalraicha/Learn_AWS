# Quiz — Part 1 (DevOps Bootcamp: Modules 1-17)

Self-assessment quiz covering the DevOps Bootcamp fundamentals. Answer first, expand the answer block, score yourself.

## Section A — Core DevOps + Linux + Git

**Q1.** Name DORA's four (now five) key DevOps metrics.

<details><summary>Answer</summary>

Deployment Frequency, Lead Time for Changes, MTTR, Change Failure Rate, plus **Reliability** added in 2024 (SLO attainment).
</details>

**Q2.** What's `set -euo pipefail` for in a bash script?

<details><summary>Answer</summary>

`-e` = exit on first error, `-u` = error on undefined variable, `-o pipefail` = fail if any command in a pipeline fails (not just the last). Together: scripts that catch errors instead of silently continuing.
</details>

**Q3.** Why generate ed25519 SSH keys instead of RSA in 2026?

<details><summary>Answer</summary>

Smaller (256-bit), faster, equivalent security to RSA-4096. Default modern recommendation.
</details>

**Q4.** What's the difference between `git pull` and `git fetch`?

<details><summary>Answer</summary>

`fetch` downloads remote changes (read-only). `pull` = `fetch` + `merge` (or `rebase`).
</details>

**Q5.** How do you recover a commit you `git reset --hard`'d away?

<details><summary>Answer</summary>

`git reflog` shows every HEAD movement (kept ~90 days). Then `git reset --hard HEAD@{n}` to the desired state.
</details>

## Section B — Build tools + Cloud + Nexus + Docker

**Q6.** What replaced Poetry as the modern Python default in 2025-2026 and why?

<details><summary>Answer</summary>

**uv** (from Astral, Rust). Single binary, ~10-100x faster than pip, lockfile-first, manages Python versions too.
</details>

**Q7.** Why is `docker-compose` (v1) replaced by `docker compose` (v2)?

<details><summary>Answer</summary>

v1 was Python-based and unmaintained. v2 is Go-written, a plugin to the Docker CLI, actively developed.
</details>

**Q8.** Name three Nexus alternatives and when you'd pick each.

<details><summary>Answer</summary>

- **AWS CodeArtifact** for AWS-native shops
- **GitHub Packages** for GitHub-native shops
- **JFrog Artifactory** for regulated finance (Cap One uses this)
- **GitLab Package Registry** for GitLab-native shops
</details>

**Q9.** What's the difference between a Docker image and a container?

<details><summary>Answer</summary>

Image = immutable, layered blueprint. Container = running instance of an image with its own writable layer + isolated process namespaces.
</details>

**Q10.** Why is multi-stage Docker build a best practice?

<details><summary>Answer</summary>

Builder stage has build tools + source; runtime stage has only the artifact + runtime deps. Smaller final image, smaller attack surface, faster pulls.
</details>

## Section C — Jenkins + AWS + K8s

**Q11.** What's a Multibranch Pipeline and what does it auto-discover?

<details><summary>Answer</summary>

Jenkins job type that scans a Git repo for branches with `Jenkinsfile`s, creates sub-jobs per branch (and per PR with the GitHub source plugin). Each branch's Jenkinsfile runs that branch's pipeline.
</details>

**Q12.** Why use OIDC + IAM Role over AWS access keys in CI/CD?

<details><summary>Answer</summary>

Short-lived credentials, nothing to leak or rotate, audited per-job in CloudTrail, scoped via trust policy to specific (project, branch).
</details>

**Q13.** Name three things a fresh `eksctl create cluster` does NOT give you.

<details><summary>Answer</summary>

CSI driver, autoscaler (Karpenter or CAS), ingress controller, cert-manager, monitoring stack, GitOps controller, policy engine. EKS Blueprints fills this gap.
</details>

**Q14.** What's the difference between IRSA and EKS Pod Identity?

<details><summary>Answer</summary>

IRSA uses OIDC provider + trust policy on the SA name in the role. Pod Identity uses Pod Identity Agent DaemonSet + EKS API association — simpler trust policy + simpler ops.
</details>

## Section D — Terraform + Python + Ansible + Prometheus

**Q15.** What's the difference between Terraform and OpenTofu?

<details><summary>Answer</summary>

OpenTofu is the OSS fork after HashiCorp's BUSL relicense (Aug 2023). Same HCL, MPL 2.0, Linux Foundation governance. Matters for OSS-purity shops and avoiding vendor lock-in.
</details>

**Q16.** When use Boto3 over Terraform?

<details><summary>Answer</summary>

Boto3 for: runtime/operations (backup, cleanup), ad-hoc scripts, things needing logic (if-then), bulk ops across accounts. Terraform for static infra.
</details>

**Q17.** Why is Ansible-to-K8s an anti-pattern in 2026?

<details><summary>Answer</summary>

K8s has native declarative tooling (Helm, Kustomize, ArgoCD/Flux). Ansible's imperative push model doesn't match K8s's pull-based reconciliation.
</details>

**Q18.** What's a Prometheus ServiceMonitor and what does it enable?

<details><summary>Answer</summary>

CRD from Prometheus Operator that selects K8s Services to scrape. Replaces hand-editing `prometheus.yml` — declarative scrape targets via labels.
</details>

**Q19.** What's the four-golden-signals SRE framework?

<details><summary>Answer</summary>

Latency, Traffic, Errors, Saturation. From Google's SRE book.
</details>

**Q20.** Why is cardinality explosion a Prometheus problem and how to avoid it?

<details><summary>Answer</summary>

High-cardinality labels (user_id, URL with path params) blow up the index. Use endpoint templates (`/users/:id` not `/users/12345`) and finite label values.
</details>

---

**Scoring**: 18-20 correct → solid command of DevOps Bootcamp. 14-17 → revisit weak areas. < 14 → re-read corresponding modules.
