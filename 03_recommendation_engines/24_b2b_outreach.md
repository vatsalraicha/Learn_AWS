# Module 24 — B2B & Outreach Startups

> B2B recommenders look superficially different from consumer recsys but the math is the same: retrieval, ranking, re-ranking. The differences are about **data scarcity** (a B2B buyer appears once in their lifetime), **high stakes per prediction** ($200K SDR salary), and the recent revolution of **LLMs as feature engineers**.

---

## 1. The four B2B differences

1. **Cold start everywhere.** A B2B buyer may appear once. There's no 100-event session.
2. **Tiny positive sets.** A "conversion" is a closed-won deal, not a click. Datasets are 100× smaller than consumer recsys.
3. **High value per prediction.** A wrong consumer rec costs a missed click. A wrong B2B "next-best-account" can waste an SDR's quarter.
4. **LLMs are the new feature engineers.** Cold-email personalisation, intent classification, account research that used to be manual SDR work is now a vector-search-plus-LLM-rerank pipeline.

The result: **gradient-boosted trees** (LightGBM, XGBoost, CatBoost) dominate, not deep models. Modern stacks use embeddings for retrieval and trees for ranking.

---

## 2. LinkedIn Sales Navigator

Surfaces "Lead Recommendations" and "Account Recommendations" inside saved searches and territories.

ML stack (per LinkedIn engineering posts):
- **Two-tower retrieval** — seller's saved-lead history + book of business vs candidate leads. In-batch negatives.
- **GBDT ranker** (XGBoost-family, "Quasar" and FastTree variants). Features: title similarity, company similarity, seniority match to converted leads, geography, mutual-connection count, recency.
- **GNN-derived features** — LinkedIn's economic graph embeddings (LiGNN successor).
- **InMail accept-rate prediction** — predicts P(accept). Subject lines / openers LLM-drafted.

Signals unique to LinkedIn: job changes (3-4× more likely to engage with prior vendor), mutual second-degree connections, Skills graph proximity.

---

## 3. The B2B "intent data" ecosystem

### 3.1 Bombora — Company Surge

~5,000 publisher websites in a co-op. Per (company, topic) baseline consumption tracked over 12 weeks. Surge = 7-day window > 2σ above baseline. Output: per-(company, topic) score 0-100.

### 3.2 6sense

Bidstream + Bombora-style co-op + de-anonymising your site traffic. **Buying-stage prediction** is the secret sauce — Markov-chain or neural-sequence model over recent signals predicts Awareness / Consideration / Decision / Purchase. Output: **6QA** (6sense Qualified Account) binary flag.

### 3.3 Demandbase

Strongest at IP-to-account resolution. Account Intelligence combines firmographics + intent + web engagement + ad exposure.

### 3.4 G2 Intent

Buyer behavior on G2 product pages — comparison views, category browsing, review reading. High signal because the visitor is explicitly evaluating software.

### 3.5 Aggregation in a buyer's stack

```
Bombora topic surge ──┐
G2 product views ─────┤
LinkedIn ad clicks ───┼──► weighted sum or LightGBM ──► Intent Score
6sense stage ─────────┤
Your own web visits ──┘
```

---

## 4. Lookalike scoring at B2B

The B2B equivalent of Facebook Lookalike Audiences:

1. Define **seed set** — closed-won customers, last 12 months.
2. Featurise: industry (NAICS/SIC), employee count, revenue, tech stack (BuiltWith / HG Insights / Wappalyzer), funding stage, growth rate, geography, hiring velocity.
3. Train binary classifier: seeds = positives, random universe sample = negatives. **LightGBM standard**; one-class SVM or isolation-forest when negatives are noisy.
4. Score the entire universe (5-20M companies). Rank.
5. Re-weight by TAM filters (geo, size band, exclusions) and freshness (recent funding, hiring).

Off-the-shelf: Apollo Look-alike Search, ZoomInfo Similar Companies, 6sense Lookalike Account Discovery, Demandbase Account Identification. $30K-$150K/yr.

---

## 5. The outbound automation stack

The 2024-2026 pattern:

```
Apollo / ZoomInfo (list)
        ▼
   Clay (enrichment + LLM research per row)
        ▼
   Smartlead / Instantly (sending — inbox warmup, deliverability)
        ▼
   CRM (HubSpot / Salesforce)
```

Clay's ML is minimal; it's an orchestration layer for LLM calls. The pattern:

1. For each row, run N enrichment steps (fetch company site, LinkedIn profile, recent funding, recent jobs).
2. Pass enriched row to LLM with templated personalisation prompt.
3. Run a quality classifier on output (filter hallucinations, irrelevance, brand-risk).
4. Send.

---

## 6. The cold email recipe — what every gen-AI outbound tool does

```python
def personalise(contact, company, product):
    web_excerpt   = scrape_and_summarise(company.website, max_tokens=500)
    linkedin_bio  = fetch_linkedin(contact.url)
    recent_news   = news_api(company.name, last_days=30)
    job_postings  = scrape_jobs(company.id, relevant_titles)

    prompt = TEMPLATE.format(
        contact=contact, company=company,
        web_excerpt=web_excerpt, bio=linkedin_bio,
        news=recent_news, jobs=job_postings,
        product_pitch=product.value_props,
    )

    candidates = llm.generate(prompt, n=5, temperature=0.7)
    scores = reply_rate_model.predict(candidates, contact_features)
    best = candidates[argmax(scores)]

    if brand_safety_classifier(best) < THRESHOLD:
        return None  # fall back to template
    return best
```

The reply-rate model + brand-safety classifier are what separate an LLM toy from a real recsys.

### 6.1 Reply-rate predictor

Fine-tuned `sentence-transformers` model (MiniLM or BGE) for email body + subject embeddings; small MLP head with contact/company features. Trained on (email_text, sent_at, contact_features) → reply_within_72h. Logloss objective. Production teams report 0.65-0.75 AUC.

### 6.2 Deliverability scoring

Distinct from reply prediction. Features: sender-domain reputation (SenderScore, Google Postmaster), inbox-warmup state, content-spam-score (SpamAssassin + learned overlay), per-mailbox bounce rate.

---

## 7. CRM-side ML

### 7.1 Salesforce Einstein / Agentforce

- Einstein Lead Scoring — auto-trained per-org GBDT on `Lead.IsConverted`.
- Einstein Opportunity Scoring — per-org GBDT for P(close).
- Einstein Account Insights — NLP for news / events.
- **Agentforce** (2024-26) — agentic LLM layer with the Einstein Trust Layer for grounding.

### 7.2 HubSpot Breeze AI

- Predictive Lead Scoring — GBDT, auto-trained per portal.
- Breeze AI — LLM-powered assistant; drafts emails, summarises records.

### 7.3 Microsoft Dynamics 365 Sales

- Sales Insights — relationship-health, opportunity scoring, predictive forecasting.
- Copilot for Sales — GPT-4-class LLM over CRM.

---

## 8. Sales enablement content — Highspot, Seismic

"Netflix for sales decks." Recommendation problem: a rep is preparing for a meeting; show the right case study, deck, one-pager.

Highspot's "Recommended Content":
- Content tags (vertical, persona, stage).
- Past-rep usage signals (CF across reps).
- Win-rate-of-content-when-used.
- LLM-driven semantic match between meeting context and content metadata.

---

## 9. Recruiting / talent

- **Indeed**: two-tower job ↔ resume retrieval; XGBoost-then-deep ranker for SERP; sequence model over user search/apply history.
- **hireEZ / SeekOut / Eightfold**: sources from public web + 800M+ profile graph; ranks fit-to-JD using BERT-class semantic similarity + filters.
- **LinkedIn Recruiter**: same graph as Sales Navigator + recruiting-specific signals (open-to-work, skill endorsements, past-employer similarity to hiring company, InMail acceptance history).

---

## 10. The canonical B2B startup recsys stack

```
Postgres / Snowflake / BigQuery (source of truth)
        │
        ├──► dbt (transformations) ────► Feature tables (offline)
        │                                     │
        │                                     ▼
        │                                Feast (offline + online)
        │                                     │
        ▼                                     ▼
   sentence-transformers (encode text)   LightGBM ranker
        │                                     │
        ▼                                     │
   Pinecone / Weaviate / pgvector             │
        │                                     │
        └────────────────┬────────────────────┘
                         ▼
                    FastAPI service
                         │
                         ▼
                  Cloudflare / Vercel / AWS ALB
```

### 10.1 The "vector search + LLM rerank" pattern

1. **Retrieve** top-K (50-200) from a vector index using a cheap embedding (`bge-small-en`, `text-embedding-3-small`).
2. **Rerank** top-K with a cross-encoder (Cohere Rerank, Voyage rerank-2) or LLM (Claude/GPT).
3. **Apply business rules** (recency boost, dedup by account, blocklist).
4. **Return top-N**.

p99 ballpark: 200-400ms for a 50-candidate Cohere rerank, 800-1500ms for a Claude rerank.

### 10.2 Why startups skip deep learning

1. **Data volume**: thousands to low-millions of labels, not billions.
2. **Talent cost**: one LightGBM-fluent MLE is enough; deep recsys needs MLE + infra-MLE.
3. **Latency**: 100ms LightGBM fits anywhere; deep needs GPU + embedding caches.
4. **Interpretability**: SHAP on LightGBM is one line.
5. **Cold-start hostility**: deep recsys needs history; B2B doesn't have it.

Crossover where startups *do* go deep: usually >10M MAUs *or* rich in-product event sequences (Notion, Linear, Figma).

---

## 11. Sanity check

1. Why does a B2B recsys typically use LightGBM rather than DLRM?
2. The Clay-style "personalisation at scale" pattern adds a quality classifier after the LLM call. What does this defend against?
3. Intent data from Bombora, 6sense, G2 are usually aggregated in a buyer's stack via weighted sum or LightGBM. What's the alternative your team should consider in 2026 given the data scale?
4. A B2B startup wants to add an "AI cold email" feature without burning customer reputation. Name two ML components that gate sending.
5. Sales enablement (Highspot-style) ranks decks by "win-rate-of-content-when-used." What's the causal-inference problem hiding in this signal?
