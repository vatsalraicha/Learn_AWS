# Quiz — Part 4 (IT Fundamentals: Modules 47-59)

**Q1.** What's the Socratic-mode AI study assistant prompting pattern?

<details><summary>Answer</summary>

Tell it to ask questions back, not give answers. "Don't give me the answer. Ask me questions to help me get there. Stop after each question."
</details>

**Q2.** Why is cycle time a better metric than velocity?

<details><summary>Answer</summary>

Cycle time is harder to game and directly measures throughput. Velocity inflates with practice as teams pad estimates.
</details>

**Q3.** Why are senior orgs dropping story-point estimation?

<details><summary>Answer</summary>

Gameable, time-consuming, doesn't predict better than t-shirt sizes or just breaking work into similar-sized pieces.
</details>

**Q4.** What is "fine-grained reactivity" in modern frontend frameworks?

<details><summary>Answer</summary>

Only DOM nodes that depend on changed state re-render — vs whole-component re-render. Implemented by Solid, Svelte 5, Vue Vapor, Angular signals.
</details>

**Q5.** What replaced Vuex as Vue's official state management?

<details><summary>Answer</summary>

Pinia (since 2022).
</details>

**Q6.** When use `v-if` vs `v-show` in Vue?

<details><summary>Answer</summary>

`v-if` adds/removes from DOM (use for rare toggles). `v-show` toggles CSS `display` (use for frequent toggles — cheaper).
</details>

**Q7.** What's the killer feature of Hono over Express/Fastify?

<details><summary>Answer</summary>

Portability — same code runs on Node, Bun, Deno, Cloudflare Workers, AWS Lambda, edge runtimes.
</details>

**Q8.** Why is Postgres often the 2026 default for OLTP over MongoDB/DynamoDB?

<details><summary>Answer</summary>

Relational + ACID + huge ecosystem + JSONB for flexible schema + pgvector for vector search + battle-tested. Postgres-with-extensions covers ~80% of what people used to need NoSQL for.
</details>

**Q9.** What's the difference between Vitest and Jest?

<details><summary>Answer</summary>

Vitest: native ESM + TypeScript, faster startup, reuses Vite config, browser mode, watch by default. Jest-compatible API but much modernized.
</details>

**Q10.** Why is 100% test coverage typically a bad goal?

<details><summary>Answer</summary>

Leads to testing implementation details + brittle tests with diminishing returns. 70-80% is the sweet spot.
</details>

**Q11.** Why is Caddy's automatic Let's Encrypt TLS a killer feature?

<details><summary>Answer</summary>

Just add the domain to the Caddyfile + point DNS — TLS just works. No certbot dance, no renewal cron, no manual cert mgmt.
</details>

**Q12.** Why never commit `.env` to Git?

<details><summary>Answer</summary>

Secrets in env files get leaked. Even if "secret" in name, repo history is forever. Use `.env.example` for the template + cloud secrets manager for actual values.
</details>

**Q13.** Where should K8s Secrets actually come from in production?

<details><summary>Answer</summary>

From cloud Secret Manager (AWS Secrets Manager / Azure Key Vault / GCP SM / Vault) via External Secrets Operator — never base64'd into Git.
</details>

**Q14.** What's the difference between AI tool autocomplete, chat, and agentic modes?

<details><summary>Answer</summary>

- **Autocomplete**: ghost-text inline as you type (Copilot Tab, Cursor Tab)
- **Chat**: conversation about code (Cursor Chat, Claude.ai)
- **Agentic**: give task, AI executes multi-step with file edits + shell (Claude Code, Cursor Composer, Aider)
</details>

**Q15.** Why is "atrophy risk" with AI tools real, and how to mitigate?

<details><summary>Answer</summary>

Relying on autocomplete erodes fundamentals. Mitigation: periodically write code without AI to stay sharp. Use AI for boilerplate, but synthesize the architecture yourself.
</details>

---

**Scoring**: 13+ → strong cross-stack literacy. 9-12 → solid. < 9 → revisit modules where you missed.
