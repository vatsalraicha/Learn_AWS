# 22 — Marketplace actions, expressions, contexts, conditionals

> *"`${{ ... }}` is the templating language inside YAML. Pin every marketplace action by SHA. These two habits separate the safe Sr Lead from the one who'll cause an incident."*

## Why this module exists

Every `uses: org/action@ref` is a supply-chain dependency. Most engineers pick `@v3` or `@main` for convenience. At a bank, that's a vulnerability. This module covers (a) how to use marketplace actions safely, (b) the `${{ ... }}` expression language, and (c) the context catalog (`github`, `env`, `secrets`, `inputs`, `needs`, `steps`).

---

## 1. The marketplace

[github.com/marketplace?type=actions](https://github.com/marketplace?type=actions) has tens of thousands of actions. Most useful categories:

- **Official actions** (`actions/*`): checkout, setup-python, setup-node, cache, upload-artifact, download-artifact, etc. Trust high.
- **GitHub-published**: `github/codeql-action`, `github/super-linter`, `github/issue-labeler`. Trust high.
- **Big-vendor**: `aws-actions/*` (AWS), `azure/*`, `google-github-actions/*` (Google), `docker/*`. Trust high.
- **Community popular**: `peaceiris/actions-gh-pages`, `softprops/action-gh-release`, `crazy-max/ghaction-import-gpg`. Trust medium; pin by SHA.
- **Random**: everything else. Trust low; read the source and pin by SHA.

---

## 2. Versioning — pin by SHA in production

Every action is a Git ref. You can reference:

```yaml
uses: actions/checkout@v6                                         # major tag (moves on minor/patch releases)
uses: actions/checkout@v6.1.0                                     # exact version tag
uses: actions/checkout@8459bc0c7e3759cdf591f513d9f141a95fef0a8f   # SHA (immutable)
uses: actions/checkout@main                                       # branch (RUN-TIME mutable — never use)
```

**For internal CI**: `@vN` major tag is acceptable if you trust the maintainer.
**For prod-deploy workflows**: pin by SHA. An attacker who compromises a maintainer can push a malicious `v3` retag that gets picked up by every consumer; SHA pins survive that.

```yaml
# Production pattern — pin by SHA, comment with version for readability
- uses: actions/checkout@8459bc0c7e3759cdf591f513d9f141a95fef0a8f # v6.1.0
- uses: aws-actions/configure-aws-credentials@e3dd6a429d7300a6a4c196c26e071d42e0343502 # v4.0.2
```

**Dependabot supports Actions** — enable it (`.github/dependabot.yml` with `package-ecosystem: github-actions`) and Dependabot auto-bumps SHA pins, raising PRs with the diff and changelog.

Per the GHAS 2026 Security Roadmap, first-time-contributor PRs that include unverified actions get auto-flagged for maintainer review.

---

## 3. The expression syntax

`${{ <expression> }}` — evaluated when the line is read. Can appear:

- In `if:` conditions
- In `with:`, `env:`, `inputs:` values
- In `name:`
- In strings within `run:` blocks (substituted before shell sees them)

```yaml
- run: echo "Branch: ${{ github.ref_name }}"
- if: ${{ github.event_name == 'pull_request' && contains(github.event.pull_request.labels.*.name, 'deploy') }}
  name: "Deploy preview for ${{ github.event.pull_request.head.sha }}"
  with:
    environment: ${{ inputs.environment }}
```

### Operators

| Type | Example |
|---|---|
| Comparison | `==`, `!=`, `>`, `<`, `>=`, `<=` |
| Logical | `&&`, `\|\|`, `!` |
| Grouping | `( ... )` |
| Index | `array[0]`, `object.key`, `object['key']` |
| Wildcard | `array.*.name` (extract `.name` from every element) |

### Functions (built-in)

```yaml
contains(github.event.head_commit.message, '[skip ci]')
startsWith(github.ref, 'refs/tags/v')
endsWith(github.ref, '-rc1')
format('Deploying v{0} to {1}', inputs.version, inputs.environment)
join(github.event.pull_request.requested_reviewers.*.login, ', ')
toJSON(matrix)
fromJSON('["a", "b", "c"]')
hashFiles('**/uv.lock', '**/pyproject.toml')      # SHA-256 of matched files (cache keys)
success()    failure()    always()    cancelled()
```

`hashFiles()` is the killer for cache keys — see [module 25](25_actions_cache_artifacts_matrix.md).

---

## 4. The context catalog

Every expression has access to these contexts:

| Context | Description |
|---|---|
| `github.*` | Event metadata, refs, actor, repo |
| `env.*` | Workflow/job/step environment variables |
| `secrets.*` | Repo/org/environment secrets |
| `vars.*` | Repo/org/environment variables (non-secret) |
| `inputs.*` | `workflow_dispatch` inputs or `workflow_call` inputs |
| `needs.*` | Output values from upstream jobs (those listed in `needs:`) |
| `steps.*` | Output values from previous steps in same job (use `id:` to reference) |
| `matrix.*` | Current matrix combination's values |
| `strategy.*` | Strategy metadata (job-index, max-parallel) |
| `runner.*` | Runner's OS, arch, name, tool cache path |
| `jobs.*` | Job context (only available in reusable workflow callers' `with:`) |

### Example: chaining steps' outputs

```yaml
- id: lint
  run: |
    OUTPUT=$(ruff check src --output-format=json)
    echo "errors=$(echo $OUTPUT | jq length)" >> $GITHUB_OUTPUT

- name: Fail if lint errors > 0
  if: steps.lint.outputs.errors != '0'
  run: |
    echo "Lint errors: ${{ steps.lint.outputs.errors }}"
    exit 1
```

### Example: cross-job output

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.ver.outputs.version }}
    steps:
      - id: ver
        run: echo "version=$(python -c 'import my_pkg; print(my_pkg.__version__)')" >> $GITHUB_OUTPUT

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying ${{ needs.build.outputs.version }}"
```

---

## 5. The `runner` context

```yaml
- run: echo "Running on ${{ runner.os }} ${{ runner.arch }}"
- run: cp data ${{ runner.temp }}/staging/
- run: cache-restore ${{ runner.tool_cache }}/python/3.11.5/x64
```

| `runner.x` | Value |
|---|---|
| `runner.os` | `Linux`, `Windows`, `macOS` |
| `runner.arch` | `X86`, `X64`, `ARM`, `ARM64` |
| `runner.name` | The runner's name (specific machine) |
| `runner.temp` | Path to a fresh temp dir, wiped between jobs |
| `runner.tool_cache` | Path where setup-* actions cache tools (Python, Node, etc.) |
| `runner.debug` | `1` if `ACTIONS_RUNNER_DEBUG=true` set, else empty |

---

## 6. The `github.event.*` deep

For each event type, `github.event` mirrors the webhook payload. Use it to access event-specific data.

`pull_request` event:
```yaml
- run: |
    echo "PR #${{ github.event.pull_request.number }}"
    echo "From: ${{ github.event.pull_request.head.ref }} (${{ github.event.pull_request.head.sha }})"
    echo "Into: ${{ github.event.pull_request.base.ref }}"
    echo "Author: ${{ github.event.pull_request.user.login }}"
    echo "Draft: ${{ github.event.pull_request.draft }}"
    echo "Labels: ${{ join(github.event.pull_request.labels.*.name, ', ') }}"
```

`push` event:
```yaml
- run: |
    echo "Commit: ${{ github.event.head_commit.id }}"
    echo "Message: ${{ github.event.head_commit.message }}"
    echo "Author: ${{ github.event.head_commit.author.email }}"
```

`workflow_dispatch`:
```yaml
- run: echo "Environment: ${{ inputs.environment }}"   # `inputs.*`, not `github.event.inputs.*`
```

`repository_dispatch`:
```yaml
- run: echo "Payload: ${{ toJSON(github.event.client_payload) }}"
```

Full payload schemas → [docs.github.com/webhooks-and-events/webhooks/webhook-events-and-payloads](https://docs.github.com/webhooks-and-events/webhooks/webhook-events-and-payloads).

---

## 7. Conditional patterns

### Skip whole job

```yaml
jobs:
  deploy:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
```

### Run only on labeled PR

```yaml
jobs:
  big-build:
    if: contains(github.event.pull_request.labels.*.name, 'full-build')
```

### Run only when specific paths changed (path filter at event-trigger level)

```yaml
on:
  push:
    paths: ['src/**']      # event-level filter — workflow doesn't even start otherwise
```

### Run only on tags

```yaml
on:
  push:
    tags: ['v*.*.*']
```

### Run on PR ONLY if not a draft

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]   # excluded `draft` events

jobs:
  test:
    if: github.event.pull_request.draft == false
```

### Different steps for different OS

```yaml
- name: Linux setup
  if: runner.os == 'Linux'
  run: sudo apt-get install -y libfoo-dev
- name: macOS setup
  if: runner.os == 'macOS'
  run: brew install libfoo
```

---

## 8. Common pitfalls

### Misusing `${{ secrets.* }}` in `if:`

```yaml
# ❌ Doesn't work — `if:` requires that secrets be present for `pull_request` from forks (they're not)
if: secrets.AWS_ROLE != ''

# ✅ Use a separate gating variable or check env presence at runtime
```

### String comparison case sensitivity

```yaml
if: github.ref_name == 'Main'    # ❌ won't match 'main'
if: github.ref_name == 'main'    # ✅
```

### Quoting in `run:`

```yaml
# ❌ The shell sees ${{ ... }} after substitution. Special chars in PR titles can break the shell.
- run: echo "Title: ${{ github.event.pull_request.title }}"

# ✅ Pass through env to avoid shell injection
- run: echo "Title: $TITLE"
  env:
    TITLE: ${{ github.event.pull_request.title }}
```

The `env:`-passthrough pattern is the standard mitigation for the "script injection via PR title" class of CVEs. Every linter (zizmor, actionlint) flags `${{ }}` substituted into `run:` blocks for review.

### Using `==` for boolean-typed inputs

```yaml
inputs:
  dry_run:
    type: boolean

# ❌ inputs are stringified
if: inputs.dry_run == true
if: inputs.dry_run == 'true'         # ✅
if: ${{ inputs.dry_run }}            # ✅ best — directly use the boolean
```

### Missing `${{ }}` in `if:` legacy syntax

```yaml
if: ${{ github.event_name == 'push' }}      # always works
if: github.event_name == 'push'              # also works in `if:` only — single deviation from rule
```

The `if:` field is unique — `${{ }}` is OPTIONAL there. Everywhere else, it's required.

---

## 9. Linting workflows

Catch problems before pushing:

```bash
# actionlint — fastest, static analysis
brew install actionlint
actionlint .github/workflows/*.yml

# zizmor — security-focused (CVE patterns)
pip install zizmor
zizmor .github/workflows/

# yamllint for YAML structure
yamllint .github/workflows/
```

Add to pre-commit (see [module 40](40_precommit_reproducibility_refactor.md)) so every commit catches issues. CodeQL also has GitHub Actions queries that run automatically with default code scanning setup.

---

## 10. Cross-references

- Caching with `hashFiles()` keys → [module 25](25_actions_cache_artifacts_matrix.md).
- Cross-job outputs + `needs:` → [module 24](24_actions_outputs_needs_concurrency.md).
- Secrets vs variables → [module 23](23_actions_vars_secrets_env.md).
- Pinning actions by SHA + Dependabot for actions → [module 34](34_ghas_dependabot.md).
- Pull-request-target safety + injection mitigations → [module 30](30_actions_environments_protection.md).
