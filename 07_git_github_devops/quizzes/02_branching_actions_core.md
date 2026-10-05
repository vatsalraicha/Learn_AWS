# Quiz 02 — Branching strategies + Repo architecture + Actions core (Parts C–E)

Covers modules 15–25.

---

## Section 1 — Branching strategies + repo architecture (modules 15–19)

1. **What's the canonical answer when asked "which branching strategy would you recommend?"**
   <details><summary>Answer</summary>Trunk-based with feature flags. DORA's elite-performer pattern; Capital One's published case study (20× release frequency improvement). Exception: libraries needing parallel-version support, where short-lived release branches off main make sense.</details>

2. **What's the role of feature flags in trunk-based development?**
   <details><summary>Answer</summary>Decouple deploy from release. Unfinished features ship to prod behind off-by-default flags. Critical for shipping incrementally without breaking users.</details>

3. **When does a monorepo pay back?**
   <details><summary>Answer</summary>When multiple packages have heavy code sharing + frequent cross-cutting changes, AND you can invest in build tooling (Bazel, Nx, Pants, Turborepo). Without the tooling investment, monorepos collapse under their own weight (slow CI, merge conflicts).</details>

4. **What's `src/` layout vs flat layout for Python projects?**
   <details><summary>Answer</summary>`src/` layout puts the package inside `src/my_pkg/`; flat puts it at the root. PyPA recommends `src/` layout — prevents accidental imports from project root before install, forces you to test the installed version.</details>

5. **What does release-please do?**
   <details><summary>Answer</summary>Parses Conventional Commits to auto-generate CHANGELOG + version bumps. Creates a "Release PR" with the version bump + changelog. Merge the Release PR → release-please tags + creates GitHub Release. No manual version bumping.</details>

6. **What are the standard Conventional Commits types that trigger version bumps?**
   <details><summary>Answer</summary>`feat:` = MINOR. `fix:` = PATCH. `BREAKING CHANGE:` (or `feat!:`) = MAJOR. Others (docs, style, refactor, perf, test, build, ci, chore) don't bump version (by default config).</details>

---

## Section 2 — Actions workflow syntax (modules 20–22)

7. **What's the difference between `pull_request` and `pull_request_target` events?**
   <details><summary>Answer</summary>`pull_request` runs in the PR's fork context — NO secrets available, GITHUB_TOKEN is read-only. `pull_request_target` runs in the BASE repo's context — has secrets and write tokens. **`pull_request_target` is dangerous** if you `checkout` the PR's code and run it. Only use for auto-labeling, comments — things that don't execute PR-author code.</details>

8. **Why pin marketplace actions by SHA in production?**
   <details><summary>Answer</summary>Tags can be moved (an attacker compromising a maintainer can push a malicious `v3` retag). SHAs are immutable. Dependabot can auto-PR SHA bumps with diff visibility. For internal CI, `@v3` is acceptable; for prod-deploy, pin by SHA.</details>

9. **Why use `env:` passthrough instead of `${{ ... }}` directly in `run:` blocks?**
   <details><summary>Answer</summary>Prevents shell injection. User-controllable strings (PR title, branch name, commit message) substituted directly into shell are RCE vectors. Pass via env vars; shell metacharacters in the value are literal text. Linters (zizmor, actionlint) flag this pattern.</details>

10. **What's `concurrency` in GitHub Actions for?**
    <details><summary>Answer</summary>Groups runs by a key; can cancel in-progress runs when new ones start. Pattern for PR CI: `group: ci-${{ github.head_ref || github.ref }}` + `cancel-in-progress: true`. Saves 80% of CI minutes on busy repos by cancelling duplicate runs.</details>

---

## Section 3 — Variables, secrets, env (modules 23–25)

11. **What's the resolution order for secrets/variables?**
    <details><summary>Answer</summary>Environment-scoped → repository-scoped → organization-scoped. Most specific wins.</details>

12. **What's the 2026 default for `GITHUB_TOKEN` permissions on new repos?**
    <details><summary>Answer</summary>Read-only across all scopes. Per the Actions 2026 Security Roadmap. You must explicitly grant write permissions via `permissions:` block where needed.</details>

13. **What `permissions:` value is required for OIDC to AWS?**
    <details><summary>Answer</summary>`id-token: write` — required to request the OIDC JWT from GitHub's identity provider.</details>

14. **What's the artifact retention default + how do you change it?**
    <details><summary>Answer</summary>Default is 90 days. Configurable 1–400 days at org/repo level. Per-artifact override: `actions/upload-artifact@v4` with `retention-days: 14`.</details>

15. **What's a dynamic matrix from a job output?**
    <details><summary>Answer</summary>A job produces a JSON output describing matrix combinations; downstream job uses `fromJSON()` to set its matrix. Use case: discover which services changed in a monorepo PR, build a matrix of just those for testing.</details>

16. **What's the matrix max combinations limit?**
    <details><summary>Answer</summary>256 jobs per matrix per workflow run (hard limit). Use `include`/`exclude` to add/remove specific combinations.</details>

17. **What's the difference between `actions/cache` and `actions/setup-python` cache option?**
    <details><summary>Answer</summary>`setup-python` cache is a shortcut that caches `~/.cache/pip` keyed on `pyproject.toml`/`requirements.txt` hashes. `actions/cache` is the generic primitive (any path, any key). Prefer setup-* cache options when available; fall back to actions/cache for custom needs.</details>

18. **What does `hashFiles()` do?**
    <details><summary>Answer</summary>Returns SHA-256 of matched files (glob patterns). Used in cache keys to invalidate cache when those files change. Example: `key: pip-${{ hashFiles('**/uv.lock', '**/pyproject.toml') }}`.</details>

19. **What's `::add-mask::` for?**
    <details><summary>Answer</summary>Workflow command that tells the runner to mask a value in logs. Use for values derived at runtime that should be treated as secrets. Example: `echo "::add-mask::$DERIVED_TOKEN"`.</details>

20. **What does `if: failure()` mean and how does it differ from `if: always()`?**
    <details><summary>Answer</summary>`failure()` = true if any prior step failed (skipped on success or cancel). `always()` = true regardless of prior outcomes (runs on success, failure, AND cancel). Use `failure()` for "on error" cleanup; `always()` for "always run" cleanup.</details>
