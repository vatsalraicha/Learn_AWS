# 27 — ⭐ Composite + custom actions (JS, Docker)

> *"Reusable workflows package whole pipelines. Composite actions package step sequences. Custom actions implement new primitives. You'll write composites; you'll rarely write JS/Docker actions."*

## Why this module exists

The other three reuse mechanisms in GitHub Actions:
- **Composite actions** — reuse a sequence of steps inside a job.
- **JavaScript actions** — TypeScript/JS code running on the runner.
- **Docker actions** — a container with an entrypoint.

This module covers all three, with a focus on composite actions (the 90% case).

---

## 1. Composite action — the shape

A composite action lives in a repo at `action.yml` (in the repo root) or in a subdirectory like `.github/actions/my-action/action.yml`.

```yaml
# .github/actions/setup-python-ml/action.yml
name: "Setup Python ML environment"
description: "Install Python, uv, project deps, with caching"
inputs:
  python-version:
    description: "Python version"
    required: false
    default: "3.11"
  install-extras:
    description: "Optional extras to install (comma-separated)"
    required: false
    default: "dev"
  working-directory:
    description: "Working directory"
    required: false
    default: "."

outputs:
  python-path:
    description: "Path to the Python executable"
    value: ${{ steps.setup.outputs.python-path }}

runs:
  using: composite
  steps:
    - id: setup
      uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}

    - name: Install uv
      shell: bash
      run: pip install uv

    - name: Cache deps
      uses: actions/cache@v4
      with:
        path: |
          ~/.cache/uv
          ${{ inputs.working-directory }}/.venv
        key: uv-${{ runner.os }}-${{ inputs.python-version }}-${{ hashFiles(format('{0}/uv.lock', inputs.working-directory)) }}

    - name: Install deps
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: |
        EXTRAS=""
        IFS=',' read -ra EXTRA_LIST <<< "${{ inputs.install-extras }}"
        for e in "${EXTRA_LIST[@]}"; do EXTRAS="$EXTRAS --extra $e"; done
        uv sync $EXTRAS
```

Use it:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: ./.github/actions/setup-python-ml          # local action — relative path
        with:
          python-version: "3.12"
          install-extras: "dev,train"
      - run: uv run pytest
```

Or from another repo:

```yaml
- uses: capitalone/actions-org/setup-python-ml@v2
  with:
    python-version: "3.12"
```

---

## 2. Composite action rules

- Every `run:` step **MUST** specify `shell:` (no default).
- Steps in composite actions can't directly access secrets (caller must pass via inputs).
- Composite actions don't have their own `runs-on:` — they inherit from the calling job.
- Can call other composite actions (no formal nesting limit but practical limit applies).
- Cannot call reusable workflows.
- Can use `if:` on steps (since 2023).

---

## 3. JavaScript actions

For custom logic that needs real programming (not shell), JS actions are the lightweight option. They run directly on the runner (Node.js 20+).

Structure:

```
my-js-action/
├── action.yml
├── package.json
├── src/
│   └── index.ts
├── dist/                     ← bundled output (checked into repo!)
│   └── index.js
└── tsconfig.json
```

`action.yml`:

```yaml
name: "My JS Action"
description: "Does a thing"
inputs:
  greeting:
    required: true
    default: "Hello"
outputs:
  result:
    description: "The greeting + name"
runs:
  using: node20
  main: dist/index.js
```

`src/index.ts`:

```typescript
import * as core from '@actions/core';
import * as github from '@actions/github';

async function run() {
  try {
    const greeting = core.getInput('greeting');
    const actor = github.context.actor;
    const result = `${greeting}, ${actor}!`;
    core.setOutput('result', result);
    core.info(result);
  } catch (err) {
    core.setFailed((err as Error).message);
  }
}

run();
```

Build + publish:

```bash
npm install
npm run build             # esbuild bundles to dist/index.js
git add dist/
git commit -m "build"
git tag v1.0.0
git push --tags
```

**Why bundle to `dist/`**: when consumed via `uses: org/my-js-action@v1`, GitHub clones the action's repo but does NOT install npm deps. The `dist/` directory must be self-contained.

Pattern: use `@vercel/ncc` or `esbuild` to bundle all `node_modules` deps into one `dist/index.js` file. Commit it. Yes, this feels weird; yes, this is the convention.

Use the `@actions/*` toolkit packages:
- `@actions/core` — inputs, outputs, logging, masking
- `@actions/github` — GitHub API client + context
- `@actions/exec` — shell execution
- `@actions/io` — file ops
- `@actions/tool-cache` — tool installer pattern

---

## 4. Docker actions

For actions that need specific OS / tool versions outside what the runner has:

`action.yml`:

```yaml
name: "My Docker Action"
description: "Runs a thing in a container"
inputs:
  config:
    required: true
runs:
  using: docker
  image: Dockerfile
  args:
    - ${{ inputs.config }}
```

`Dockerfile`:

```dockerfile
FROM python:3.11-slim
COPY entrypoint.sh /entrypoint.sh
COPY src/ /app/
RUN pip install -r /app/requirements.txt
ENTRYPOINT ["/entrypoint.sh"]
```

`entrypoint.sh` receives args from `action.yml`.

**Pros**: full control over environment. Hermetic.
**Cons**: slower (image build/pull every run unless you publish to GHCR), only runs on Linux runners, can't access most host context.

For published Docker actions, pre-build the image and reference it:

```yaml
runs:
  using: docker
  image: docker://ghcr.io/myorg/my-action:v1.2.3
```

---

## 5. Action.yml metadata fields

Every action has:

```yaml
name: "Display Name"                       # required
description: "What it does"                 # required
author: "Vatsal"                            # optional
branding:                                   # for marketplace
  icon: "package"
  color: "blue"
inputs:
  foo:
    description: "..."
    required: true
    default: "value"
    deprecationMessage: "Use bar instead"   # for deprecated inputs
outputs:
  result:
    description: "..."
    value: ${{ steps.x.outputs.y }}         # composite only — JS/Docker actions set via tools
runs:
  using: composite | node20 | docker
  steps: [...]                              # composite
  main: dist/index.js                       # JS
  image: Dockerfile                         # Docker
  pre: dist/pre.js                          # JS only — run before main
  post: dist/post.js                        # JS only — run after main (even on failure)
```

`pre:` and `post:` are useful for setup/cleanup actions (e.g., the `actions/cache` action uses `post:` to save the cache after the job completes).

---

## 6. When to write which

| Need | Use |
|---|---|
| Reuse 3+ steps across jobs/workflows | Composite action |
| Reuse a whole job/pipeline | Reusable workflow |
| Add a marketplace-quality action with logic | JS action |
| Need specific OS/CUDA/toolchain | Docker action |
| Tiny one-liner | Just `run:` |

For internal Capital One actions, composite covers 90%. The other 10% — JS for things like "post a custom check status via API" or "compute a complex matrix."

---

## 7. The internal-actions repo pattern

```
capitalone/actions-org/
├── setup-python-ml/
│   └── action.yml                # composite
├── deploy-sagemaker/
│   └── action.yml                # composite
├── post-status-check/
│   ├── action.yml                # JS
│   ├── src/index.ts
│   └── dist/index.js
├── jira-link/
│   └── action.yml                # JS
└── compliance-scanner/
    ├── action.yml                # Docker
    └── Dockerfile
```

Reference from any consumer:

```yaml
- uses: capitalone/actions-org/setup-python-ml@v2
- uses: capitalone/actions-org/deploy-sagemaker@v3
  with:
    endpoint-name: ${{ vars.PROD_ENDPOINT }}
- uses: capitalone/actions-org/post-status-check@v1
  with:
    name: "model-validation"
    status: "success"
```

Each action tagged independently. Bump as needed. Dependabot can auto-PR upgrades (per-action `dependabot.yml` config).

---

## 8. Local testing of actions

Composite actions: invoke via `act`:

```bash
act -W .github/workflows/ci.yml --container-architecture linux/amd64
```

JS actions: standard Node testing with `vitest`/`jest`. Use `@actions/core` mocks:

```typescript
import * as core from '@actions/core';
vi.mock('@actions/core');

test('greets the actor', () => {
  vi.mocked(core.getInput).mockReturnValue('Hello');
  // ... invoke action's main
  expect(core.setOutput).toHaveBeenCalledWith('result', 'Hello, vraicha!');
});
```

Docker actions: `docker build .` + `docker run` with mock args.

---

## 9. Versioning + tagging conventions

For internal actions, follow the marketplace conventions:

- Tag `v1.0.0`, `v1.1.0`, `v2.0.0`
- Force-update major-version tags (`v1`, `v2`) to point at latest minor in that line
- Document breaking changes in CHANGELOG

```bash
git tag v1.2.3 -m "v1.2.3"
git tag -d v1 && git tag v1 -m "v1 → v1.2.3" && git push --force origin v1
git push origin v1.2.3
```

Consumers pin `@v1` for "follow the latest v1.x" or `@v1.2.3` for exact.

---

## 10. Cross-references

- Reusable workflows (the job-level reuse) → [module 26](26_actions_reusable_workflows.md).
- Pinning marketplace actions by SHA → [module 22](22_actions_marketplace_expressions.md).
- The `@actions/toolkit` package set — [actions/toolkit](https://github.com/actions/toolkit).
- Capital One internal actions pattern → [module 56](56_capital_one_devops_deep.md).
