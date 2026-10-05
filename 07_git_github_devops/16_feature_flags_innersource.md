# 16 — Feature flags, release branching, InnerSource

> *"Feature flags decouple deploy from release. InnerSource decouples ownership from contribution. Both are how a regulated bank ships fast without losing its mind."*

## Why this module exists

Trunk-based development is impossible without **feature flags** — you can't ship unfinished code to prod without a way to disable it for users. InnerSource is what makes the singular-pipeline pattern work at a 7,000-engineer bank — code is open across the org, anyone can contribute, ownership routes via CODEOWNERS. This module covers both, plus a brief on release branching when you do need it.

---

## 1. Feature flags — the primitive

A feature flag is a runtime conditional:

```python
if feature_flag.is_enabled("new-token-cache", user=current_user):
    return new_token_cache_logic()
else:
    return legacy_token_logic()
```

The flag's state is read from a **flag service** (LaunchDarkly, Unleash, AWS AppConfig, GrowthBook, OpenFeature-backed self-hosted) at runtime. Changes take effect within seconds, no redeploy.

### What flags enable

- **Decouple deploy from release** — ship code Monday with flag OFF; flip flag ON Friday during business hours when on-call is fresh.
- **Gradual rollout** — turn on for 1% of users, then 10%, then 100%. Catch issues with limited blast radius.
- **A/B testing** — randomly assign half of users to feature A, half to feature B; measure outcome metric.
- **Targeting** — turn on only for `users in beta_group` or `internal employees` or `region=us-east-1`.
- **Kill switch** — instant disable if something breaks (faster than rolling back a deploy).
- **Long-lived "experiment" flags** vs short-lived "release toggle" flags vs "ops toggle" (kill switches) — different lifecycles.

### The four flag types (Pete Hodgson taxonomy)

| Type | Purpose | Lifetime | Stakeholders |
|---|---|---|---|
| **Release toggle** | Hide unfinished feature | Days–weeks | Dev team |
| **Experiment toggle** | A/B test | Weeks | Product team |
| **Ops toggle** | Kill switch for ops | Long-term | SRE |
| **Permission toggle** | Beta-only / internal-only | Long-term | Product team |

### Flag debt

Flags rot. Every flag is a code branch — over time you accumulate dead code behind unused flags. Discipline:
- Set an expiration date on each flag.
- Use a linter (e.g., flag-service SDKs surface "stale flag" warnings).
- Schedule a quarterly cleanup PR series — delete the flag check + the dead branch + the flag service config.

Capital One's published model: feature flags are first-class infrastructure with a flag-management service team. Engineers register flags in a catalog with owner + expected sunset date.

---

## 2. Flag-service options

| Tool | Hosted | Self-host | Open source | Best for |
|---|---|---|---|---|
| **LaunchDarkly** | ✅ | ❌ | ❌ | Enterprise SaaS — the default at most banks |
| **Unleash** | ✅ | ✅ | ✅ | Self-hosted with OSS option |
| **GrowthBook** | ✅ | ✅ | ✅ | A/B testing + flags combined |
| **AWS AppConfig** | ✅ | ❌ | ❌ | AWS-native; integrated with Lambda, ECS, EKS |
| **Flagsmith** | ✅ | ✅ | ✅ | Mid-market |
| **OpenFeature** | — (it's a SPEC) | ✅ via any provider | ✅ | The CNCF abstraction — vendor-neutral SDK |

For Capital One: probably **LaunchDarkly** or **AWS AppConfig** depending on team. The OpenFeature standard means SDK code is portable — you can swap the provider without rewriting code.

---

## 3. Release branching — when you actually need it

Trunk-based + tags handles ~90% of cases. The 10% where release branches earn their keep:

### Pattern A: Long-lived versions in parallel

```
main ──●─●─●─●─●─●─●─●─●─●─●─●──   (HEAD; v3 development)
        │
        v2.x ●─●─●─●─●─●─●  (still supported for old customers, security patches only)
        │
        v1.x ●─●  (EOL — no more changes)
```

You actively maintain `release/v2.x` and `release/v1.x`. Critical fixes are PRs to main, then cherry-picked back to v2 (and v1 if applicable).

Use when: B2B customers with version-pinned contracts, OS distributions, libraries with SemVer guarantees, runtime engines.

### Pattern B: Stabilization branch for a major release

```
main ──●─●─●─●─●─●─●─●─●─●─●──
                  │
                  release/3.0 ●─●─●  (only bugfixes; eventually merged to main + tagged v3.0.0)
```

A short-lived (days–weeks) branch where the engineering team stops new features and just fixes bugs for a quality bar. Merged back, tagged, then deleted.

Use when: discrete major releases with PR/marketing tied to a release date.

### Pattern C: Hotfix branches

When something is broken in prod but main has unreleased work that you don't want to ship together:

```
main ──●─●─●─●─●─●  (has features A, B, C; not ready to release)
        │
        v1.4-hotfix ●  (cherry-pick the urgent fix; tag v1.4.1; deploy)
```

Cherry-pick the fix from main to the branch (or fix directly on the branch and cherry-pick back to main).

This is rare in trunk-based + feature-flags world — usually you'd just merge the fix to main and the unfinished features stay flag-off. But occasionally the fix conflicts with unreleased work, and you need the branch.

---

## 4. InnerSource — the model

**InnerSource = open-source practices applied inside an organization.** Code in a company-internal repo is visible (read access) across the whole org. Anyone can fork, branch, PR. Ownership is via CODEOWNERS.

### Why Capital One bet on it

- **Scale**: 7,000 engineers. You can't have every team rebuild the same auth library, telemetry wrapper, deploy pipeline. InnerSource → one canonical library, many contributors.
- **Knowledge sharing**: senior engineers on team A can drop a fix into team B's repo without bureaucracy.
- **Code consistency**: shared patterns spread because they're literally the same code.
- **Bus factor**: ownership doesn't die when a team disbands; CODEOWNERS routes to whoever's now responsible.

### The principles

1. **Discoverability** — central search index, repo metadata, topics, README badges showing maturity.
2. **Open contribution** — anyone in the org can read; anyone can fork + PR.
3. **Curated ownership** — CODEOWNERS routes PRs to the people who must approve.
4. **Trusted committers** — long-term contributors gain write access; outsiders contribute via PR.
5. **Single source of truth** — no internal forks that diverge; the canonical repo is THE repo.

### The Capital One pattern

From their published [Building a Singular Software Delivery Pipeline](https://www.capitalone.com/tech/open-source/innersource-singular-software-delivery-pipeline/) post:

- One central pipeline repo (Jenkins shared library + GitHub Actions reusable workflows).
- Every team's `Jenkinsfile` is a few lines that `@Library` the central one.
- Contributions to the central pipeline come from any team via PR; CODEOWNERS routes review to the platform team.
- Per-team customizations via parameters, not forks.

### Maturity model (loose)

Many orgs use a 3-tier maturity for InnerSource projects:

- **🌱 Seed** — single-team owned, others can read; PRs welcome but no SLA.
- **🌿 Growing** — multi-team contributions, some external committers, CONTRIBUTING.md exists, PRs reviewed in <1 wk.
- **🌳 Mature** — many contributors, CODEOWNERS richly populated, ADRs maintained, dedicated maintainer team, PR SLA <1 day.

Badge it in your README. Tells contributors what to expect.

---

## 5. Where InnerSource is right vs wrong

✅ **Right for**:
- Shared libraries (auth, logging, telemetry, retry policies)
- Platform tooling (CI templates, IaC modules, deploy scripts)
- Domain models that many services consume
- Documentation sites
- ML model training utilities

❌ **Wrong for**:
- Highly sensitive code that only specific teams should see (fraud, financial models — these need restricted org access)
- Vendor code (just package it)
- Code that's truly one team's concern with no cross-team consumers

The boundary is: *does another team benefit from being able to read, learn from, or contribute to this code?* If yes → InnerSource it. If no → keep it team-scoped.

---

## 6. Feature flags + InnerSource together

The combination unlocks the Capital One operational model:

1. **Engineer on team A** wants to contribute to **team B's auth library** to fix a bug they hit.
2. They fork team B's repo, branch, fix, open PR.
3. Their PR includes a **feature flag** for any behavior change ("if `auth.use-new-validation` is on, use new logic; else legacy").
4. CODEOWNERS routes the PR to `@team-b/auth`.
5. Team B approves + merges. Code is live in prod within hours, flag-off.
6. Team B turns the flag on for their own service first (1% → 10% → 100%), then announces to other consumers.
7. Other teams enable the flag at their own pace.
8. Eventually team B cleans up the flag (months later, after all consumers migrated).

No coordinated release. No "code freeze." No "wait for the platform team." Many engineers contributing safely to shared code.

---

## 7. Cross-references

- The branch-protection rules that make trunk-based safe → [module 11](11_branch_protection_rulesets_codeowners.md).
- Reusable workflows as the GitHub Actions equivalent of Jenkins shared libraries → [module 26](26_actions_reusable_workflows.md).
- The Capital One Jenkins shared-library pattern → [module 50](50_jenkins_multibranch_shared_libs.md).
- Champion/challenger ML deployment as feature flags applied to models → [module 44](44_mlops_champion_challenger.md).
