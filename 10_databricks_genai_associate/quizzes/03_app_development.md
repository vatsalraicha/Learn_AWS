# Quiz 03 — Application Development (30%, 41 Qs)

> Largest quiz — matches Section 3's exam weight. Take cold. ~2 min/Q. Maps to **Modules 05–09**.

---

## Recall

1. Define the difference between `mlflow.pyfunc.ChatAgent` and `mlflow.pyfunc.ResponsesAgent`.
2. Which framework wraps your LangChain / LangGraph / vanilla agent code for governed deployment on Databricks?
3. Where do Unity Catalog Function tools run when called from an agent?
4. Which `mlflow.langchain` call enables automatic tracing of LangChain chains?
5. What does Lakeguard sandbox limit?
6. What's the SQL function for querying a Vector Search index from a SQL statement?
7. What's the recognition signal that distinguishes Agent Bricks from Agent Framework in an exam scenario?
8. List the three MCP server integration types.
9. Name the new Databricks surface that lets agents retrieve from structured data via natural-language SQL.
10. Which of these built-in MLflow judges require ground truth: Relevance, Groundedness, Correctness, Safety?

## Apply

11. You're building a customer-support agent that needs both policy doc QA and recent claim DB lookups. Which Agent Bricks variant fits?
12. Your prompt asks for JSON output AND a paragraph explanation. Which problem is likely?
13. The agent's tool description reads: "Returns data." Why doesn't the LLM call it correctly?
14. You want SME annotations on prod traffic. Which Databricks surface auto-provides this UI?
15. Build a chain spec: top-10 from `cat.indexes.x_v1`, hybrid, prompt `cat.prompts.faq@production`, LLM `databricks-llama-3-3-70b-instruct`. Write the high-level pseudocode for the LangChain wiring.
16. A user asks "what's my last cardiology visit's prescribed dosage?" Best pattern?
17. The agent's retrieval miss rate is high on multi-hop questions like "What tier is my Lipitor + what's my copay?" Which pattern?
18. You need to extract `{vendor, date, amount}` from 5M invoices. Pick between `ai_extract` SQL function vs Agent Bricks Information Extraction — what's the deciding question?
19. The agent calls a UC function as a tool. The endpoint deploys, but tool calls fail with `PERMISSION_DENIED: Cannot access Spark Connect`. Diagnosis?
20. Which prompt-engineering technique reliably constrains output to a known schema, ranked above few-shot?

## Diagnose

21. The Llama 3.3 70B agent never picks the `get_member_eligibility` tool, even when relevant. The function's `COMMENT` is empty. Fix?
22. Tracing UI shows the retriever step but no LLM step. The chain ran end-to-end. What's missing in the tracing config?
23. Symptom: the chain works locally but at serving, retrieval returns "PERMISSION_DENIED on VS index." Resources are declared correctly. Other cause?
24. After upgrading to MLflow 3, your old `mlflow.pyfunc.PythonModel`-based agent no longer renders properly in the Review app. Suggested change?
25. The chain's retrieved context is dominated by boilerplate footers. The reranker doesn't help. Two upstream fixes?
26. The LangGraph agent loops infinitely between LLM and tool nodes. Suspected cause and fix?
27. Hybrid search returns the same top-5 as pure ANN. Why no lift, and what to check?

## Defend

28. Argue why you'd build a custom LangGraph supervisor over an Agent Bricks Multi-Agent Supervisor for a regulated finance use case.
29. Defend storing prompts in MLflow Prompt Registry rather than a Delta table with a timestamp column.
30. Justify picking ResponsesAgent over ChatAgent for a new multimodal voice + text agent.
31. Argue against retrieving top-5 directly from Vector Search with no rerank for production.

## Code-spotting

32. Which line is wrong?
   ```python
   mlflow.set_registry_uri("databricks")  # line A
   mlflow.pyfunc.log_model(
       artifact_path="agent",
       python_model=MyAgent(),
       registered_model_name="my_agent",  # line B
   )
   ```
33. The chain works locally but `predict` calls return 503 on the deployed endpoint. The user passed `messages` as a list of dicts. Which schema mismatch is plausible?

## [Multi-select]

34. **[select TWO]** When wiring an external MCP server that needs an API key, which steps belong to the exam-correct integration?
   (A) Hardcode the key in the agent code
   (B) Store the key in Databricks Secrets
   (C) Reference the secret in MCP config via `{{secrets/scope/key}}`
   (D) Make the agent fetch the key from a public endpoint at boot
   (E) Disable AI Gateway for the agent to simplify auth

35. **[select TWO]** Which prompt techniques reduce hallucination in RAG agents?
   (A) "Be more accurate" appended to the prompt
   (B) "Answer ONLY using provided context; if context is insufficient, say so"
   (C) Removing few-shot examples
   (D) Forcing citation tags like `[S1]` after each claim
   (E) Increasing model temperature

36. **[select THREE]** Built-in MLflow judges that do **NOT** require ground truth.
   (A) Relevance
   (B) Groundedness
   (C) Correctness
   (D) Safety
   (E) Similarity

37. **[select TWO]** Patterns for multi-step / multi-hop retrieval in an agent.
   (A) Single similarity_search call with high `num_results`
   (B) LangGraph state machine with iterative retrieval
   (C) Multi-query retriever generating reformulations
   (D) Pure prompt engineering with chain-of-thought only
   (E) Lower the chunk size and rerun

## Scenario

38. The product team says: "Customer-facing agent over our policy manuals. Internal team has no LangChain experience. SLA: 99% uptime. Quality bar: ≥ 0.85 groundedness. Volume: 5 QPS sustained. Cost target: minimize." Which build path?
39. Marketing wants a quick PoC of a content-generation agent over their product catalog within a week. Engineering team is unavailable. Which path?
40. The legal team wants every output to cite chunk IDs. Which prompt-engineering pattern + which judge would you wire?
41. The chain returns "I don't have enough information" 40% of the time even on questions clearly answerable from the corpus. Top three diagnostic steps?

---

## Answers

1. `ChatAgent` matches OpenAI ChatCompletion (messages in, message out); `ResponsesAgent` matches OpenAI Responses API (richer item types: text, tool_call, tool_result), multi-modal-friendly. → Module 08
2. **Mosaic AI Agent Framework.** Wraps your code; does not replace LangChain/LangGraph. → Module 08
3. **Serverless generic compute (Spark Connect serverless)**, sandboxed by **Lakeguard**. → Module 08
4. **`mlflow.langchain.autolog()`**. → Module 07
5. CPU time, memory, wall-clock, local code execution, network egress beyond approved. → Module 08
6. **`vector_search(index_name, query_text => ..., ...)`** in SQL (LATERAL VIEW or scalar). → Module 06
7. "minimize maintenance / auto-optimize / domain-specific quality without manual tuning" → **Agent Bricks**. "fine control / custom tools / specific framework" → **Agent Framework**. → Module 09
8. Managed, External, Custom. → Module 11
9. **Genie Spaces.** → Module 08
10. **Correctness** requires ground truth. The other three do not. → Module 14
11. **Multi-Agent Supervisor.** Routes between Knowledge Assistant (policy QA) and Genie Space (claims SQL). → Module 09
12. **Format drift** — the explanation leaks around the JSON and breaks parsing. Separate calls or use a unified schema with an `explanation` field. → Module 05
13. **Bad tool description.** LLM picks tools by reading the description/COMMENT; "Returns data" gives no decision signal. → Module 08
14. **The Review app** auto-provisioned by `databricks.agents.deploy()`. → Module 08
15. ```python
    retriever = DatabricksVectorSearch(endpoint="vs-prod",
        index_name="cat.indexes.x_v1",
        embedding=DatabricksEmbeddings(endpoint="databricks-bge-large-en"))\
      .as_retriever(search_kwargs={"k":10, "query_type":"HYBRID"})
    prompt = PromptTemplate.from_template(
      mlflow.genai.load_prompt("cat.prompts.faq@production").template)
    llm = ChatDatabricks(endpoint="databricks-llama-3-3-70b-instruct")
    chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm
    ``` → Module 07
16. **Feature lookup via agent tool.** Data is per-record dynamic; expose `member_prescriptions` via Online Table + UC function. NOT RAG, NOT fine-tune. → Module 01
17. **Multi-hop retrieval via LangGraph agent** (or Agent Framework with retrieval tool). One pass for tier, second pass for copay. → Module 07
18. **Cardinality of iteration.** One-shot well-defined schema → `ai_extract`. Will need ongoing iteration with eval feedback + auto-tuning → **Information Extraction Brick**. → Module 09
19. **Workspace lacks serverless generic compute** enabled or the calling identity doesn't have access. UC function tools require Spark Connect serverless, not SQL warehouses. → Module 08
20. **Structured-output / function-calling API** (provider-native JSON schema constraint). Most reliable ladder rung above few-shot. → Module 05
21. Add a substantive `COMMENT` describing **when to call** the tool: "Looks up a member's eligibility status. Use when the user asks about coverage start dates or active plans." → Module 08
22. **`mlflow.langchain.autolog()`** not called (or `mlflow.openai.autolog()` for direct OpenAI), or LLM call is outside the LangChain runnable. → Module 07, 14
23. The **endpoint's service principal** does not actually have `USE_INDEX` grant on the new index — maybe the index was rebuilt under a new name and the resources list points to old, or grants weren't applied after a UC migration. → Module 07
24. **Wrap in `mlflow.pyfunc.ChatAgent` (or `ResponsesAgent`)** — these are the chat-shaped base classes the Review app expects. → Module 08
25. (a) **Pre-chunk filter** to strip boilerplate (regex / structure-aware HTML parser). (b) **Source filter at indexing** to drop pages that are pure boilerplate. → Module 03
26. **Missing termination condition** in the conditional edge. The graph keeps deciding "tools" because the LLM keeps emitting tool_calls. Add a `step_count` guard or a `should_continue` rule that stops on N consecutive tool calls. → Module 08
27. (a) BM25 index didn't build (check sync state). (b) Embedding model already captures the lexical signal (e.g., the model is fine-tuned on this domain). (c) Top-5 is below the noise floor where fusion differs. Lift comes more at top-20 or top-50. → Module 06
28. Regulated finance needs per-step audit, custom validation, deterministic routing, and human-reviewed prompt changes. Bricks abstracts routing prompts. LangGraph supervisor gives explicit branches the compliance team can review; logs every state transition; tools are UC-governed. → Module 09
29. Prompt Registry ties prompts to UC ACLs, gives **aliases** for atomic gated promotion across environments, integrates with MLflow eval runs (you can compare prompt v7 vs v8 head-to-head), and provides clean rollback. Delta+timestamp loses the alias semantics, has no per-version eval link, and requires custom rollback code. → Module 05, 11, 14
30. ResponsesAgent's item types model tool calls and multi-modal items natively. Voice → text → tool_call → text response sequences fit ResponsesAgent's schema cleanly; ChatAgent forces everything into one `content` string. → Module 08
31. Top-K=5 ANN-only misses borderline-relevant chunks the reranker would promote. Over-retrieve (50) + cross-encoder rerank to 5 has higher precision per chunk delivered to the LLM, which directly raises Groundedness scores. The cost (one reranker call) is well worth the quality lift. → Module 04, 06
32. **Both lines have issues.** Line A: should be `"databricks-uc"`, not `"databricks"`. Line B: `registered_model_name` must be three-level UC (`cat.schema.my_agent`), not unqualified. → Module 07
33. The agent inherits `ChatAgent` (or `ResponsesAgent`); calling code is sending an OpenAI-Chat-style request body. If the chain was wrapped as `ResponsesAgent`, the input schema differs and a 503 / 422 results. Match the base class to the input schema. → Module 08
34. **(B) + (C).** Sample Q9 pattern: secrets stored, referenced via `{{secrets/scope/key}}`. → Module 11
35. **(B) + (D).** Explicit grounding constraint + citation tags both pressure the model to stay sourced. (A) too vague. (C) removes a reliability lever. (E) increases hallucination. → Module 05
36. **(A) Relevance, (B) Groundedness, (D) Safety.** Correctness and Similarity compare against expected → need ground truth. → Module 14
37. **(B) LangGraph state machine** and **(C) Multi-query retriever.** (A) raising K alone doesn't decompose the question. (D) CoT can't fetch new data. (E) shrinking chunks doesn't help missing-hop. → Module 07
38. **Agent Bricks Knowledge Assistant.** Internal team lacks LangChain skill; cost-minimize + quality SLO acceptable for managed RAG; 5 QPS is well within Bricks endpoint capacity. → Module 09
39. **Agent Bricks Knowledge Assistant.** Fastest path to a working PoC over docs without engineering involvement. → Module 09
40. **Pattern:** explicit `[S\d+]` citation tag instructed in system prompt + few-shot examples showing citations. **Judge:** custom scorer pattern-matching `[S\d+]` regex; also `Groundedness` for semantic check. → Modules 05, 14
41. (a) Retrieval miss rate too high → over-retrieve + rerank, hybrid search ON. (b) System prompt too conservative — re-tune to refuse only when truly unsourced. (c) Chunks too small or boilerplate-dominated → revisit chunking + pre-filter. → Modules 03, 04, 05, 06
