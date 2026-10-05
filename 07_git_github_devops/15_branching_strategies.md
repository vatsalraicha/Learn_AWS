# 15 — ⭐ Git Flow vs GitHub Flow vs Trunk-based development

> *"Capital One ships ~50,000 build/test/deploy actions a day on trunk-based development with feature flags. There's a reason that's the published DORA pattern."*

## Why this module exists

Every team I've worked with has had a strong opinion on branching. Most opinions don't survive contact with scale. This module covers the three canonical strategies, why trunk-based has won at high-performing orgs (Capital One, Google, Meta, Netflix), and where Git Flow still makes sense (almost nowhere — but you should know when).

---

## 1. The three canonical strategies

| | Git Flow (2010) | GitHub Flow (2011) | Trunk-based development |
|---|---|---|---|
| Long-lived branches | `main`, `develop`, `release/*`, `hotfix/*` | `main` only | `main` only |
| Feature branches | Yes (off `develop`) | Yes (off `main`), short | Tiny (<1 day) or none |
| Where releases come from | `release/x.y` branch → tagged | `main` (every merge can deploy) | `main` (every merge SHOULD deploy) |
| Hotfix path | `hotfix/*` branch off `main` | Quick PR to `main` | Same: quick PR to `main` |
| Deploy decoupled from merge? | Yes (releases are explicit) | No (merge = deploy) | Yes (via feature flags) |
| Best for | Versioned products with parallel releases (libraries, OS distros) | Simple SaaS, small teams | Continuous delivery at scale |

---

## 2. Git Flow — the original

Vincent Driessen's 2010 model. The DAG looks like:

```
master ────────●────────●────────●──── (production releases tagged here)
                \      / \      /
release/1.x      ●────●   ●────●  (final QA + version bump)
                  \  /     \  /
develop ──────●────●●●──●───●●──── (integration branch)
              /\  /         \
feature/x ──●──● /           (feature work)
feature/y ─────●              

hotfix/* ──── (off master, urgent fixes, merged back to master AND develop)
```

**Five branch types**:
- `master` — production-only, every commit is tagged release
- `develop` — integration branch where features land
- `feature/*` — work happens here, branched off `develop`
- `release/*` — pre-release stabilization, branched off `develop`, merged to both `master` AND `develop`
- `hotfix/*` — emergency fix on `master`, merged to both

**Where it works**: shipping versioned software with multiple supported versions in parallel. Linux distros, Android OS, language runtimes, libraries with LTS lines.

**Where it doesn't**: web apps, microservices, anything continuously deployed. The overhead of `develop` + `release/*` + merge-back-into-develop is pure tax. Driessen himself acknowledged in 2020 that Git Flow is not suitable for continuous delivery.

---

## 3. GitHub Flow — the simplification

A 2011 post from Scott Chacon describing GitHub's own model. Five rules:

1. `main` is always deployable.
2. Branch off `main` for new work.
3. Push and open a PR early.
4. Review + discuss in the PR.
5. Merge to `main` → deploy.

The whole strategy fits on a postcard. Just `main` + short feature branches.

**Where it works**: small-to-mid teams, SaaS apps, web services with simple release cadence (every merge ships).

**Where it doesn't**: when you need release versioning (libraries), when "merge = deploy" is too risky (regulated finance — you want a separation between code-merge and customer-impacting release).

---

## 4. Trunk-based development (TBD) — the high-performing pattern

DORA-blessed; Capital One published; Google's internal model; what every "elite-performing" DevOps team in DORA's report does.

**Core rules**:

1. Everyone commits to `main` (the trunk).
2. Branches are SHORT — <1 day, ideally hours.
3. Many small commits, several times per day per engineer.
4. **Deploy is decoupled from merge** via **feature flags** — unfinished features ship to prod behind off-by-default flags.
5. CI is continuous and fast (<10 min ideally).
6. Branch protection blocks broken commits from landing.
7. Releases are tags on `main` (or every merge is a release in pure CD).

```
main ──●─●─●─●─●─●─●─●─●─●─●─●─●─●──
        \   \   \   \   \   \
         f1  f2  f3  f4  f5  f6     (each feature branch lives <1 day)
```

### Why TBD wins

- **Smaller PRs** → easier review → faster merge → faster feedback.
- **No long-lived integration pain** — main IS the integration point.
- **Trunk is always green** — branch protection makes it impossible for it not to be.
- **DORA's 4 metrics improve together** — deploy frequency up, lead time down, change failure rate down (smaller batches = less blast radius), MTTR down (revert one small PR vs unrolling a megabranch).
- **Feature flags decouple deploy from release** — ship code Monday, enable feature Friday, roll back via flag toggle in 10 seconds.

### Why TBD looks scary at first

- "But what if a feature isn't done?" → Feature flag, off by default.
- "But what if it breaks main?" → Branch protection + required CI = it can't.
- "But what about hotfixes?" → Same path: small PR to main, deploy.
- "But how do we version releases?" → Tag main; semantic-release auto-versions from Conventional Commits (see [module 19](19_templates_adr_docs_conventional_commits.md)).
- "But we need a QA gate" → That's the staging environment in the deploy pipeline, not a branch.

---

## 5. Variants and hybrids

Most real teams aren't pure. Common hybrids:

### "Trunk-based with release tags"

```
main ──●─●─●─●─●─●─●─●─●─●─●─●─●──
                       │             │
                       v1.4.0        v1.5.0     (annotated tags, no branches)
```

Every deploy creates a tag for traceability. No `release/*` branch. Hotfixes are PRs to main, tagged as `v1.5.1`. This is Capital One's default.

### "Trunk-based with short-lived release branches"

```
main ──●─●─●─●─●─●─●─●─●─●─●─●──
        │           │
        v1.4-branch v1.5-branch  (short-lived, for very late-stage hotfix only)
```

Used when you have two long-supported customer versions in parallel. Common in B2B SaaS with version-pinned customers.

### "GitHub Flow + environments"

```
main ──●─●─●─●─●─●─●─●─●─●──
       │   deploy to dev (auto)
       │       deploy to staging (auto on next merge)
       │           deploy to prod (manual approval gate)
```

The "merge = deploy" of GitHub Flow softened by GitHub Environments + manual approval gates (see [module 30](30_actions_environments_protection.md)). Capital One pattern but with a Jenkins promote-through-envs job rather than Actions.

---

## 6. Where Git Flow is still right

Honest case for Git Flow:

- **You ship installable software** with semantic versions customers consume (e.g., a Python package on PyPI, a Helm chart, a Linux package).
- **You support multiple major versions** in parallel for compliance reasons (v2.x for old customers, v3.x for new).
- **You have a meaningful QA cycle** before release that doesn't fit in continuous CI.

If none of those apply, you don't need Git Flow.

---

## 7. The DORA metrics evidence

DORA's annual State of DevOps report consistently shows: high-performing teams use trunk-based development. The 2025 report (4,867 respondents, restructured into 7 team profiles instead of elite/high/medium/low):

- Teams with TBD + feature flags ship multiple times per day.
- Teams with long-lived feature branches (Git Flow) ship weekly or less.
- Change-failure rate is **lower** for high-frequency deployers (smaller batches = less risk per change).

Capital One specifically: reported 20× release frequency improvement when they moved from long-lived branches to trunk-based.

---

## 8. The migration path (long-lived → trunk-based)

You inherit a codebase using Git Flow. Migration steps:

1. **Get CI fast and reliable.** TBD requires <10 min CI. If yours is 30 min, fix that first.
2. **Set up feature flags infrastructure.** LaunchDarkly, Unleash, OpenFeature, or homegrown. Without flags, TBD = breaking prod.
3. **Make `develop` an alias for `main`.** Settings → Branches → Default branch → `main`. Delete `develop`.
4. **Shorten feature branch lifetime.** Set a team norm: "if your branch is >2 days old, you've gone wrong."
5. **Enforce branch protection on main.** Required CI checks, required PR review, required signed commits.
6. **Release on tag.** Adopt `release-please` to auto-tag on merges containing Conventional Commits.
7. **Watch DORA metrics improve.** Deploy frequency goes up, lead time comes down. Mean to PR-to-merge becomes the bottleneck.

Expect 3–6 months for an established team to internalize the pattern.

---

## 9. The Sr Lead lens

The question you'll be asked: *"What branching strategy would you recommend?"*

The good answer:

> "Trunk-based with feature flags. It's what Capital One has published, it's what DORA consistently shows correlates with high performance, and it aligns with the InnerSource model where many teams contribute to shared repos — long-lived branches don't survive 50 PRs/day to a repo. The exceptions are libraries that need parallel-version support, where I'd add short-lived release branches off of main."

The bad answer:

> "Git Flow, because we need a develop branch for integration testing." (Conflates branch strategy with environment strategy — environments belong in the deploy pipeline, not in branches.)

---

## 10. Cross-references

- Feature flags + InnerSource → [module 16](16_feature_flags_innersource.md).
- Branch protection that makes trunk-based safe → [module 11](11_branch_protection_rulesets_codeowners.md).
- Environments + deployment gates → [module 30](30_actions_environments_protection.md).
- Conventional Commits + release-please for automated tagging → [module 19](19_templates_adr_docs_conventional_commits.md).
