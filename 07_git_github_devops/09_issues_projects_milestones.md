# 09 — Issues, projects, milestones, labels

> *"At a bank, Jira is the system of record. GitHub Issues is the system of conversation. Don't fight that — bridge it."*

## Why this module exists

Most enterprises (Capital One included) have Jira as the canonical ticket system, with GitHub Issues either disabled on internal repos or used for engineering-only discussion (bugs, RFC threads, technical debt). This module covers what GitHub's work-management primitives are and how to use them in a Jira-centric world.

If you're at a smaller shop using GitHub Issues as the canonical tracker, the same primitives apply — just heavier use.

---

## 1. The primitives

| Primitive | What it is | Where it lives |
|---|---|---|
| **Issue** | A unit of work, discussion, or bug. Has title, body, comments. | Per repo |
| **Label** | A tag on an issue/PR. Color-coded. | Per repo |
| **Milestone** | A grouping of issues/PRs with a target date. | Per repo |
| **Assignee** | A person responsible. | Per issue/PR |
| **Project (v2)** | A board/table/roadmap view over issues + PRs from any repo. | Org-wide or per repo |
| **Discussion** | A long-form thread for questions, RFCs, announcements. | Per repo (if enabled) |

---

## 2. Issues — the core

Every issue has:
- **Title** + **body** (markdown)
- **Status**: open / closed (closed can be subdivided as **completed**, **not planned** since 2023)
- **Labels** (zero or many)
- **Assignees** (zero or many, max 10)
- **Milestone** (zero or one)
- **Linked PRs**: close-keyword links (`Closes #123` in PR body) and manual links
- **Comments**

```bash
# Via gh CLI (much faster than UI)
gh issue create --title "Bug: token cache stale on refresh" --body "..." --label "bug,high-priority" --assignee "@me"
gh issue list --label "bug" --state "open"
gh issue view 42
gh issue close 42 --comment "Fixed in #50"
gh issue edit 42 --add-label "needs-triage" --remove-label "bug"
```

---

## 3. Labels — the taxonomy

Sane default labels (GitHub seeds some; customize per org):

| Label | Color | Purpose |
|---|---|---|
| `bug` | red | Defect |
| `feature` | green | New functionality |
| `documentation` | blue | Docs change |
| `good-first-issue` | purple | For newcomers |
| `help-wanted` | green | Maintainer asking for contributions |
| `triage` | gray | Needs maintainer attention |
| `priority/high` | red | SLA-driven |
| `priority/low` | gray | Backlog |
| `type/refactor` | orange | Code quality |
| `area/ml` | yellow | ML subsystem |
| `area/infra` | yellow | Infrastructure |
| `status/in-review` | blue | Currently in PR review |
| `status/blocked` | red | Waiting on external |
| `wontfix` | gray | Closed as not planned |

**Label hygiene patterns**:
- Use `category/value` prefixes (`priority/`, `area/`, `type/`, `status/`) so they group visually.
- One label per category — don't tag `priority/high` AND `priority/medium`.
- Automate label application via PR paths: `actions/labeler` + `.github/labeler.yml`:
  ```yaml
  area/ml:
    - changed-files:
      - any-glob-to-any-file: ['src/models/**', 'src/inference/**']
  area/infra:
    - changed-files:
      - any-glob-to-any-file: ['infra/**', '.github/workflows/**']
  ```

---

## 4. Milestones — date-bound batches

A milestone is "release 1.4" or "Q3 2026 OKR" — a collection of issues with a target date and a percentage-complete bar.

```bash
gh issue list --milestone "v1.4"
gh issue edit 42 --milestone "v1.4"
```

Use them when you actually have date-driven releases. Don't use them as a substitute for sprint planning (that's Projects, or Jira).

---

## 5. Projects (v2) — the new beast

Projects v2 (rolled out 2022, GA 2023) is a **fully customizable spreadsheet/board/roadmap** over issues + PRs. It's the replacement for the legacy "Project boards" (which were Trello-clones, now sunset).

Capabilities:
- Cross-repo (an org-level Project can pull issues from any repo in the org)
- Custom fields: text, number, date, single-select, iteration, multi-select
- Multiple views: Table (spreadsheet), Board (Kanban), Roadmap (Gantt-like)
- Group, filter, sort by any field
- Automation: when issue closed → set Status to Done; when added → set initial Status
- Insights: built-in burn-up/burn-down, status snapshots over time

```bash
# gh CLI supports Projects v2
gh project list --owner @me
gh project create --owner @me --title "Topic-07 Backlog"
gh project item-add 5 --owner @me --url https://github.com/org/repo/issues/42
```

GraphQL is the primary API (REST has limited coverage). The query for fetching a project + its items is:

```graphql
query {
  organization(login: "capitalone") {
    projectV2(number: 7) {
      title
      items(first: 50) {
        nodes {
          content {
            ... on Issue { title number repository { name } }
            ... on PullRequest { title number repository { name } }
          }
          fieldValues(first: 10) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2SingleSelectField { name } } }
            }
          }
        }
      }
    }
  }
}
```

---

## 6. Discussions

GitHub Discussions (per-repo, enabled in Settings) is for **threaded conversations that aren't issues** — Q&A, polls, announcements, RFC discussion, show-and-tell.

Categories you typically enable:
- **Q&A** — has an "accepted answer" mark, threaded
- **Ideas** — for proposals before they become issues
- **Show and tell**
- **Polls** (recent feature)
- **Announcements** (maintainer-only)

For internal projects with Confluence/Wiki shops, Discussions is often skipped. For OSS, it offloads "is this a bug or am I confused?" traffic from Issues.

---

## 7. The Jira bridge (Capital One reality)

Capital One uses Jira heavily. Standard patterns:

- **Branch naming**: `feature/PROJ-1234-add-token-cache` — the JIRA key is in the branch name.
- **PR title prefix**: `[PROJ-1234] feat: add token caching` — JIRA key is in the PR title.
- **Smart commits**: `git commit -m "PROJ-1234 #close #comment Done"` if your Jira instance has GitHub for Jira integrated. Jira auto-transitions the ticket and adds comments.
- **Jira-GitHub link** (Atlassian's "GitHub for Jira" app or "Jira" GitHub App): bidirectional linking — PRs appear in Jira tickets, Jira links surface in PR sidebar.
- **GitHub Issues disabled** on most internal repos (Settings → Features → uncheck Issues) to avoid two systems of record.

The convention to internalize: **JIRA = the unit of business work**. **PR = the unit of code change.** One JIRA can have many PRs; PRs link back via title prefix or branch name.

---

## 8. Issue-to-PR linking

In a PR body or commit message:

```
Closes #42
Fixes #43
Resolves #44
Closes capitalone/other-repo#100
```

When the PR merges, the linked issues auto-close. The keywords are case-insensitive and there are 7 valid ones: `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves`, `resolved`.

Without a closing keyword (e.g., `See #42` or `Related to #42`), GitHub still shows the link in the sidebar but doesn't auto-close.

---

## 9. Notifications and discoverability

GitHub's notification settings are the most-overlooked productivity lever. Tune them:

- **Watch settings per repo**: Participating only (default), All Activity, Releases only, Custom, Ignore.
- **Subscribed**: notifications for things you commented on or were assigned to.
- **Email digest**: weekly summary instead of per-event.
- **Filter inbox by reason**: `reason:author`, `reason:mention`, `reason:review-requested`, `reason:team-mention`.

For an active reviewer at Capital One scale, Custom (Issues + PRs + Discussions, not Releases) + filter by `review-requested` is the default that keeps you sane.

---

## 10. Cross-references

- PRs in depth (the change unit) → [module 10](10_prs_code_review_merge.md).
- CODEOWNERS auto-routing → [module 11](11_branch_protection_rulesets_codeowners.md).
- `gh` CLI for issues + PRs → [module 14](14_gh_cli_fundamentals.md).
- GitHub Apps + webhooks for custom Jira integrations → [module 52](52_apps_webhooks_ghcli_graphql.md).
