# 33 — 🏦 CodeQL + custom queries + SARIF + Copilot Autofix

> *"CodeQL turns your code into a queryable database. The default queries catch the OWASP Top 10. Custom queries catch your bank-specific anti-patterns."*

## Why this module exists

CodeQL is GitHub's static-analysis engine, included in GitHub Code Security ($30/active committer/mo). It's the deepest SAST in the ecosystem because it actually represents your code as a typed graph and lets you query data flows. This module covers the operational view (default + advanced setup), Copilot Autofix (the now-default fixer), and custom query patterns.

---

## 1. What CodeQL does

CodeQL builds a **database** from your source code — an AST + symbol table + dataflow graph. You then run **queries** (written in QL, a logic-programming language) against the database to find patterns: SQL injection, XSS, hardcoded secrets, unsafe deserialization, race conditions, …

GitHub ships **standard query packs** covering the OWASP Top 10 + per-language idioms. You can also write custom queries for your codebase's specific anti-patterns.

Supported languages (2026): C/C++, C#, Go, Java/Kotlin, JavaScript/TypeScript, Python, Ruby, Swift, **GitHub Actions workflows**.

---

## 2. Default setup vs Advanced setup

### Default setup (the easy path)

Settings → Code security → Code scanning → Set up → **Default**.

GitHub auto-detects languages, schedules code scanning on push to default branch + on every PR + weekly cron. No workflow file written by you. Uses the default query suite.

Pros: zero config. Cons: no customization (matrix, schedule, query selection).

### Advanced setup (the production path)

Settings → Code security → Code scanning → Set up → **Advanced** → commits a workflow file:

```yaml
# .github/workflows/codeql.yml
name: CodeQL

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    timeout-minutes: 360
    permissions:
      actions: read
      contents: read
      security-events: write
    strategy:
      fail-fast: false
      matrix:
        include:
          - language: python
          - language: actions

    steps:
      - uses: actions/checkout@v6

      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-and-quality                  # or 'security-extended', 'security-and-quality'
          # config-file: ./.github/codeql/codeql-config.yml

      - uses: github/codeql-action/autobuild@v3           # tries to autobuild compiled langs

      - uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
          # upload: failure-only   # only upload SARIF if something found
```

Query suites:
- `security-extended` (default) — security findings
- `security-and-quality` (recommended) — security + code quality findings
- Custom suites via `.github/codeql/codeql-config.yml`

---

## 3. Configuration file

`.github/codeql/codeql-config.yml`:

```yaml
name: "Capital One ML CodeQL config"

queries:
  - uses: security-and-quality
  - uses: ./.github/codeql/custom-queries/sql-builder.ql   # custom query in this repo

paths:
  - src/
  - lambdas/
paths-ignore:
  - tests/
  - notebooks/
  - vendor/

disable-default-queries: false     # keep defaults + add yours

# Per-language settings
python:
  setup-python-dependencies: true   # install requirements.txt for better analysis
```

---

## 4. Copilot Autofix

Since August 2024, Copilot Autofix is **GA and enabled by default** when CodeQL runs. It uses an LLM to propose fixes for the alerts CodeQL surfaces. The fix appears as a suggestion in the PR — one click to commit.

Workflow:
1. PR opens; CodeQL runs.
2. CodeQL finds, say, an SQL injection alert.
3. Copilot Autofix analyzes the surrounding code + suggests a parameterized-query fix.
4. PR review UI shows the fix as a code suggestion.
5. Reviewer (or author) clicks "Commit suggestion" → fix lands.

You can disable autofix per repo if your policy requires manual remediation. For Capital One: most likely enabled (faster MTTR for vulnerabilities) but with mandatory human review of every applied fix.

---

## 5. SARIF — the integration format

SARIF (Static Analysis Results Interchange Format) is the standard JSON format for SAST tool output.

```json
{
  "version": "2.1.0",
  "runs": [{
    "tool": { "driver": { "name": "MyTool", "version": "1.0" } },
    "results": [{
      "ruleId": "PY001",
      "level": "warning",
      "message": { "text": "Possible SQL injection" },
      "locations": [{
        "physicalLocation": {
          "artifactLocation": { "uri": "src/db.py" },
          "region": { "startLine": 42 }
        }
      }]
    }]
  }]
}
```

GitHub accepts SARIF uploads from any third-party SAST tool:

```yaml
- uses: snyk/actions/python@master
  with:
    args: --sarif-file-output=snyk.sarif
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: snyk.sarif
    category: snyk
```

Results appear alongside CodeQL findings in the Security tab. Use this to integrate `bandit`, `semgrep`, `snyk`, `trivy`, `safety`, etc.

---

## 6. Custom CodeQL queries

QL is a logic-programming language. The structure of a query:

```ql
/**
 * @name Hardcoded internal API token
 * @description Detects hardcoded C1-style API tokens in source.
 * @kind problem
 * @problem.severity error
 * @id capitalone/hardcoded-c1-api-token
 * @tags security
 */

import python

from StrConst s
where s.getText().regexpMatch("c1_api_[A-Za-z0-9]{32}")
select s, "Hardcoded C1 API token found."
```

Run locally:

```bash
# Install CodeQL CLI
brew install codeql

# Create a database for your code
codeql database create my-db --language=python --source-root=.

# Run a query
codeql database analyze my-db ./capitalone-queries.qlpack --format=sarif-latest --output=results.sarif

# Run a single query file
codeql query run ./.github/codeql/custom-queries/sql-builder.ql --database my-db
```

Pack your queries into a **QL pack** (`qlpack.yml`) that can be referenced from `codeql-config.yml`. Distribute via GitHub Container Registry as an OCI artifact.

For Capital One: a central QL pack with bank-specific patterns (forbidden APIs, internal naming-convention violations, regulated-data handling rules), referenced from every repo's CodeQL config.

---

## 7. Reading + triaging alerts

GitHub UI: repo Security tab → Code scanning alerts. For each:
- Severity (critical / high / medium / low / note)
- Tool (CodeQL or imported SARIF source)
- Rule ID + description
- Location (file + line)
- Status (open / fixed / dismissed)

Dismissal reasons:
- False positive (with note)
- Won't fix (with note)
- Used in tests (with note)

Capital One pattern: dismissals require security-team approval (custom workflow: GH App that requires `@security-team` label before allowing dismissal).

---

## 8. Pre-merge enforcement

To block PR merges with new alerts:

1. Branch protection → require `CodeQL` status check.
2. Per 2026, CodeQL has a "Code scanning alerts must be resolved" rule in repository security settings — newly introduced alerts block merge until addressed.
3. Org Rulesets can require code scanning across all repos.

For bank: required CodeQL status check on `main` + critical alerts block merge.

---

## 9. The third-party SAST landscape

| Tool | Languages | Open source | Best for |
|---|---|---|---|
| **CodeQL** | 10+ | Free (GHAS-licensed) | Deep dataflow analysis; the gold standard |
| **semgrep** | 30+ | Yes (community + paid) | Fast, easy custom rules, broad coverage |
| **bandit** | Python | Yes | Python-specific; security linter |
| **Snyk Code** | Many | No (paid) | Commercial; good ecosystem integration |
| **Sonarqube** | Many | OSS + paid | Code quality + security |
| **trivy** | IaC, container, secrets, deps | Yes | Container + IaC focus |

Use CodeQL as the foundation; layer semgrep for fast custom-rule iteration; layer trivy for container/IaC. Upload everyone's SARIF to GitHub for unified triage.

---

## 10. Cross-references

- The dependency-side scanning (Dependabot) → [module 34](34_ghas_dependabot.md).
- SBOM + supply chain → [module 35](35_ghas_sbom_slsa_attestations.md).
- Secret scanning → [module 32](32_ghas_secret_scanning.md).
- Required status checks in branch protection → [module 11](11_branch_protection_rulesets_codeowners.md).
- Pre-commit ML stack (local pre-CI checks) → [module 40](40_precommit_reproducibility_refactor.md).
