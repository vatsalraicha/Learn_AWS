# 39 — GitLab CI/CD vs GitHub Actions vs Jenkins

## Why this module exists

Three CI/CD platforms dominate 2026. Which one to pick for a new project — and why teams have all three — is a real architectural question.

## 1. The market shares (rough, 2026)

| Platform | Share |
|---|---|
| Jenkins (incl. CloudBees CI) | ~40% |
| GitHub Actions | ~35% (and rising) |
| GitLab CI | ~15% |
| CircleCI / Travis / Bitbucket Pipelines / Buildkite / Drone / Tekton / others | ~10% |

Jenkins is declining (slowly) in greenfield; Actions is gaining. GitLab is ~stable. In regulated finance, Jenkins is still dominant due to self-hostability + air-gap support.

## 2. Side-by-side comparison

| Feature | Jenkins | GitHub Actions | GitLab CI |
|---|---|---|---|
| **Hosting** | Self-hosted (CloudBees SaaS exists) | SaaS-first (Enterprise Server on-prem) | SaaS + Self-hosted |
| **Pricing model** | Free OSS / CloudBees license | Per-user + per-minute | Per-user (Free/Premium/Ultimate) |
| **Config language** | Groovy (Jenkinsfile) | YAML | YAML |
| **Plugin ecosystem** | Massive (1800+) | Marketplace, fast-growing | Limited (built-in features instead) |
| **Built-in registry** | Plugin-based | GitHub Packages / GHCR | Built-in container + package registry |
| **Built-in DevSecOps** | Plugins | GHAS (paid; SAST + Secret Scanning) | Ultimate (full SAST + DAST + SCA + Secret + Container) |
| **Self-hosted runners** | Native (agents) | Yes (ARC for K8s) | Yes (well-supported) |
| **Air-gap capable** | Yes | Enterprise Server | Self-managed |
| **Workflow language** | Imperative Groovy | Declarative YAML | Declarative YAML |
| **Learning curve** | Steep (Groovy + plugins) | Mild | Mild |
| **K8s deploy** | Plugins | Actions | GitLab Agent for K8s |
| **Best for** | Regulated / legacy / large orgs | GitHub-native projects | All-in-one DevSecOps |

## 3. When to pick each

### Pick Jenkins when:
- Regulated finance / healthcare (air-gap, on-prem mandates)
- Large existing investment in Groovy + shared libraries
- Need plugin-level customization
- Multi-master, multi-tenant at scale
- Capital One reality

### Pick GitHub Actions when:
- Your code lives on GitHub
- You want the path of least resistance
- You're OK with SaaS (Enterprise Server if you need self-host)
- Strong DevSecOps via GHAS

### Pick GitLab CI when:
- You want one platform for SCM + CI + DevSecOps + registry + IaC + ML registry
- Single-vendor procurement matters
- Strong DevSecOps requirements with budget for Ultimate
- Compliance frameworks built-in

## 4. The "you have all three" reality

Big orgs end up with:
- **Jenkins** for legacy + regulated workloads (Capital One)
- **GitHub Actions** for new microservices + open-source contributions
- **GitLab CI** for teams that want all-in-one

This is fine if you accept the cost: shared libraries don't transfer, runners don't share, observability is split.

## 5. Architectural primitives — vocabulary translation

| Concept | Jenkins | Actions | GitLab |
|---|---|---|---|
| **Pipeline definition** | Jenkinsfile | workflow YAML | .gitlab-ci.yml |
| **Job execution unit** | Stage / Step | Job / Step | Job |
| **Build agent** | Agent | Runner | Runner |
| **Secret storage** | Credentials Store | Secrets | CI/CD Variables |
| **Reusable logic** | Shared Library | Reusable Workflow / Composite Action | CI/CD Component / include |
| **Trigger** | SCM polling / webhook | Event | Push / MR / Schedule |
| **Plugin ecosystem** | Plugins | Marketplace Actions | Limited (built-in) |
| **Environment** | (3rd party) | Environment | Environment |
| **K8s deploy auth** | Plugin / kubeconfig | OIDC + IAM | GitLab Agent |

## 6. Migration paths

### Jenkins → GitLab CI
- Convert Jenkinsfile → .gitlab-ci.yml (Mostly manual; Jenkinsfile Groovy doesn't translate 1:1)
- Migrate shared libraries → CI/CD Components or includes
- Replace plugin functionality with GitLab built-ins
- Re-provision runners as GitLab Runners on EC2/K8s
- Move credentials from Jenkins Credentials → GitLab Variables (or OIDC)

### Jenkins → Actions
- Similar exercise: Jenkinsfile → workflow YAML
- Self-hosted runners as ARC pods on K8s
- Shared libraries → Composite Actions or Reusable Workflows
- See [Topic 07](../07_git_github_devops/) for the Actions deep dive

### Actions → GitLab
- Generally easier than Jenkins → either (YAML to YAML)
- ARC runners → GitLab K8s executor
- Reusable workflows → GitLab includes / Components
- Marketplace Actions → custom job templates (less off-the-shelf in GitLab)

### GitLab → Actions
- YAML → YAML; mostly mechanical
- Use Marketplace Actions for what GitLab built-in did
- For DevSecOps coverage: GHAS replaces GitLab Ultimate scanners

## 7. Cost — the back-of-envelope

### GitHub Actions
- $0.008/min for Linux on Free; included minutes per tier
- Larger runners much more expensive
- Free public repo runners

### GitLab CI SaaS
- 400 free min/mo on Free tier
- 10,000 included min/mo on Premium ($29/user/mo)
- $0.10/min for additional Linux compute units in 2025
- Or self-hosted runners on your infra

### Jenkins
- OSS free; you pay infra + ops
- CloudBees CI: opaque enterprise pricing; ~$5-20/user/mo at scale

For a 50-engineer team:
- Actions: $200-1000/mo (depending on minute usage + GHAS licensing)
- GitLab Ultimate: $4,950/mo (50 × $99) — yikes — but includes everything
- Jenkins OSS: ~$500/mo infra cost (k8s + ec2 agents) + ~1 engineer

## 8. DevSecOps coverage compared

| | Jenkins | Actions | GitLab |
|---|---|---|---|
| **Secret scanning in repo** | Plugins | Free + Push Protection paid via GHAS | Free + Premium for Detection |
| **SAST** | Plugins (Sonar, etc.) | CodeQL via GHAS | Ultimate built-in |
| **SCA** | Plugins | Dependabot free + GHAS | Ultimate built-in |
| **Container scanning** | Plugins | GHAS Container | Ultimate built-in |
| **DAST** | Plugins (ZAP) | 3rd party Actions | Ultimate built-in |
| **License scanning** | Plugins | GHAS | Ultimate built-in |
| **API fuzzing** | Plugins | 3rd party | Ultimate built-in |
| **Vuln tracker** | Plugins (DefectDojo) | Security tab | Built-in Vulnerability Report |

GitLab Ultimate's strength is "everything in one console." The cost is the platform lock-in.

## 9. The CI/CD platform team angle

If you're an AI/ML engineer at Capital One, you'll **consume** Jenkins, not build the platform. Your interview-relevant skills:
- Understand the platform model (controller + agents, runners, etc.)
- Read + write Jenkinsfile / .gitlab-ci.yml / Actions YAML
- Know the security model (OIDC + IAM roles)
- Know how to debug pipeline failures
- Know how to optimize (caching, parallelism, matrix)

You don't need to know "how to install Jenkins from scratch." You need to know "how to add a new pipeline to the existing Jenkins."

## 10. Quick self-check

1. Why is Jenkins dominant in regulated finance?
2. What's the GitLab Ultimate equivalent for GHAS in security coverage?
3. Why might a team end up with all three CI platforms?
4. What's the Composite Action equivalent in GitLab?
5. What does "CI/CD Components" replace in GitLab?

(Answers: self-hostable + air-gap-capable + plugin ecosystem + 20-year track record; GitLab Ultimate scanners (SAST + DAST + SCA + Secret + Container + License + API) all included; legacy on Jenkins, new microservices on Actions because GitHub-native, all-in-one team chooses GitLab; CI/CD Component or `include:` block; CI Templates from the pre-17.0 era.)
