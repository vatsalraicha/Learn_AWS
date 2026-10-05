# 10 — Pull requests, code review, merge strategies

> *"A PR is a change proposal — title, body, diff, conversation, status checks, reviewers, merge button. Every part has a discipline."*

## Why this module exists

The PR is the unit of change at every team running modern Git workflows. At a Sr Lead level you're expected to (a) author PRs that get merged fast with minimal back-and-forth, (b) review PRs with sufficient depth and speed, (c) understand the merge-strategy choice and its implications for history, and (d) wire up PRs into the CI/CD gates that protect prod.

---

## 1. Authoring a good PR

The three things that determine PR merge time:

1. **Size**: small PRs merge fast. Aim for <400 added LOC (excluding generated/lock files). Big refactor? Split into reviewable chunks via a stacked PR series.
2. **Title + body**: title is one line, action-verb start, scope clear. Body answers *what, why, how, validation, risk, rollback*. PR template enforces this — fill it in fully (see [module 08](08_repo_setup_standards.md)).
3. **Green CI**: open the PR with red CI = you've wasted your reviewer's first 5 minutes. Run the lint+test suite locally first (via pre-commit + `make test` or equivalent).

### Stacked PRs (the senior pattern for big changes)

You have a 1500-LOC change. Break it into 3 logical PRs:

```
PR #100  feat: introduce TokenCache class           (base = main)
PR #101  feat: wire TokenCache into AuthService     (base = PR #100's branch)
PR #102  refactor: remove old token logic           (base = PR #101's branch)
```

Reviewers can review #100 first; once merged, you rebase #101 onto main; etc. Tools that help: `git-spice`, `git-branchless`, GitHub CLI extensions like `gh stack`, Graphite. For solo work without tooling, just label them clearly and link PRs in their bodies.

---

## 2. The PR lifecycle

```
Draft (optional)  ─► Open for review  ─► Approved + CI green  ─► Merged
       │                    │                                          │
       ▼                    ▼                                          ▼
  WIP — no               Active                                    Branch deletable
  notifications          reviewers
```

- **Draft PR**: opens but doesn't notify reviewers. Useful when you want CI to run but you're not ready for review. Convert to "Ready for review" when ready.
- **Open**: reviewers notified, status checks run, CODEOWNERS routing triggers.
- **Approved**: at least one approving review + all required checks green.
- **Merged**: branch can auto-delete (Settings → "Automatically delete head branches").

---

## 3. Code review — the etiquette

What a good reviewer does:

- **Reviews within 1 business day** (sometimes faster — the longer a PR sits open, the more it diverges from main).
- **Reads the description before the diff.** "What and why" is context for "how to read this."
- **Notes positive things**, not just problems. Reinforces good patterns.
- **Uses suggestions** (the `🔍 Suggest change` button — produces an inline diff the author can apply with one click) instead of "could you change line 42 to ..." comments.
- **Distinguishes blocking vs nit comments**. Prefix nits as `nit:` so the author knows they can ignore or fix at their discretion.
- **Doesn't litigate style** (formatter + linter should handle that — argue style in the linter config, not on PRs).
- **Approves with confidence** or **requests changes** — avoid the wishy-washy "comments only" if you mean "approve with these fixed."

### Suggestion syntax

In a review comment:
````
\`\`\`suggestion
final_text_replacing_the_selected_lines
\`\`\`
````

Author sees a "Commit suggestion" button. Done.

### Review levels

| Level | Meaning |
|---|---|
| **Comment** | I'm leaving feedback but not blocking | 
| **Approve** | Looks good, ship it |
| **Request changes** | Don't merge until I re-review |

When you "Request changes," GitHub blocks the merge until you (or anyone with permission to dismiss) marks it resolved. Use sparingly — over-using makes reviewers' approvals worth less.

---

## 4. The merge button — three choices

GitHub PRs offer up to three merge strategies (configurable per-repo in Settings → General → "Pull Requests"):

| Strategy | What happens | Best for |
|---|---|---|
| **Merge commit** | Creates a merge commit on main (`Merge pull request #N from branch`). Preserves branch's individual commits in history. | Long-lived branches with meaningful commit-by-commit history (rare in trunk-based) |
| **Squash and merge** | Combines all branch commits into ONE new commit on main. Branch's individual commits disappear from history. | Feature work with messy WIP commits. **Most common at trunk-based shops.** |
| **Rebase and merge** | Replays each branch commit on top of main. Linear history, no merge commit. Each branch commit appears individually on main. | Branches with clean, atomic, well-messaged commits |

Capital One's **trunk-based + small PRs** model usually uses **Squash and merge**. The squash commit message becomes part of permanent history — make it good.

**Per-repo rule of thumb**: pick ONE merge strategy and disable the others. Mixed merge strategies on the same repo produce inconsistent history.

---

## 5. Auto-merge

A PR can be set to **auto-merge** — when all required reviews + status checks pass, GitHub merges automatically.

```bash
gh pr merge 100 --auto --squash
gh pr merge 100 --auto --squash --delete-branch
```

Pre-requisites:
- Repo has auto-merge enabled (Settings → General).
- Branch protection requires status checks and/or reviews.

Pattern: open PR → request reviews → enable auto-merge → walk away. When the last reviewer approves (or last check passes), it merges itself. Saves the "is it merged yet?" loop.

---

## 6. Merge queues (the elite-team pattern)

A **merge queue** (GA 2023) serializes PR merges into main and re-runs CI on the *queued tentative commit* before actually merging. Prevents "semantic merge conflicts" where two PRs each pass CI in isolation but break main when both merge.

How it works:
1. Reviewer approves PR with all checks green.
2. PR is added to the merge queue (button: "Merge when ready").
3. Queue creates a temporary commit applying THIS PR on top of MAIN + any PRs ahead of it in the queue.
4. Re-runs required checks on the temporary commit.
5. If green → fast-forward main to it. If red → kicks the PR out of the queue with explanation.

Enable: Settings → Branches → Branch protection rule → "Require merge queue."

The new `merge_group` event lets your workflow run on the tentative commit too.

```yaml
on:
  pull_request:
  merge_group:    # also run on queue's tentative commits
```

For Capital One at 50k builds/day, merge queues prevent the "main is broken because two PRs landed in the wrong order" pager.

---

## 7. Required reviews + CODEOWNERS

Branch protection settings that matter for PRs:

- **Require pull request reviews before merging** (1+ approvals)
- **Dismiss stale pull request approvals when new commits are pushed** (re-approval needed if PR changes after approval)
- **Require review from Code Owners** (CODEOWNERS-matched files require approval from listed owner)
- **Require approval of the most recent reviewable push** (someone other than the most recent pusher must approve)
- **Require conversation resolution before merging** (all review threads must be marked resolved)

Capital One's typical config: **2 approvals + CODEOWNERS + dismiss stale + require resolution.** Deep dive in [module 11](11_branch_protection_rulesets_codeowners.md).

---

## 8. Status checks

A **status check** is a build/test/scan that reports green or red on a PR's HEAD commit. Branch protection can require specific checks to be green before merge.

Status checks come from:
- **GitHub Actions workflows** triggered by `pull_request`
- **Third-party CI** (Jenkins, CircleCI, etc.) via webhooks or GitHub App
- **GHAS scans** (CodeQL, secret scan, dependency review)
- **Code coverage** services (Codecov, Coveralls)
- **Custom commit statuses** posted via API (e.g., your model-validation gate)

To require a check, add it under Branch protection → Status checks → Require status checks to pass before merging → search and add. **Only checks that have already run on at least one PR can be required** — there's no way to "require check X" before it exists.

---

## 9. PR reviewer assignment

Three mechanisms, in increasing automation:

1. **Manual** — author picks reviewers (or uses `gh pr edit --add-reviewer`).
2. **CODEOWNERS** — required reviewers auto-added based on changed paths.
3. **Team review request with round-robin or load-balanced assignment** — under Org → Teams → settings, configure auto-assignment so a request to team `@org/sre` rotates through team members.

The Sr Lead pattern: CODEOWNERS for required + team round-robin for "anyone on this team is fine" reviews.

---

## 10. PR comments — kinds

- **General comment**: bottom of PR; broad feedback.
- **Inline comment**: on a specific line in the diff.
- **Review thread**: a series of inline comments grouped together — can be marked resolved.
- **Suggestion**: special inline comment that proposes a code change (one-click apply).
- **Single-line code in inline comment**: triple-backticks for syntax highlighting.

Resolved threads: don't unresolve someone else's resolution without good reason. The conversation-resolution requirement in branch protection makes "resolve to dismiss" a moral hazard — discipline it.

---

## 11. Draft PRs as RFCs

A useful pattern: open a draft PR with NO code, just the README/design doc updated, and the body explaining "I'm thinking about doing X this way. Thoughts?" Use as a lightweight RFC. Once consensus, push the code, convert to ready-for-review.

Cheaper than a full ADR for tactical decisions; better than a Slack thread because it ends up in git history.

---

## 12. Cross-references

- The CODEOWNERS + branch protection setup that makes PR review safe → [module 11](11_branch_protection_rulesets_codeowners.md).
- `gh pr` CLI commands (create, view, review, merge) → [module 14](14_gh_cli_fundamentals.md).
- CI status checks (the workflows that produce them) → [module 20](20_actions_workflow_events.md) onward.
- Model-validation gate as a status check → [module 42](42_mlops_validation_gates.md).
