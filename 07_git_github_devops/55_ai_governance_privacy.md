# 55 — ⭐🏦 Governance, privacy, code-of-conduct for AI dev tools

> *"At a bank, the question isn't 'is the AI useful?' It's 'can we prove every piece of generated code went through the same controls as human-written code, and that no sensitive data leaked into a model's training set?'"*

## Why this module exists

Capital One's Code of Conduct (publicly available) section 3.3 prohibits sharing internal data + code with unsanctioned external systems. Generative AI tools that send code to an LLM are sanctioned external systems — but only when properly governed. This module is the framework for thinking about AI dev tool governance at a regulated bank.

---

## 1. The four risk dimensions

| Dimension | Question | Mitigation |
|---|---|---|
| **Data leakage** | Does our code/data leave the network? Where does it go? Retained how long? | Content exclusion; zero-day retention contracts; BYOK |
| **IP risk** | Could the AI suggest code that's IP-encumbered? | IP indemnity contract; default-on copyright filters |
| **Quality** | Could AI introduce bugs / security vulnerabilities into prod? | Mandatory human review; CI catches; CodeQL scans |
| **Compliance** | Does the use of AI satisfy regulatory expectations (SR 11-7, fair lending)? | Audit log of usage; same controls as human-written code |

---

## 2. The data-leakage matrix

For each AI tool you consider, ask:

| Question | Copilot Business | Copilot Enterprise | Claude Code Enterprise | Cursor Business |
|---|---|---|---|---|
| Is my code sent to a third party? | Yes (GitHub/MS) | Yes (GitHub/MS) | Yes (Anthropic) | Yes (Cursor + provider) |
| Is it retained? | No (zero-day) | No | Configurable (default short) | No (Privacy Mode) |
| Is it used to train future models? | No | No | No (default) | No |
| Can I exclude specific paths? | Yes (content exclusion) | Yes | Yes | Limited |
| SOC 2 Type II? | Yes | Yes | Yes | Yes |
| HIPAA available? | No | No | Yes (Enterprise) | No |
| BYOK? | No | Limited | Yes (Enterprise) | No |

For a bank, you want:
- ✓ Zero-day retention
- ✓ No training on customer data
- ✓ Content exclusion configurable at org level
- ✓ SOC 2 Type II (table stakes)
- ✓ Audit logs of every interaction

---

## 3. Content exclusion patterns

Configure at org level (in each tool's admin console):

```
# Always exclude — never sent to AI
secrets/
**/.env
**/.env.*
**/credentials.json
**/*-private-key*
**/keystore.*
data/customer/
data/pii/
compliance/audit/
models/proprietary/
```

For Capital One: probably extends to all of `customer/`, anything containing `PII`, anything in regulated-data dirs (CCPA / GDPR / SOC 1 paths).

Test the exclusion by deliberately placing a token-shaped string in an excluded path; verify the AI tool doesn't surface it.

---

## 4. The "AI-generated code" attribution question

When AI generates a chunk of code that you commit:
- The commit is YOURS (your name, your signed commit).
- You are responsible for the diff.
- The code goes through normal review (CODEOWNERS, status checks, etc.).
- The fact that AI assisted doesn't change the audit story — you accepted the suggestion.

What you should NOT do:
- ❌ Mention Claude / Copilot in commit messages (no point; and your team's commit-style memory likely says don't)
- ❌ Skip review because "it's AI-generated, must be fine"
- ❌ Bypass CI/security checks
- ❌ Commit AI-suggested code you don't understand

What you SHOULD do:
- ✓ Treat AI suggestions like a junior pair-programmer's input — review carefully
- ✓ Verify behavior (run tests, check edge cases)
- ✓ Edit to your team's style + naming conventions
- ✓ For sensitive code (security, model logic, IaC), apply extra scrutiny

---

## 5. Governance program structure (the Capital One pattern, inferred)

Capital One reportedly has a **Developer Experience & Innovation (DEI)** team responsible for enterprise AI dev tooling. Pattern:

1. **Tool approval process** — DEI evaluates new AI dev tools against the data + compliance criteria. Approved list published internally.
2. **License procurement** — central, not per-team.
3. **SSO + audit log integration** — every approved tool integrates with C1's IdP + SIEM.
4. **Org policy enforcement** — content exclusion + retention + RBAC configured org-wide.
5. **Training** — annual mandatory training on responsible AI use.
6. **Feedback channel** — engineers report wins / concerns / suggestions.
7. **Quarterly review** — ROI, incidents, evolving threat landscape.

---

## 6. The Code of Conduct overlay

Capital One's Code of Conduct (publicly available, section 3.3) covers data handling. Paraphrasing the spirit: don't put confidential data in places it doesn't belong.

For AI tools: an approved tool with the right governance IS a sanctioned place. An unapproved tool (random ChatGPT, personal Claude account, free Cursor) IS NOT. The distinction is governance, not technology.

Implications:
- You can use Copilot Business/Enterprise + Claude Code Enterprise (if approved).
- You CANNOT paste C1 code into ChatGPT.com (no DPA, no content exclusion, retained by default).
- You CANNOT use a personal Claude.ai account for work code (same).
- For AI tools your team wants but DEI hasn't approved — make the request through DEI; don't go rogue.

---

## 7. The audit trail for AI usage

Every approved tool should provide audit logs:

| Tool | Audit log capability |
|---|---|
| Copilot Business+ | Per-user prompt counts; aggregated metadata. Detailed per-event log via API. |
| Claude Code Enterprise | Per-session log; per-prompt log (with retention setting); export to SIEM |
| Cursor Business | Per-user usage; admin console |

Stream to your central SIEM. Set up alerts for:
- Excessive usage by single user (potential automation abuse)
- Usage from unexpected IPs (account compromise indicator)
- Failed authentications (credential stuffing)

For SR 11-7 (model-impacting code), the audit trail for AI involvement may be reviewed in audit.

---

## 8. The training-data leakage worry

LLM providers say they don't train on your data. But:
- Content sent during inference is processed (may be logged for abuse detection).
- Bug in their system could log + leak.
- Subpoena could force disclosure of training data.

Mitigation:
- BYOK where available (your encryption key, they can't decrypt without it).
- Self-hosted models for the most sensitive code (Capital One could run open-source models like Llama / Qwen / Code-Llama on their own infra).
- Content exclusion for the absolute most sensitive (PCI auth code, customer data handlers).

Capital One reality: probably uses self-hosted models for some use cases (e.g., internal Capital One Software products like Eno may use them); commercial Enterprise tiers for productivity tools.

---

## 9. The interview answer

When asked: "How would you roll out AI dev tools at a bank?"

> "Three things: contracts, controls, culture. Contracts: SOC 2 Type II minimum, zero-day retention, no training on our data, IP indemnity, configurable HIPAA/BYOK if needed. Controls: SSO + SCIM + audit log streaming to SIEM; content exclusion at the org level for sensitive paths; admin-managed approved list. Culture: human review of every AI-generated diff is non-negotiable; training annually; clear escalation path for new tools. Capital One's DEI team owns this for the org; I'd partner with them to roll it out to my team responsibly."

The bad answer: "Copilot is great, let's give everyone access."

The bad answer's bad answer: "AI is risky, ban it."

---

## 10. Cross-references

- GitHub Copilot in depth → [module 53](53_ai_copilot.md).
- Claude Code in enterprise → [module 54](54_ai_claude_code_enterprise.md).
- Audit log streaming → [module 36](36_compliance_sso_scim_audit.md).
- SR 11-7 compliance posture → [module 37](37_compliance_sr117_audit.md).
- Capital One DEI team + open-source AI tooling → [module 56](56_capital_one_devops_deep.md).
