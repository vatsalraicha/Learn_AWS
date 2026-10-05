# 17 — Monorepo vs polyrepo trade-offs

> *"Both can work. Most teams default to whichever they're used to. The senior call is to pick deliberately and accept the tax."*

## Why this module exists

The mono-vs-poly question is one of the more contested decisions in 2026 engineering, and it tends to be reopened every time a team scales. Both work; both have failure modes; both come with specific tooling debt. This module gives you the honest comparison so you can defend either side in an interview and pick the right one for the actual situation.

---

## 1. Definitions

- **Monorepo**: one Git repo holding many projects/services/packages. Bazel-built or Nx-built or Pants-built. Atomic cross-project commits. Examples: Google internal, Meta, Microsoft Office, Twitter, Pinterest.
- **Polyrepo (a.k.a. multirepo)**: one Git repo per project/service/library. Cross-service changes = coordinated PRs. Examples: Netflix, most startups, most banks.
- **Manyrepos** (informal): polyrepo taken to extreme — every microservice its own repo, dozens of repos per team.

Most real orgs are **hybrid**: a few monorepos for platform code + many polyrepos for individual services.

---

## 2. The honest trade-off table

| Dimension | Monorepo | Polyrepo |
|---|---|---|
| **Code sharing** | Direct import — instant | Publish package → consumer bumps version |
| **Atomic cross-cutting refactor** | One PR | N coordinated PRs |
| **Dependency unification** | One lockfile, one version | Each repo independently versioned (drift inevitable) |
| **PR cycle time** | Higher variance; can be slower due to large CI graph | Lower; per-repo CI |
| **CI/CD tooling cost** | High — needs incremental build (Bazel, Nx, Pants, Turborepo) | Low — every repo is independent |
| **Git performance** | Bad at scale unless using sparse checkout / partial clone / scalar | Always fine |
| **Search / discovery** | Easy — grep the whole org | Hard — need code-search tool |
| **Team independence** | Lower — your CI shares infrastructure with everyone | Higher — your repo is your kingdom |
| **Access control** | Coarse — repo-level only | Fine-grained — different teams can have different repos |
| **Onboarding** | Clone one repo, you have everything | Need to know which repos to clone |
| **Open-sourcing a component** | Hard (must extract) | Easy (already separate) |
| **Trunk-based at scale** | Yes if tooling is invested in | Yes naturally |
| **Best size** | Either tiny (<10 packages) or huge (100s of packages, dedicated platform team) | Anywhere in between |

The Faros 2024 study of 320 scrum teams: median PR cycle time was 19 hours in monorepos vs 2 hours in polyrepos. But monorepos showed greater variance — well-tooled ones were faster than polyrepos; poorly-tooled ones were 10× slower. **Monorepos pay back when you invest in the tooling.**

---

## 3. When to pick which

### Pick a **monorepo** when:

- Multiple packages have **heavy code sharing** and **frequent cross-cutting changes**.
- You can afford to invest in build tooling (Bazel, Pants, Nx, Turborepo, Buck2).
- You want a single source of truth for shared types/protos/APIs.
- You're a tiny project (<10 packages) where polyrepo overhead exceeds monorepo overhead.
- You want atomic version-locking across all packages.

### Pick a **polyrepo** when:

- Services are owned by different teams with different release cadences.
- You truly have no shared code (or it's distributed via package registry).
- Different repos need different access controls (e.g., one has PII handlers, another doesn't).
- Per-repo CI is sufficient and the per-repo tooling cost is acceptable.
- You want each repo to evolve independently without coordinating with others.

### Pick a **hybrid** when (the most common):

- Platform code (shared libraries, IaC modules, design tokens) → monorepo.
- Business services (each a separately deployed app) → polyrepo, one per service.

This is what Capital One's published pattern implies — the InnerSource shared libraries (Jenkins shared library, Cloud Custodian policies) are in central repos; per-team services are in their own repos.

---

## 4. The monorepo tooling tax

A monorepo at scale REQUIRES:

- **Incremental build** — only rebuild what changed. Bazel, Pants, Nx, Turborepo, Buck2 all solve this. Without it, every commit rebuilds the world.
- **Sparse checkout / partial clone** (Git 2.27+) — engineers check out only the part of the repo they work on. Critical at huge scale.
- **Code-owners-aware CI** — only run tests/build for changed packages + their reverse dependencies. Without this, CI takes hours.
- **Selective deploys** — when commit X touches only service Y, only deploy service Y. Requires deploy tooling that knows the repo graph.
- **Bot maintenance** — Renovate or Dependabot configs that handle the whole repo's dependencies.
- **Trunk-based** — long-lived branches in a monorepo become merge-hell within days.

Without the tooling, monorepos collapse under their own weight. Pants/Bazel/Nx have steep learning curves; budget months of platform-engineering investment.

---

## 5. The polyrepo tax

- **Cross-service refactors are hard** — typing change in shared types library requires N PRs across N consumers, in the right order.
- **Dependency drift** — every repo independently picks framework versions; quarterly "fleet update" sprints needed.
- **Code search is hard** — need a code-search tool (Sourcegraph, OpenGrok, GitHub code search) or you literally can't find things.
- **Onboarding documentation must explain the repo map** — new engineers won't know what to clone.
- **Per-repo CI/CD config drift** — repo A's GitHub Actions config differs from repo B's; bug fixes don't propagate. Mitigation: reusable workflows + composite actions (see [module 26](26_actions_reusable_workflows.md)).
- **Per-repo CODEOWNERS, branch protection, security settings drift** — mitigation: org-level Rulesets + Terraform-managed repos.

---

## 6. The ML lens

For ML specifically:

| | Monorepo | Polyrepo |
|---|---|---|
| Shared utilities (data loaders, model utils) | Easy direct import | Publish as internal package |
| Notebook code | One `notebooks/` dir for everyone | Per-team `notebooks/` |
| Training pipelines | One `pipelines/` dir | Per-team |
| Model registry artifacts | Out of repo regardless (MLflow, SageMaker Registry) | Same |
| Per-team experimentation freedom | Lower — shared CI may slow you down | Higher |
| Reproducibility across teams | Easier (one lockfile) | Harder (drift) |

ML teams often start polyrepo (one team, one repo). At scale, the "shared utils" repo becomes pseudo-monorepo. Watch for: shared ML library → many service consumers → coordination pain → push toward monorepo for the platform.

Capital One pattern: shared ML platform code in central repos (likely InnerSource); per-team production ML services in their own repos.

---

## 7. The wrong reason to pick monorepo

> "Google does it." — Google has 50+ engineers on the build-system team. You don't.

> "Everything in one place is convenient." — Until your CI takes 90 min and a flaky test blocks 200 PRs simultaneously.

> "It'll force us to share code." — It won't. People will still write duplicative code in different parts of the monorepo. Sharing requires team norms, not just colocation.

## 8. The wrong reason to pick polyrepo

> "Microservices means microrepos." — Microservices are about runtime decomposition. Repo decomposition is independent.

> "Independent deploys means independent repos." — A monorepo with per-package CD pipelines is perfectly fine.

> "We want each team to own their stack." — Polyrepo enables this but doesn't require it; monorepo can enforce it via CODEOWNERS.

---

## 9. The 2026 wrinkle — AI-assisted dev

AI coding assistants (Copilot, Claude Code, Cursor) change the calculation slightly:

- **Polyrepo benefit reduced**: AI can hold context for many small files across repos via codebase indexing. The "you can't find anything" tax is smaller.
- **Monorepo benefit enhanced**: AI in a monorepo sees the whole graph and can suggest cross-package refactors safely.
- **But**: agents working in polyrepos with proper APIs are often safer than agents in monorepos with sprawling cross-dependencies.

Net effect: small. Pick on the traditional criteria.

---

## 10. The senior answer

In an interview:

> "It depends on the org's investment in build tooling and the cross-cutting change rate. For a 5-person startup with 3 services, polyrepo is right. For a 1000-engineer company with hundreds of shared libraries and frequent platform refactors, monorepo with Bazel/Pants pays back. For Capital One scale, hybrid: InnerSource platform repos as central shared monorepos (Jenkins library, CI templates), service repos as polyrepo. The mistake to avoid is picking monorepo without budgeting for the build-system team — that's the path to 90-min CI and miserable engineers."

---

## 11. Cross-references

- Python ML repo structure (within whichever model) → [module 18](18_python_ml_repo_structure.md).
- Reusable workflows as the polyrepo-CI-drift mitigation → [module 26](26_actions_reusable_workflows.md).
- Sparse checkout for monorepos → [module 03](03_core_workflows.md).
- Capital One's InnerSource shared-library pattern → [module 16](16_feature_flags_innersource.md) + [module 50](50_jenkins_multibranch_shared_libs.md).
