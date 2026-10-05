# 53 — ⭐ GitHub Copilot (IDE, Chat, PR review, `gh copilot`)

> *"Copilot is the most-deployed AI dev tool in industry. The 2026 question isn't whether to use it; it's how to use it responsibly at a bank."*

## Why this module exists

GitHub Copilot ships with three primary surfaces — inline completion in your IDE, Chat (sidebar conversation), and PR-review agent. Plus the `gh copilot` CLI extension. Plus, since June 2026, usage-based billing changes the cost calculus. This module covers all surfaces + the bank-grade governance lens.

---

## 1. The plans

| Plan | Price | What |
|---|---|---|
| **Free** | $0 | Limited completions + chat for individuals |
| **Pro** | $10/user/mo | Unlimited completions; Chat |
| **Pro+** | $39/user/mo | + Claude/GPT-5 access; more advanced reasoning |
| **Business** | $19/user/mo | Pro + content exclusion, IP indemnity, admin controls, audit logs |
| **Enterprise** | $39/user/mo | Business + codebase indexing, custom fine-tuned models, Copilot in github.com chat, custom knowledge bases |

Capital One: certainly Business or Enterprise.

**Big change June 1, 2026**: usage-based billing via "AI Credits." Every plan includes a monthly credit allotment; paid plans can buy more. Token consumption (input + output + cached) metered per model. **Code completions + Next Edit Suggestions remain free of credits** (always-on autocomplete is unmetered).

---

## 2. Inline completion (IDE)

The primary surface. Type code; Copilot suggests next lines.

```python
# You type:
def calculate_tax(

# Copilot suggests:
def calculate_tax(amount: float, rate: float = 0.08) -> float:
    """Calculate the tax on a given amount."""
    return amount * rate
```

Accept with Tab; reject by continuing to type.

**Quality**: highly dependent on context. Copilot reads the surrounding file + open files in tabs (and, in Enterprise, the indexed codebase). Better naming + better existing code → better suggestions.

**Disabling**: per-file via comment (`// copilot:disable-next-line`), per-extension setting, or just close it.

---

## 3. Copilot Chat

Sidebar chat in VS Code, JetBrains, Visual Studio. Reference code with `@workspace`, `@file`, `@symbol`. Ask questions, request refactors, generate tests.

Useful patterns:
- `@workspace why does the tax calculation not handle negative amounts?`
- `@workspace generate unit tests for src/tax.py covering edge cases`
- `/explain` — explain selected code
- `/fix` — propose a fix for selected code
- `/tests` — generate tests
- `/doc` — generate docstring

Enterprise tier adds:
- Codebase indexing → `@workspace` understands the whole repo (or org)
- Knowledge bases → `@knowledge` references your internal docs
- Models: choose Claude 4.7, GPT-5, etc.

---

## 4. Copilot in github.com (Enterprise)

A Chat sidebar embedded in github.com — answers questions about issues, PRs, discussions across your org. Index of your indexed repos.

Useful for: cross-repo "where does X live?" questions, recent activity summaries, PR review assistance.

---

## 5. Copilot PR review (the agent)

A PR-review agent that reads the diff + leaves comments + suggests fixes. As of 2025, GA for Business + Enterprise.

How it works:
1. PR opened or updated.
2. Reviewer assigns "Copilot" as a reviewer (or it auto-runs based on settings).
3. Copilot reads the diff + relevant surrounding code.
4. Posts review comments inline + a summary.
5. Reviewer (human) decides to apply / discuss / dismiss.

Coverage:
- Style + idiomatic improvements
- Potential bugs (null handling, off-by-one)
- Missing tests
- Security concerns (input validation, secret patterns)
- Performance hints

**Cost (since June 1, 2026)**: each Copilot review run consumes Actions minutes on GitHub-hosted runners (the agent runs in a workflow). Watch your Actions usage.

**Pattern at Capital One**: Copilot review as a first-pass; human reviewer still required (CODEOWNERS). Copilot catches the obvious; humans catch the contextual.

---

## 6. Copilot Autofix (security-focused)

A specific Copilot application for CodeQL alerts (since August 2024 GA, enabled by default with code scanning).

When CodeQL surfaces an alert, Copilot Autofix:
1. Reads the alert context + surrounding code
2. Proposes a fix
3. Shows the fix as a code suggestion in the PR

Click "Commit suggestion" → fix lands.

For Capital One: certainly enabled (faster MTTR for vulnerabilities). Probably with mandatory human review of every applied fix.

See [module 33](33_ghas_codeql_autofix.md) for the GHAS side.

---

## 7. `gh copilot` (CLI)

```bash
gh extension install github/gh-copilot

gh copilot suggest "list all running EC2 instances in us-east-1, filter by tag Team=ML"
# Suggests: aws ec2 describe-instances --region us-east-1 --filters "Name=tag:Team,Values=ML" --query 'Reservations[].Instances[?State.Name==`running`]'
# [Run / Copy / Explain / Cancel]

gh copilot explain "find . -mtime -7 -type f -not -path '*/.*'"
# Explains: find files modified in last 7 days, excluding hidden dirs
```

Useful when:
- You forget the exact flag for `aws`/`kubectl`/`docker`/`jq`
- You see a complex command in a script and want to understand it
- You want to combine tools you know separately but not together

Available with Pro+ / Business / Enterprise.

---

## 8. Privacy + IP — what gets sent

Default (Business + Enterprise):
- Code in your IDE is **sent to GitHub's models** for completions.
- Snippets are NOT retained after the request (zero-day retention).
- Your code is NOT used for training (Business + Enterprise).
- Content exclusion: org admin can specify file/folder patterns whose content is NEVER sent.

For Capital One: content exclusion likely configured to skip `secrets/`, `compliance/`, anything PII-sensitive.

**IP indemnity** (Business + Enterprise): GitHub will defend + cover damages if Copilot suggests code that's found to infringe — provided you have the relevant filter enabled (default on).

---

## 9. The Capital One usage pattern (likely)

For a Sr Lead at Capital One:

- **Copilot Enterprise** seat (with codebase indexing for capital-one orgs)
- **Content exclusion** for sensitive paths
- **Custom instructions** at org level (e.g., "use Capital One internal libraries; don't suggest direct AWS SDK calls — use the wrapper")
- **PR review** running on all PRs (first-pass)
- **Autofix** enabled with required human approval
- **CLI** (`gh copilot`) approved for use
- **Audit logs** of Copilot usage flowing to SIEM
- **Quarterly review** of which suggestions ended up in committed code

---

## 10. The Sr Lead's relationship with Copilot

Treat Copilot like a junior pair-programmer:
- Use for: boilerplate, syntax recall, code-review first pass, command suggestions, test generation
- Verify before commit: it's confidently wrong sometimes (hallucinations on package names, made-up API methods)
- Don't accept blindly: read every suggestion before Tab
- Don't ask it for design — it's not a senior

You're paid (and trusted) for judgment. Copilot speeds up the typing, not the thinking.

For governance discussions: be the one who articulates how to roll this out responsibly at Capital One — not the one who claims "AI will replace senior engineers." The Sr Lead frame is "AI augments senior judgment; protect bank-grade trust." See [module 55](55_ai_governance_privacy.md).

---

## 11. Cross-references

- Claude Code in enterprise → [module 54](54_ai_claude_code_enterprise.md).
- Governance for AI dev tools → [module 55](55_ai_governance_privacy.md).
- CodeQL + Copilot Autofix → [module 33](33_ghas_codeql_autofix.md).
- `gh` CLI fundamentals → [module 14](14_gh_cli_fundamentals.md).
