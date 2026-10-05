# 25 — Caching, artifacts, matrix builds, debugging

> *"Caching cuts CI time in half. Matrix multiplies your test surface. Artifacts pass files between jobs. Debugging in CI is its own skill."*

## Why this module exists

Three speed + breadth mechanics + one survival skill — every CI/CD engineer needs them sharp.

---

## 1. Caching — `actions/cache`

Store/restore directories between workflow runs.

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache/pip
      ~/.cache/uv
    key: pip-${{ runner.os }}-${{ hashFiles('**/pyproject.toml', '**/uv.lock') }}
    restore-keys: |
      pip-${{ runner.os }}-
```

How it works:
- On a cache **miss** (no entry matches `key`), step proceeds without restoring; at job end, the runner saves the `path` contents under `key`.
- On a cache **hit** (key matches exactly), step restores the data and saves it back at job end (idempotent).
- On a **partial** match (no exact key but `restore-keys` prefix matches), restores the most-recent matching cache; saves new cache under `key` at job end.

Cache size limit: 10 GB per repo (oldest evicted). Caches expire after 7 days of no access.

### Setup-action caching shortcut

Many setup-* actions have built-in cache support:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
    cache: pip                             # caches ~/.cache/pip keyed on pyproject.toml hash
    cache-dependency-path: |
      **/pyproject.toml
      **/uv.lock

- uses: actions/setup-node@v4
  with:
    node-version: "22"
    cache: npm
    cache-dependency-path: "**/package-lock.json"
```

Use these instead of manual `actions/cache` when available — simpler and tested.

### Cache keys + invalidation

The cache key must change when the cached content should be invalidated.

```yaml
# Good: changes when deps change
key: pip-${{ hashFiles('**/pyproject.toml', '**/uv.lock') }}

# Bad: cache never invalidates
key: pip

# Good: per-OS, per-deps
key: pip-${{ runner.os }}-${{ hashFiles('**/uv.lock') }}

# Good: with fallback for partial match
key: pip-${{ runner.os }}-${{ hashFiles('**/uv.lock') }}
restore-keys: |
  pip-${{ runner.os }}-
```

### What to cache (Python ML)

```yaml
path: |
  ~/.cache/pip
  ~/.cache/uv
  ~/.cache/huggingface       # HF model downloads
  ~/.cache/torch             # Torch model downloads
  ~/.cache/pre-commit
  ~/.local/share/virtualenvs
  /home/runner/.venv          # if using project-local venv
```

**Don't cache** node_modules in isolation (use `actions/setup-node` with cache) — the dependency resolution result is implicit in `package-lock.json`.

---

## 2. Artifacts

Cross-**job** file passing (caches are per-key, not per-job). Artifacts persist after the workflow completes for the configured retention period.

```yaml
# In job A — upload
- uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: dist/
    retention-days: 14
    if-no-files-found: error            # fail if path is empty (default: warn)
    compression-level: 6                # default 6; 0=no compression, 9=max

# In job B — download (must have job A in `needs:`)
- uses: actions/download-artifact@v4
  with:
    name: build-output
    path: ./dist                        # where to extract
```

Defaults:
- **Retention**: 90 days (configurable 1–400 days at org/repo).
- **Max size per artifact**: 10 GB.
- **Max total artifacts per workflow run**: 500 GB.

v4 vs v3: v4 is **immutable per name** (can't re-upload same name in same run); has merge support; runs much faster. Always use v4.

To pass between **steps** in the same job, just use the filesystem. No artifact needed.

### Download all artifacts

```yaml
- uses: actions/download-artifact@v4
  with:
    path: ./artifacts                    # creates ./artifacts/<artifact-name>/<files>
    pattern: 'build-*'                   # only matching pattern
    merge-multiple: true                 # flatten into one dir instead of subdirs
```

### Artifact retention strategy

- **CI artifacts** (junit, coverage): 14 days. Visible in PR + used by reviewer.
- **Build artifacts** (wheels, binaries): 90 days. May be needed for hotfix rebuilds.
- **Release artifacts**: copy to S3 / GitHub Release for permanent retention. Don't rely on Actions artifact retention beyond 90 days.

---

## 3. Matrix builds

Run one job's steps N times across different parameter combinations.

```yaml
jobs:
  test:
    strategy:
      matrix:
        python: ["3.11", "3.12", "3.13"]
        os: [ubuntu-latest, macos-latest]
        # → 6 combinations
      fail-fast: false                  # don't cancel other matrix jobs if one fails
      max-parallel: 4                    # cap concurrent matrix jobs
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python }}" }
      - run: pip install -e ".[dev]"
      - run: pytest
```

`fail-fast: true` (default) cancels remaining matrix jobs when one fails. Set to `false` when you want to see all failures (debugging compatibility).

### `include` and `exclude`

Add specific combinations:

```yaml
matrix:
  python: ["3.11", "3.12"]
  os: [ubuntu-latest, macos-latest]
  include:
    - python: "3.13"
      os: ubuntu-latest
      experimental: true                 # extra value, only available in this combo
  exclude:
    - python: "3.11"
      os: macos-latest                   # don't test this combo
```

`include` adds combinations; `exclude` removes. `include` entries can have extra keys (`experimental`) accessible via `matrix.experimental`.

### Dynamic matrix from job output

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.gen.outputs.matrix }}
    steps:
      - id: gen
        run: |
          MATRIX=$(jq -nc '{python: ["3.11","3.12"], os: ["ubuntu-latest","macos-latest"]}')
          echo "matrix=$MATRIX" >> $GITHUB_OUTPUT

  test:
    needs: setup
    strategy:
      matrix: ${{ fromJSON(needs.setup.outputs.matrix) }}
    runs-on: ${{ matrix.os }}
    steps: ...
```

Use case: discover which services changed in a monorepo PR, build a matrix of those to test.

### Matrix limits

- **256 jobs per matrix per workflow run** (hard limit).
- **20 inputs in matrix** (combined `include`/`exclude` axes).

---

## 4. Debugging workflows

### Enable debug logging

Set repository secrets:
- `ACTIONS_RUNNER_DEBUG = true` — runner internal logs
- `ACTIONS_STEP_DEBUG = true` — step-level debug logs (shows what the action is doing internally)

Or **re-run with debug logging** button in the Actions UI (re-runs a failed run with both flags on).

### Add debug output

```yaml
- name: Debug environment
  if: runner.debug == '1'                # only when debug logging enabled
  run: |
    env | sort
    pwd
    ls -la
```

### `tmate` for interactive debugging

The nuclear option — pause a workflow and SSH into the runner:

```yaml
- name: Setup tmate session
  if: failure() && runner.debug == '1'
  uses: mxschmitt/action-tmate@v3
  timeout-minutes: 15
```

When the step runs, it prints an SSH command in the log. SSH in, poke around, type `touch /tmp/done` to release the runner.

Be careful: tmate exposes a public SSH endpoint. Don't enable in workflows with prod secrets.

### Local workflow testing — `act`

Run workflows locally via `act`:

```bash
brew install act
act push                                # run workflows triggered by push
act pull_request
act -j test                             # run specific job
act --dry-run                           # show what would run
act -W .github/workflows/ci.yml
```

`act` runs jobs in Docker (uses runner images). Not 100% identical to GitHub-hosted runners but catches 80% of bugs in seconds.

Useful for: testing new workflows, iterating on YAML changes without push-CI-fail-push cycles.

Limitations: doesn't perfectly emulate `secrets`, `environments`, OIDC, some marketplace actions. Use for syntax + flow, fall back to real CI for end-to-end.

### `gh run` inspection

```bash
gh run list --limit 5
gh run view 1234567890
gh run view --job 9876543210 --log
gh run view 1234567890 --log-failed         # just failed steps
gh run watch 1234567890                      # live tail
gh run rerun 1234567890 --failed             # re-run only failed jobs
gh run cancel 1234567890
gh run download 1234567890 -n my-artifact   # download an artifact locally
```

### Workflow commands (`echo "::..."`)

Special log markers the runner interprets:

```yaml
- run: |
    echo "::group::Loading deps"
    pip install -e ".[dev]"
    echo "::endgroup::"

    echo "::warning file=src/app.py,line=42,col=10::Deprecated function called"
    echo "::error file=src/app.py,line=50::Missing test"

    echo "::notice title=Build summary::Built 1.2.3"

    echo "::add-mask::$SECRET_VALUE"

    echo "::set-output name=key::value"     # DEPRECATED — use $GITHUB_OUTPUT
    echo "key=value" >> $GITHUB_OUTPUT       # the modern way
```

`::group::` / `::endgroup::` make log sections collapsible — huge readability win.

`::warning::` / `::error::` / `::notice::` annotations appear inline in the PR diff view if you use `file=`, `line=`, `col=`. CodeQL, ESLint, pytest, etc. produce these natively.

---

## 5. The job summary

Each job can have a markdown summary that appears in the run UI:

```yaml
- name: Generate summary
  run: |
    echo "## Test Results" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "| Test | Status |" >> $GITHUB_STEP_SUMMARY
    echo "|------|--------|" >> $GITHUB_STEP_SUMMARY
    echo "| unit | ✅ |" >> $GITHUB_STEP_SUMMARY
    echo "| integration | ❌ |" >> $GITHUB_STEP_SUMMARY
```

Rendered at the top of the job's run page. Great for high-density status without scrolling through logs.

---

## 6. Cross-references

- Outputs/needs (the orchestration primitives) → [module 24](24_actions_outputs_needs_concurrency.md).
- Cost optimization (concurrency, runner sizing) → [module 31](31_actions_token_cost_templates.md).
- Reusable workflows (apply this pattern across many repos) → [module 26](26_actions_reusable_workflows.md).
- Self-hosted GPU runners for ML matrix builds → [module 28](28_actions_self_hosted_arc_gpu.md).
