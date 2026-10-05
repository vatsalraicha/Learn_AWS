# 52 — GitHub Apps, webhooks, `gh` CLI scripting, GraphQL vs REST

> *"When the platform team needs more than what Actions can do."*

## Why this module exists

Beyond CI/CD, GitHub is a programmable platform. GitHub Apps are how you build serious automation (chatbots, custom checks, org-wide dashboards). This module is the power-user / platform-engineer layer.

---

## 1. GitHub Apps vs OAuth Apps vs PATs

| | OAuth App | GitHub App | PAT |
|---|---|---|---|
| Identity | A user (acts as them) | Its own identity (acts as itself) | A user (acts as them) |
| Install scope | All user repos by default | Per-repo or all repos in org | All user's repos |
| Token expiry | Long-lived (until revoked) | 1 hour (auto-refresh) | User-configured (often forever) |
| Rate limit | 5000/hr per user | 5000/hr per installation (scales) | 5000/hr per user |
| Webhooks | Limited | Native event subscriptions | None |
| Use for | User-facing tools | Bots, internal automation | Personal scripts |

**Default to GitHub Apps for any non-trivial automation.** OAuth Apps are legacy. PATs are for personal one-off scripts.

---

## 2. Building a GitHub App

1. Settings → Developer settings → GitHub Apps → New GitHub App
2. Choose:
   - Name, description, homepage URL
   - Webhook URL (where events POST) — optional
   - Permissions (per category: Repo / Org / User permissions)
   - Events subscribed to (push, pull_request, issues, etc.)
   - Where it can be installed (this account only / any account)
3. Generate webhook secret + private key
4. Install on a repo / org

The App is now a callable identity. To act as it from code:

```python
import jwt
import requests
import time

APP_ID = 12345
PRIVATE_KEY = open("private-key.pem").read()
INSTALLATION_ID = 67890

# 1. Generate App-level JWT (10 min validity)
now = int(time.time())
app_jwt = jwt.encode(
    {"iat": now - 60, "exp": now + 600, "iss": APP_ID},
    PRIVATE_KEY,
    algorithm="RS256",
)

# 2. Exchange for installation access token
resp = requests.post(
    f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens",
    headers={"Authorization": f"Bearer {app_jwt}", "Accept": "application/vnd.github+json"},
)
installation_token = resp.json()["token"]   # 1-hour lifetime

# 3. Use the installation token as a normal API token
me = requests.get(
    "https://api.github.com/repos/capitalone/cool-repo",
    headers={"Authorization": f"Bearer {installation_token}"},
).json()
```

In Actions, use `actions/create-github-app-token@v1` to do steps 1+2 in one step.

---

## 3. Webhooks

GitHub sends HTTP POSTs to your webhook URL for subscribed events. Payload contains the event data + a signature for verification.

```python
# Flask example
import hashlib
import hmac
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = "your-secret"

@app.route("/webhook", methods=["POST"])
def webhook():
    sig = request.headers.get("X-Hub-Signature-256", "")
    body = request.data
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        abort(401)

    event = request.headers["X-GitHub-Event"]
    payload = request.json
    print(f"Event: {event}, action: {payload.get('action')}")
    return "", 204
```

Common events:
- `push` — commits pushed
- `pull_request` — PR opened/closed/labeled/merged
- `issue_comment` — comment on issue or PR
- `installation` / `installation_repositories` — App installed/uninstalled
- `workflow_run` / `workflow_job` — Actions workflow lifecycle
- `check_suite` / `check_run` — status checks

Webhooks are FIRE-AND-FORGET. GitHub retries on failure (5xx) up to ~24h.

---

## 4. ChatOps pattern

Bot listens for `/deploy staging` style comments on PRs, executes action, posts result:

```python
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.json
    if request.headers["X-GitHub-Event"] == "issue_comment":
        comment = payload["comment"]["body"]
        if comment.startswith("/deploy "):
            env = comment.split()[1]
            # Trigger Actions workflow via repository_dispatch
            requests.post(
                f"https://api.github.com/repos/{payload['repository']['full_name']}/dispatches",
                headers={"Authorization": f"Bearer {installation_token}"},
                json={"event_type": f"chatops-deploy-{env}", "client_payload": {
                    "pr": payload["issue"]["number"],
                    "actor": payload["sender"]["login"],
                }},
            )
            # React with 👀
            requests.post(
                f"https://api.github.com/repos/{payload['repository']['full_name']}/issues/comments/{payload['comment']['id']}/reactions",
                headers={"Authorization": f"Bearer {installation_token}"},
                json={"content": "eyes"},
            )
    return "", 204
```

---

## 5. Probot — the framework

[Probot](https://probot.github.io/) is a Node.js framework for GitHub Apps. Handles JWT generation, installation tokens, webhook routing.

```javascript
module.exports = (app) => {
  app.on('issues.opened', async (context) => {
    const issueComment = context.issue({
      body: 'Thanks for the issue! A maintainer will respond shortly.',
    });
    return context.octokit.issues.createComment(issueComment);
  });
};
```

Deploy: `probot deploy` or AWS Lambda / Vercel / fly.io.

For Python equivalent: `gh4j` or just hand-rolled with `requests` + PyJWT.

---

## 6. `gh api` — the CLI for arbitrary API calls

```bash
# REST
gh api /repos/capitalone/cool-repo
gh api -X POST /repos/org/repo/issues -f title="..." -f body="..."
gh api --paginate /orgs/capitalone/repos --jq '.[].name'

# GraphQL
gh api graphql -f query='
  query {
    organization(login: "capitalone") {
      repositories(first: 10) {
        nodes { name, pushedAt, isPrivate }
      }
    }
  }
' --jq '.data.organization.repositories.nodes'
```

`-f` adds form fields; `-F` adds raw JSON values; `-X` overrides HTTP method.

`--jq` runs jq on the output for slicing.

`--paginate` follows `Link: rel="next"` headers automatically.

---

## 7. REST vs GraphQL

| | REST | GraphQL |
|---|---|---|
| Endpoint | Many | `https://api.github.com/graphql` |
| Returns | All fields by default | Only fields you ask for |
| Cross-resource | Multiple requests | Single request, nested |
| Pagination | `Link` header | `pageInfo` + cursor |
| Rate limit | Per request | Per "node fetched" (calculated) |
| Documentation | docs.github.com/rest | docs.github.com/graphql |
| Best for | Simple, one-resource calls | Complex queries spanning many resources |

GraphQL example — get the last 5 PRs across all repos in an org, with reviewers:

```graphql
query {
  organization(login: "capitalone") {
    repositories(first: 100) {
      nodes {
        name
        pullRequests(first: 5, states: OPEN, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            number
            title
            author { login }
            reviewRequests(first: 10) {
              nodes {
                requestedReviewer {
                  ... on User { login }
                  ... on Team { name }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

One request, fully nested. The REST equivalent is ~N+M+K requests. For cross-repo dashboards, GraphQL is dramatically faster.

GitHub's GraphQL explorer ([docs.github.com/graphql/overview/explorer](https://docs.github.com/graphql/overview/explorer)) lets you build queries interactively.

---

## 8. Rate limits

| Token type | Limit |
|---|---|
| Unauthenticated | 60/hr |
| Authenticated (PAT, user OAuth) | 5,000/hr |
| GitHub App installation | 5,000/hr per installation |
| GraphQL | 5,000 points/hr (different metric — calculated per node) |
| Search API | 30 requests/min |
| Secondary rate limits | Per-endpoint, per-IP — opaque |

Check current usage: `gh api /rate_limit` or response header `X-RateLimit-Remaining`.

For high-volume scripts: use a GitHub App (5k/hr per installation × many installations); add exponential backoff on 429 responses.

---

## 9. `gh` extensions

Extensions add subcommands. Useful ones:
- `gh-dash` — TUI dashboard for PRs / issues
- `gh-notify` — notification inbox in TUI
- `gh-copilot` — Copilot suggestions (see [module 53](53_ai_copilot.md))
- `gh-poi` — prune local branches whose PR was merged
- `gh-spice` — stacked PR management

```bash
gh extension install dlvhdr/gh-dash
gh dash
```

Custom extensions: any binary/script named `gh-foo` on your PATH becomes `gh foo`. Three-line shell scripts become CLI tools.

---

## 10. Cross-references

- Auto-merge Dependabot via gh CLI scripting → [module 34](34_ghas_dependabot.md).
- ChatOps via repository_dispatch → [module 20](20_actions_workflow_events.md).
- Audit-log queries via `gh api` → [module 36](36_compliance_sso_scim_audit.md).
- `gh copilot` for command suggestions → [module 53](53_ai_copilot.md).
