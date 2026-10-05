# 59 — AI Tools for Engineers in 2026

## 1. The landscape

| Tool | Strength |
|---|---|
| **GitHub Copilot** | Default; broadest install; in-IDE autocomplete; agentic mode (Workspace) |
| **Cursor** | Standalone editor (VS Code fork); fast autocomplete + chat |
| **Windsurf** | Cursor competitor; agentic-first |
| **Claude Code (CLI)** | Vatsal's tool; project-aware coding agent |
| **Claude.ai** | Long-form reasoning + Projects + Skills |
| **Aider** | OSS terminal coding agent |
| **Cline** | OSS VS Code extension agent |
| **Continue** | OSS extension; bring-your-own-model |
| **Replit Agent** | Cloud IDE + agent |
| **Cody** (Sourcegraph) | Code search + AI in big repos |
| **Tabnine** | Privacy-focused autocomplete |

## 2. The three usage modes

### Autocomplete mode (Copilot, Cursor Tab)
Ghost-text completion as you type. Accept with Tab. Best for boilerplate, obvious patterns.

### Chat mode (Cursor Chat, Claude.ai, ChatGPT)
Conversation about code. Best for: "explain this function", "refactor to do X", brainstorming.

### Agentic mode (Claude Code, Cursor Composer, Aider, Cline)
You give a task; the agent reads files, edits, runs commands, iterates. Best for: multi-file changes, prototype generation, refactors.

## 3. GitHub Copilot in 2026

- ~15M paid users (early 2026)
- **Copilot Free** — limited usage
- **Copilot Pro** — $10/mo individual
- **Copilot Business** — $19/user/mo (org)
- **Copilot Enterprise** — $39/user/mo (custom models on org code)
- **Usage-based billing** moving in June 2026 ("AI Credits")

Features:
- Code completions (in-line)
- Chat (in-IDE)
- Copilot Workspace (agentic; web-based)
- Autofix for CodeQL
- PR summaries
- CLI assistance

## 4. Claude Code (Vatsal's daily tool)

Claude Code is the CLI agent:
```bash
claude
# Opens an interactive session in current directory
# Read files, edit, run shell commands, iterate
```

Strengths:
- Full project awareness via `CLAUDE.md`
- Strong reasoning + planning
- Skills + Plugins ecosystem
- Web UI (claude.ai/code) in 2026
- Enterprise GA early 2026

## 5. Cursor — the rising VS Code fork

- ~$20/mo Pro tier
- Built on VS Code; familiar UI
- Built-in chat + agent ("Composer") + Tab completion
- Multi-file edits
- Codebase-wide context (vector-indexed)

The 2026 wave: ~30% of new engineers default to Cursor over VS Code + Copilot.

## 6. The "prompt the agent well" patterns

### Be specific
Bad: "Add login"
Good: "Add a /login route that accepts email + password, validates against the users table, sets a session cookie, redirects to /dashboard on success. Use the existing auth helper in src/lib/auth.ts."

### Reference files
"Look at src/lib/db.ts for the connection pattern; apply the same to src/lib/redis.ts."

### Constrain
"Don't add new dependencies. Don't change the public API. Don't touch tests."

### Verify
"After making changes, run `npm test` and report the output."

### Iterate
Long sessions: break the task into chunks. Ask the agent to plan before executing.

## 7. Generating tests

```
Generate unit tests for src/lib/auth.ts using Vitest.
- Cover login, logout, refreshToken
- Include edge cases: expired token, invalid signature, missing email
- Use MSW to mock the API
- Aim for 80% line coverage
```

AI-generated tests need review:
- Verify they actually test the intended behavior
- Don't accept tests that just snapshot whatever the function returns
- Run them; confirm they fail when you break the code

## 8. Generating documentation

```
Read src/lib/auth.ts. Generate a README section explaining:
- The auth flow (3 sentences)
- How to use the public functions
- Common errors and how to handle them
Match the style of existing READMEs in this repo.
```

## 9. Troubleshooting + debugging

```
This test is failing intermittently. Look at the test output + the function. What hypotheses do you have? Don't fix yet — list the top 3 candidates.
```

Force the agent to enumerate hypotheses before committing to a fix. Reduces "I think I fixed it" without root cause.

## 10. Generating automation scripts

Great use case:
```
Write a Python script that:
- Reads all .yaml files in ./manifests/
- Sets `resources.requests.cpu` to "100m" if missing
- Writes the files back
- Reports a summary of changes
```

Or:
```
Write a bash script that runs Trivy on every Docker image in our registry and posts results to DefectDojo.
```

These tasks are well-bounded; AI gets them mostly right + you review.

## 11. Limits + risks

**Verify everything**:
- API signatures (Copilot will invent methods)
- Library versions
- Security-sensitive code (auth, crypto, file ops)
- Anything where wrong-without-knowing is costly

**Don't paste secrets into chat models** — even though many vendors say "we don't train on your data," operationally treat the chat surface as untrusted. Use enterprise tiers with data residency / no-train clauses for sensitive work.

**Atrophy risk** — relying entirely on autocomplete can erode fundamentals. Periodically write code from scratch without AI to stay sharp.

## 12. Governance for AI tools (enterprise angle)

For Capital One / regulated finance:
- **Approved vendor list** — only enterprise tiers with DPA + no-train guarantees
- **Air-gap / private deployment** for sensitive repos (Copilot Enterprise + custom models, Claude Code Enterprise)
- **Data classification** — what can be sent to AI tools (no PII, no card data, no SR 11-7 model code)
- **Audit logs** of AI tool usage (prompts + outputs in regulated repos)
- **Code review** by humans for AI-generated security-critical code

See [Topic 07 Module 55](../07_git_github_devops/55_ai_governance_privacy.md) for the deep dive.

## 13. Quick self-check

1. What's the difference between autocomplete, chat, and agentic AI modes?
2. Why is Cursor a serious challenger to VS Code + Copilot?
3. Why force the agent to enumerate hypotheses before fixing a bug?
4. What's the atrophy risk with AI tools?
5. What enterprise governance applies to AI dev tools in regulated finance?

(Answers: autocomplete = ghost-text inline, chat = conversation about code, agentic = give task and AI executes multi-step with file edits + shell; built on VS Code so familiar + tight integration of Tab + Chat + Composer + codebase-wide context; reduces premature fixes that look right but miss root cause; relying on autocomplete erodes fundamentals — periodically write code without AI; approved vendor list, enterprise tiers with no-train, data classification, audit logs, human review of AI-generated security code.)
