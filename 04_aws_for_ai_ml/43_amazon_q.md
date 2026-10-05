# Module 43 — Amazon Q Family

> **What this is:** Q Developer (rebranded from CodeWhisperer), Q Business (enterprise assistant), Q Apps, Q in QuickSight, Q in Connect. The Amazon-branded LLM productivity layer.

---

## 1. Q Developer

Rebranded from **CodeWhisperer** in April 2024. The developer assistant:

- **Code generation** in 15+ languages.
- **Agent mode**: `/dev` (feature implementation), `/transform` (Java upgrade), `/test` (test generation), `/doc` (documentation), `/review` (code review).
- **Security scanning** inline.
- **IDE plugins** for VS Code, JetBrains, Eclipse, Visual Studio, command line.
- **AWS Console embedded** assistant.

**Pricing:**
- **Free tier** — limited.
- **Pro tier** — $19/user/month.

## 2. Q Business

Enterprise assistant connected to corporate data sources. Conceptually a managed RAG-backed enterprise chatbot.

**Features:**
- **40+ connectors**: Confluence, SharePoint, ServiceNow, Salesforce, Jira, Slack, Teams, GitHub, S3, etc.
- **Identity-aware retrieval** — uses each user's permissions in source systems (not a flat index).
- **Requires IAM Identity Center** (organizational SSO).

**Pricing:**
- **$3/user/month** Lite
- **$20/user/month** Pro (includes Q Apps)

## 3. Q Apps

No-code app builder within Q Business. Create scoped chatbots / assistants for specific business workflows (e.g., "summarize regulatory updates by jurisdiction").

## 4. Q in QuickSight

BI assistant. Natural-language questions translate to SQL/visualizations against your data sources.

- "Show me Q1 revenue by region" → auto-generated chart.
- Embedded in QuickSight dashboards.

## 5. Q in Connect

Contact-center assistant. Real-time agent assistance with relevant articles, suggested responses, customer history summarization. Comparable to Capital One's Generative AI Agent Servicing Tool (which appears to be a custom build, possibly leveraging Q in Connect plus custom).

## 6. Governance

- **Identity-aware** — Q Business retrieval respects source-system permissions per user.
- **Audit logs** to CloudTrail.
- **Tags and chargeback** via Application Inference Profiles (Module 42).
- **No model training on customer data** (explicit policy).

## 7. 2024-2026 changes

- **CodeWhisperer → Q Developer** rebrand April 2024.
- **Q Apps** GA 2024.
- **Q in Connect** GA 2024.
- **Q Business connectors** expanded throughout 2024-2025.

## 8. Pitfalls

- **Q Business connector freshness** — index refresh latency means users see stale data; tune crawler intervals.
- **Connector permission propagation** — if source-system perms aren't synced, users see stale denials.
- **Per-user pricing math** — $20/user × 50,000 employees = $12M/year, a significant line item.

## 9. Capital One lens

- **Q Business** is the natural fit for enterprise knowledge access — likely paired with their tokenization layer (Databolt) for sensitive data.
- **Q Developer** likely standard issue for engineers (or competing with internal/Anthropic-Claude-direct developer assistants).
- **Q in Connect** may underpin parts of the Servicing Tool, though Capital One built a custom system.

## 10. Sanity check

1. What was CodeWhisperer renamed to, and when?
2. What does "identity-aware retrieval" mean in Q Business?
3. What is the IAM Identity Center prerequisite for Q Business?
4. How does Q in QuickSight translate natural language to charts?
5. Per-user pricing at 50k users — what's the annual order of magnitude?

## 11. Cross-references

- **Module 42** — Bedrock (the FM backend Q uses)
- **Module 12** — DataZone (governance overlap)
- **Module 56** — Q cost analysis

## Primary sources

- Q Business / Q Developer docs (archived in downloads/aws_whitepapers/)
- Research report: [`10_genai_on_aws.md`](../../research_inputs/04_aws_for_ai_ml/10_genai_on_aws.md)
