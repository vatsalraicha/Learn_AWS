# Quiz — Module 17 (Security, Privacy & Auditing)

## Recall

1. What does Vec2Text demonstrate, and what's the headline recovery rate?
2. Three production-ready defenses against embedding inversion.
3. Federated RAG vs DP-RAG vs TEE — pick a use case for each.
4. What does "counterfactual RAG" add to vanilla retrieval traces?

## Apply

5. You're building RAG over employee performance reviews (highly sensitive). Vector DB will be cloud-hosted. Outline the security layering.
6. List the audit log fields you'd retain for regulated workloads.
7. Embedding inversion attack vectors: name three paths an attacker could exploit.

## Diagnose

8. Your security team flags the vector DB as "leaking source data." What's the theoretical basis and what's a fix that doesn't require rearchitecting?
9. A regulator asks "show me why the model decided X." Your team can show retrieved chunks and the prompt. Why is that insufficient and what's missing?

## Defend

10. Argue "treat embeddings of sensitive data with the same protection as the source data."
11. Defend the operational complexity of cache-invalidation-on-corpus-update over a simple TTL approach for healthcare RAG.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. Vec2Text shows that embedding vectors leak the original text. Specifically: **92% exact recovery of 32-token text inputs from their embeddings**, including PII like names from clinical notes. Counters the assumption that embeddings are "lossy enough" to be safe.
2. (a) Don't expose raw vectors to clients (architectural). (b) Encrypt embeddings at rest with the same key-management as source data. (c) Add Gaussian noise (mild defense; modern attacks adapt). (d) Concept-aware obfuscation (mask sensitive concepts before embed). (e) Differential privacy for strongest formal guarantee.
3. **Federated RAG:** multi-org collaboration where data can't be centralized (cross-hospital research). **DP-RAG:** when you need a formal `(ε, δ)` privacy guarantee for regulatory or research purposes. **TEE / confidential compute:** when running on untrusted cloud and need hardware-attested isolation.
4. Counterfactual RAG asks "if we'd retrieved a different chunk, would the answer change?" Vanilla traces show what happened; counterfactual analysis shows which chunks were *load-bearing* — true causal attribution per claim. Audit-grade.
5. (a) Encryption at rest (vector DB). (b) Strict ACL: per-employee or per-manager scoping at query time. (c) Self-host the vector DB or use a vendor with explicit DPA covering this data class. (d) Audit log with retention. (e) Don't expose raw vectors to clients. (f) Consider federated retrieval if performance reviews shouldn't centralize.
6. trace_id, timestamp, user_id_hash, query_text_hash, embedder_version, retriever_config, retrieved_doc_ids + scores + ranks, reranker_version, prompt_template_version, prompt_tokens, llm_model_version, response_text_hash, citations + verdicts, abstain_reasons, retention_until.
7. (a) Steal the vector DB (network breach, exposed cloud credentials). (b) Steal a few (text, vector) pairs and use ALGEN-style alignment to invert any embedding from that embedder. (c) Insider with legitimate read access exfiltrates vectors. (d) Embedding API logs leak embeddings, attacker invertes them.
8. **Theoretical basis:** Vec2Text and successor attacks (ALGEN, ZSinvert) can reconstruct text from embeddings. The vector DB is functionally equivalent to a leak of the source text. **Fix without rearchitecting:** encrypt the vector DB at rest, restrict read access to a small allowlist of services (not human users or analytics), audit access. Don't expose vectors via any user-facing API.
9. Insufficient because: (a) doesn't show *which* claim came from *which* span. (b) doesn't show counterfactual — "if we hadn't had chunk X, would the answer differ?" (c) doesn't show reranker scores or stage-by-stage decisions. **Missing:** claim-level citations with span pointers, counterfactual replay capability, full per-stage audit trail with versioned components.
10. (a) Vec2Text-class attacks demonstrate embeddings recover ~92% of text. (b) An "embedding leak" is functionally equivalent to a source-data leak. (c) The threat model of vector DBs (often less hardened than primary databases) is a weakness, not a strength — they're often "secondary" infrastructure with less rigorous controls. (d) The simplest mental model — "vectors = compressed text" — drives correct decisions across encryption, access control, and logging.
11. (a) Healthcare answers must be current. A stale answer about a deprecated treatment can harm patients. (b) TTL-based invalidation gives stale data within the TTL window. For ICU-related guidance, even hours-stale is unacceptable. (c) Dependency-tracking (cached response → which chunks supported it → invalidate when those chunks change) gives correctness, not just "stale-but-bounded." (d) The complexity is a one-time engineering cost vs ongoing patient-safety risk. (e) Required for regulatory compliance — HIPAA audits will ask "did your system serve out-of-date guidance?"

</details>
