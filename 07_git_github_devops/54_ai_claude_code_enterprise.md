# 54 — ⭐ Claude Code in enterprise (agentic workflows, scoping, `.agent.md`, MCP)

> *"Copilot autocompletes lines. Claude Code completes tasks. Different category of tool."*

## Why this module exists

Claude Code (Anthropic's agentic coding tool) is increasingly deployed in enterprises alongside Copilot. Capital One's published commitment to AI dev tools includes a dedicated team for enterprise governance — and Claude Code Enterprise hit GA in early 2026. This module covers what Claude Code is, how it differs from Copilot, and the bank-grade rollout pattern.

---

## 1. What Claude Code actually does

Claude Code is a CLI (and IDE extension, and now a desktop app) that:
- Reads your codebase via tool calls (Read, Grep, Glob)
- Runs commands (Bash)
- Edits files (Edit, Write)
- Verifies changes (running tests, lints)
- Can spawn sub-agents for parallel work

A typical session: `cc` (or `claude` in newer versions) → describe a task → Claude reads the relevant code, makes changes, runs tests, commits. Several minutes to hours per task.

Vs Copilot: Copilot suggests the next line; Claude completes the next task. Different temporal scale.

---

## 2. The plans

| Plan | What |
|---|---|
| **Pro** | Personal use; limited usage |
| **Team** | Multi-user; SOC 2 Type II; shared knowledge base |
| **Enterprise** | Team + SSO, RBAC, org policy enforcement, HIPAA, BYOK, customizable retention, detailed audit logs |

Capital One: certainly Enterprise.

---

## 3. The agentic loop

Claude Code's strength is the iterate-until-done loop:

```
1. User: "Add OIDC support to the auth module"
2. Claude: (Grep for "auth", Read auth.py)
3. Claude: "I see you use a TokenService class. I'll add OIDC alongside the existing OAuth path."
4. Claude: (Edit auth/oidc.py, Edit auth/token_service.py, Edit tests/test_auth.py)
5. Claude: (Bash: pytest tests/test_auth.py)
6. Test fails — wrong import path.
7. Claude: (Edit fix import)
8. Claude: (Bash: pytest)
9. Passes.
10. Claude: "Done. 3 files changed, 5 new tests added. Verified via pytest. Want me to also update the README?"
```

You can scope:
- Time-bounded: "spend 15 minutes investigating"
- Scope-bounded: "only touch files in `src/auth/`"
- Permission-bounded: "don't run any commands; just propose changes"
- Verify-bounded: "after editing, always run pytest"

---

## 4. `.agent.md` and CLAUDE.md

The repo can include a `CLAUDE.md` (or `AGENTS.md` — emerging convention) at the root. Claude Code reads it at session start as context.

```markdown
# Project context for AI agents

This is a fraud-detection model service.
- Code style: black + ruff; type-hint everything.
- Tests: pytest in `tests/`; run with `make test`.
- Don't modify `vendor/` (third-party).
- Don't add new dependencies without asking — we have an approved list.
- Run `pre-commit run --all-files` before committing.
- Use the InnerSource library `capital-one-pipeline` for any CI changes.
- For AWS calls, use `boto3` via the wrapper in `lib/aws_wrapper.py` — never raw `boto3.client(...)`.
- All commits must be Conventional Commits format.
- Push protection is enabled; don't include any secret-shaped strings even in test fixtures.
```

The agent reads + follows these instructions. Reduces friction (no need to repeat in every session) + enforces team norms at the AI layer.

---

## 5. MCP — Model Context Protocol

[MCP](https://modelcontextprotocol.io/) (Anthropic-pioneered, now multi-vendor adopted) is a standard for connecting LLMs to external tools and data.

Examples of MCP servers Claude Code can use:
- **Filesystem** — read/write specific dirs
- **GitHub** — issue/PR operations
- **Slack** — send messages
- **Postgres / Snowflake** — read DB schemas + run queries
- **AWS** — perform read operations
- **Custom**: any tool you build

Configure in your Claude Code settings (`~/.claude/settings.json` or equivalent):

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "..." }
    },
    "snowflake": {
      "command": "uvx",
      "args": ["mcp-server-snowflake"],
      "env": { "SNOWFLAKE_ACCOUNT": "..." }
    }
  }
}
```

For Capital One: internal MCP servers exposing approved tools (read-only Snowflake, internal docs search, JIRA, ServiceNow) — Claude Code uses them as part of agent workflows. Sensitive operations would not be MCP-exposed (or require approval flow).

---

## 6. Skills and slash commands

Claude Code supports **skills** — reusable workflow definitions activated by slash commands.

```
~/.claude/skills/
├── deploy-staging/
│   └── SKILL.md
├── post-mortem/
│   └── SKILL.md
└── code-review/
    └── SKILL.md
```

Each `SKILL.md` is a markdown file describing the skill's purpose + procedure. Claude reads it on activation.

```markdown
# /code-review

Review the current PR following Capital One's review checklist.

1. Read the PR description + diff (use `gh pr view`).
2. Check for:
   - Signed commits
   - CODEOWNERS coverage
   - Test coverage delta
   - Conventional Commits format
   - Security: no secret-shaped strings, no SQL string concatenation
   - SR 11-7 model-impacting paths route to MRM CODEOWNERS
3. Post review comments (use suggestion syntax for fixes).
4. Decide: approve / request changes / comment.
```

Now `/code-review` is a one-command code-review pass with bank standards baked in.

---

## 7. Subagents

For complex tasks, Claude Code can spawn focused subagents:

- `general-purpose` — broad research
- `Explore` — fast read-only code search
- `Plan` — design + planning
- Custom: define agents per your role/team

Subagents run in isolated contexts. The main session sees only their summary. Useful for: long codebase exploration without blowing main context; parallel investigation of independent areas.

---

## 8. The Capital One-grade rollout pattern

For deploying Claude Code (or any agentic AI tool) at a bank:

1. **Procurement + legal** — DPA, BAA if PHI is in scope, IP indemnity terms reviewed.
2. **Security review** — what data leaves the network? where does it go? retention?
3. **SSO + audit log integration** — every session attributed to a user via SSO; logs to SIEM.
4. **Content exclusion** — sensitive paths denied access via config.
5. **MCP server review** — every approved server reviewed by security; default no MCP servers.
6. **Skills review** — central skill repo, CODEOWNERS, security-reviewed. Users can install personal skills; only approved skills can touch prod systems.
7. **Pilot** — small team for 6–8 weeks; collect: time saved, bugs introduced, security incidents.
8. **Rollout** — phased by team; feedback loop.
9. **Quarterly review** — usage metrics, incidents, ROI.

---

## 9. The output discipline

Whatever the AI agent did, you commit:
- **You** are responsible for the diff.
- **You** must understand every line you commit.
- **You** must run the tests + verify behavior — not just trust the agent.
- **Your** name is on the commit (the AI is not a co-author for legal purposes).

Treat AI output like a junior engineer's PR — review carefully before merging.

For SR 11-7 model code specifically: AI-generated changes to model code are the SAME bar — full code review, full MRM independent validation, audit trail. AI involvement is a factor in scope, not a shortcut around process.

---

## 10. Cursor vs Claude Code vs Copilot — when to pick

| Tool | Primary use | Best for |
|---|---|---|
| **Copilot** | Inline completion + chat | Day-to-day typing acceleration; broad IDE support |
| **Cursor** | AI-first IDE | Heavy editor-integrated agentic workflows; chat with full repo context |
| **Claude Code** | Agentic CLI | Complex multi-step tasks; codebase-wide refactors; CI/CD automation |
| **Aider** | OSS, lightweight CLI | Privacy-sensitive, self-host friendly |

At Capital One: probably Copilot for IDE day-to-day + Claude Code for heavier work. Multiple tools coexist; users pick per task.

---

## 11. Cross-references

- GitHub Copilot in depth → [module 53](53_ai_copilot.md).
- Governance + privacy posture for AI dev tools → [module 55](55_ai_governance_privacy.md).
- Capital One's DEI (Developer Experience & Innovation) team's role in enterprise AI tools → [module 56](56_capital_one_devops_deep.md).
