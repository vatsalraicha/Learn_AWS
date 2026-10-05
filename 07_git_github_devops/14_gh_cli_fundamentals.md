# 14 — GitHub CLI (`gh`) fundamentals

> *"`gh` is faster than the web UI for 90% of what you do daily. Learn the 20 commands that matter and you'll never reach for the browser for routine work again."*

## Why this module exists

The GitHub CLI shipped GA in September 2020 and has become the productivity baseline for senior engineers. It does everything the web UI does, plus scripts cleanly, plus exposes the API directly for things the UI doesn't expose. This module is the practical cheat sheet.

---

## 1. Install + auth

```bash
brew install gh                       # macOS
sudo apt install gh                   # Ubuntu/Debian via official repo
winget install GitHub.cli             # Windows

gh auth login                         # device-code OAuth, walks you through
gh auth status                        # what am I logged in as
gh auth refresh -s admin:org,workflow # add new scopes to existing auth
gh auth setup-git                     # use gh as git credential helper for HTTPS

# Switch between accounts (e.g., personal vs work)
gh auth switch
```

For Enterprise Server:

```bash
gh auth login --hostname github.example.com
```

---

## 2. The 20 commands you'll use daily

### Repos

```bash
gh repo view                                       # info about current repo
gh repo view org/repo --web                        # open in browser
gh repo clone org/repo                             # clone (auto-uses SSH if configured)
gh repo create my-new-thing --public               # create new repo
gh repo create org/new-thing --private --template org/template-repo
gh repo sync                                       # sync your fork with upstream
gh repo fork                                       # fork current repo
gh repo list capitalone --limit 200                # list repos in an org
gh repo edit --add-topic ml --add-topic prod
```

### Pull requests

```bash
gh pr create                                       # interactive PR creation
gh pr create --title "feat: x" --body "..." --base main --head my-branch
gh pr create --fill                                # title/body from commits
gh pr list                                         # list PRs in current repo
gh pr list --author "@me" --state open
gh pr view 123                                     # PR details in terminal
gh pr view 123 --web                               # open in browser
gh pr diff 123                                     # show diff in terminal
gh pr checks 123                                   # status of CI checks
gh pr checkout 123                                 # check out PR branch locally
gh pr review 123 --approve --body "LGTM"
gh pr review 123 --comment --body "see inline"
gh pr review 123 --request-changes --body "needs tests"
gh pr edit 123 --add-reviewer vraicha,jdoe --add-label "needs-test"
gh pr merge 123 --squash --delete-branch           # squash-and-merge, delete branch
gh pr merge 123 --auto --squash                    # enable auto-merge
gh pr close 123 --delete-branch
gh pr ready 123                                    # mark draft as ready for review
```

### Issues

```bash
gh issue create --title "..." --body "..." --label bug --assignee @me
gh issue list --label bug --state open
gh issue view 42
gh issue edit 42 --add-label triage --milestone v1.5
gh issue close 42 --comment "Fixed in #50"
gh issue reopen 42
gh issue develop 42 --branch-name feature/PROJ-42-fix --checkout
```

### Workflows + runs (Actions)

```bash
gh workflow list
gh workflow view ci.yml
gh workflow run ci.yml -f environment=staging       # trigger workflow_dispatch
gh workflow disable ci.yml
gh workflow enable ci.yml

gh run list                                         # recent runs
gh run list --workflow ci.yml --limit 5
gh run view 123456                                  # details
gh run view --job 987654 --log                      # full log of one job
gh run view 123456 --log-failed                     # just the failed steps
gh run rerun 123456                                 # re-run all failed jobs
gh run rerun 123456 --failed                        # only failed jobs
gh run watch 123456                                 # follow live until done
gh run cancel 123456
```

### Releases + tags

```bash
gh release create v1.2.0 --notes "..."
gh release create v1.2.0 --generate-notes          # autogenerate from PRs
gh release create v1.2.0 --notes-from-tag          # use annotated-tag message
gh release upload v1.2.0 ./dist/*.tar.gz
gh release list
gh release view v1.2.0
gh release download v1.2.0 -p '*.tar.gz'
```

### Secrets + variables (for Actions)

```bash
gh secret list
gh secret list --env staging
gh secret set MY_TOKEN                              # prompts for value
gh secret set MY_TOKEN < token.txt
gh secret set MY_TOKEN -b "value-here"
gh secret set MY_TOKEN --env staging --body "$VALUE"
gh secret set MY_TOKEN --org capitalone --visibility selected --repos repo1,repo2
gh secret delete MY_TOKEN

gh variable list
gh variable set AWS_REGION --body "us-east-1"
```

### Codespaces (if used)

```bash
gh codespace list
gh codespace create --repo org/repo
gh codespace ssh
gh codespace code                                   # open in local VS Code
gh codespace delete -c <name>
```

### Projects (v2)

```bash
gh project list --owner @me
gh project view 5 --owner @me
gh project item-add 5 --owner @me --url https://github.com/org/repo/issues/42
gh project item-list 5 --owner @me --format json
gh project field-list 5 --owner @me
```

### Raw API

```bash
gh api /repos/capitalone/cool-repo
gh api /orgs/capitalone/teams/ml-team/members --paginate
gh api -X POST /repos/org/repo/issues -f title="..." -f body="..."
gh api graphql -f query='query { viewer { login } }'

# JSON-format output, filter with jq
gh api /repos/capitalone/cool-repo --jq '.full_name, .pushed_at'
gh pr list --json number,title,author --jq '.[] | "\(.number) \(.author.login) \(.title)"'
```

---

## 3. JSON output + jq

Most `gh` commands accept `--json field1,field2,...` for structured output:

```bash
gh pr list --json number,title,author,statusCheckRollup --jq '.[] | select(.statusCheckRollup[].conclusion == "FAILURE") | .number'

gh run list --json databaseId,name,conclusion,headBranch --jq '.[] | select(.conclusion=="failure")'

gh issue list --json number,title,labels --jq '.[] | select(.labels | map(.name) | index("bug"))'
```

The combo of `--json` and `--jq` is the basis for almost all CLI automation.

---

## 4. Aliases

`gh` has user-defined aliases for repeated commands:

```bash
gh alias set co 'pr checkout'                      # gh co 123
gh alias set bugs 'issue list --label bug'         # gh bugs
gh alias set release-notes 'pr list --base main --merged --json title,number,author -t "{{range .}}* {{.title}} (#{{.number}}) — @{{.author.login}}\n{{end}}"'
gh alias list
gh alias delete co
```

Aliases are stored in `~/.config/gh/config.yml`. Share useful ones with your team.

---

## 5. Extensions

`gh` extensions add new sub-commands. Some valuable ones:

```bash
gh extension install dlvhdr/gh-dash                 # TUI dashboard for PRs/issues
gh extension install meiji163/gh-notify             # notification inbox in TUI
gh extension install nektos/gh-act                  # run actions locally (wraps act)
gh extension install github/gh-copilot              # AI command suggestions (Copilot)
gh extension install seachicken/gh-poi              # prune local branches whose PR was merged

gh extension list
gh extension upgrade --all
```

---

## 6. `gh copilot` (Copilot integration)

```bash
gh copilot suggest "list S3 buckets in us-east-1"   # suggest a shell command
gh copilot explain "find . -mtime -7 -type f"        # explain a command you saw
```

Requires Copilot subscription. Useful when you forget the exact flag for `aws` or `kubectl`. The suggestion comes with a one-key "run it" option, with safety prompts for destructive commands.

---

## 7. Common workflow patterns

### "What PRs am I waiting on?"

```bash
gh pr list --search "is:open review-requested:@me"
```

### "Show me my open PRs with failing checks"

```bash
gh pr list --author @me --json number,title,statusCheckRollup \
  --jq '.[] | select(.statusCheckRollup[] | .conclusion == "FAILURE") | "\(.number) \(.title)"'
```

### "Re-run failed jobs on my latest PR's run"

```bash
RUN=$(gh run list --branch $(git branch --show-current) --limit 1 --json databaseId --jq '.[0].databaseId')
gh run rerun $RUN --failed
```

### "Approve a PR and enable auto-merge"

```bash
gh pr review 123 --approve
gh pr merge 123 --auto --squash --delete-branch
```

### "Bulk close stale issues"

```bash
gh issue list --search "is:open label:stale updated:<2025-01-01" --json number \
  --jq '.[].number' | xargs -I {} gh issue close {} --comment "closing as stale"
```

### "Bootstrap a new repo from a template"

```bash
gh repo create capitalone/new-ml-svc \
  --template capitalone/python-ml-template \
  --private \
  --add-readme \
  --clone
cd new-ml-svc
```

---

## 8. Configuration

```bash
gh config get editor                                # 'vim', 'nvim', 'code --wait', etc.
gh config set editor "code --wait"
gh config set git_protocol ssh
gh config set browser firefox
gh config list

# Per-host (Enterprise)
gh config set --host github.example.com git_protocol ssh
```

Config file: `~/.config/gh/config.yml`. Hosts file: `~/.config/gh/hosts.yml` (holds tokens — never check in).

---

## 9. Speed tips

- `gh pr list --limit 200` defaults to 30; if you actually want more, ask.
- `gh api ... --paginate` follows pagination automatically (otherwise stops at 30/100 items).
- `gh pr checkout 123` is much faster than fetching the branch manually for review.
- `gh run watch` instead of refreshing the browser to wait for CI.
- `gh pr view --web` when you do need the browser — `--web` opens to the right tab.

---

## 10. Cross-references

- Workflow runs + Actions in depth → [module 20](20_actions_workflow_events.md) onward.
- Secrets/variables management → [module 23](23_actions_vars_secrets_env.md).
- `gh api` + GraphQL for org-wide automation → [module 52](52_apps_webhooks_ghcli_graphql.md).
- `gh copilot` in deeper detail → [module 53](53_ai_copilot.md).
