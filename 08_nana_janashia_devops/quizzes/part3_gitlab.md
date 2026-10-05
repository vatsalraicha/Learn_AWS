# Quiz — Part 3 (GitLab CI/CD: Modules 39-46)

**Q1.** When pick GitLab over GitHub Actions vs Jenkins?

<details><summary>Answer</summary>

- **Jenkins**: regulated finance, air-gap requirements, large existing Groovy investment
- **GitHub Actions**: code on GitHub, simplest path, GitHub-native ecosystem
- **GitLab**: all-in-one DevSecOps (Ultimate tier), single-vendor procurement, compliance frameworks built in
</details>

**Q2.** What's the difference between `stages:` and `needs:` in `.gitlab-ci.yml`?

<details><summary>Answer</summary>

Stages = sequential groups (a stage waits for all previous-stage jobs). `needs:` = explicit DAG dependencies between jobs — a job starts as soon as listed dependencies finish, regardless of stage boundary.
</details>

**Q3.** What replaced legacy `only`/`except` in modern GitLab CI?

<details><summary>Answer</summary>

`rules:` — more flexible, supports `if`/`changes`/`exists`/`when`, composable.
</details>

**Q4.** What's a merged-results pipeline?

<details><summary>Answer</summary>

Pipeline runs on the *merged* result (source branch + target merged in memory) — closer to what production will see after merge. Catches conflicts that don't exist in source alone.
</details>

**Q5.** What's the difference between a Runner and an Executor?

<details><summary>Answer</summary>

**Runner** = the process polling GitLab + dispatching jobs. **Executor** = the actual environment where the job runs (shell, docker, k8s pod, ssh).
</details>

**Q6.** Why is Project Runners preferred over Instance Runners for sensitive projects?

<details><summary>Answer</summary>

Isolation — Instance Runners share host with other projects' jobs; risk of supply-chain attack or noisy neighbors. Project Runners run only your team's jobs.
</details>

**Q7.** Why use Kaniko instead of `docker build` in a K8s GitLab runner?

<details><summary>Answer</summary>

Kaniko builds images without a privileged Docker daemon or `docker.sock` mount — works in unprivileged K8s pods, respecting Pod Security Standards.
</details>

**Q8.** What does GitLab Environments add over just deploy jobs?

<details><summary>Answer</summary>

Deployment history per env, easy rollback, MR shows latest deploy URL, dashboards for compliance.
</details>

**Q9.** What replaced "CI Templates" in GitLab 17+?

<details><summary>Answer</summary>

**CI/CD Components** — versioned, catalog-published, typed inputs, dedicated test pipeline.
</details>

**Q10.** What's the difference between `include: project:` and `include: component:`?

<details><summary>Answer</summary>

`include: project:` is older — includes a YAML file from another project by path + ref. `include: component:` is newer — references a CI/CD Component with typed inputs + semver versioning + catalog discoverability.
</details>

**Q11.** Why pin Components to exact version (`@v1.2.3`) in production?

<details><summary>Answer</summary>

Supply-chain safety — `@~latest` could change unexpectedly and break your pipeline. Treat Components like dependencies.
</details>

**Q12.** What problem does GitLab Agent for Kubernetes solve over kubeconfig-in-CI?

<details><summary>Answer</summary>

Agent dials out from cluster to GitLab (no inbound traffic to cluster). No kubeconfig stored in CI vars. Audit by Git history (GitOps mode).
</details>

**Q13.** What's the difference between Agent CI access mode and GitOps mode?

<details><summary>Answer</summary>

**CI access mode**: pipelines use `kubectl` via the Agent (push). **GitOps mode**: Agent pulls manifests from a Git repo + applies autonomously (no CI involvement after manifest commit).
</details>

**Q14.** Why does `id_tokens:` block matter in `.gitlab-ci.yml` for AWS OIDC?

<details><summary>Answer</summary>

Tells GitLab to issue an OIDC JWT for that job with the specified audience — required for AWS to verify the token in `AssumeRoleWithWebIdentity`.
</details>

**Q15.** Why split CI roles into "plan" and "apply" for Terraform?

<details><summary>Answer</summary>

Least privilege — plan never needs write permissions, so a compromise in a plan job can't apply destructive changes. Apply role only assumable on protected branches.
</details>

---

**Scoring**: 13+ → GitLab CI competent. 9-12 → solid baseline. < 9 → revisit modules 39-46.
