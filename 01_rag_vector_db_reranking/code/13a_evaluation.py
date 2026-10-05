# %% [markdown]
# # Notebook 13A — Evaluation with Claude as Judge
#
# **Pairs with:** [Module 8 — Evaluation](../08_evaluation.md) and [Module 13A — Methodology & Statistics](../13a_eval_methodology_statistics.md)
#
# **What you'll see:**
# 1. **Ragas configured with Claude as judge** (default is OpenAI; we override).
# 2. **DeepEval also with Claude** — the same eval through a different framework, scores differ.
# 3. **The Ragas faithfulness algorithm decompiled** — see the actual claim decomposition.
# 4. **Bootstrap confidence intervals** — measure if a metric difference is real or noise.
# 5. **Position-swap bias mitigation** for pairwise judge comparisons.
#
# **Stack:** anthropic, ragas, deepeval. **No OpenAI.**

# %% [markdown]
# ## Setup

# %%
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

assert os.environ.get("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY must be set in .env"

import sys
sys.path.insert(0, str(Path(__file__).parent / "data"))
from seed_corpus import get_corpus  # noqa: E402

corpus = {c[0]: c[1] for c in get_corpus()}

# %% [markdown]
# ## A small fixed eval set (query, retrieved_context, generated_answer, ground_truth)
#
# In real use you'd curate or synthesize these from your corpus. Here we hand-craft 4 cases
# spanning **good answer**, **partial hallucination**, **off-topic answer**, and **subtle factual error**
# so we can see how each metric reacts.

# %%
EVAL_CASES = [
    {
        "query": "What is our 401k match policy?",
        "contexts": [corpus["hr_001"]],
        "answer": (
            "Acme matches 100% of your contributions up to 4% of your salary, "
            "and the match vests over 3 years (33% / 66% / 100%)."
        ),
        "ground_truth": "100% match up to 4% with 3-year graded vesting.",
        "expected_quality": "good",
    },
    {
        "query": "What is our 401k match policy?",
        "contexts": [corpus["hr_001"]],
        "answer": (
            # Subtle factual error: "50% up to 6%" instead of "100% up to 4%"
            "Acme matches 50% of your contributions up to 6% of salary. "
            "Vesting is immediate."
        ),
        "ground_truth": "100% match up to 4% with 3-year graded vesting.",
        "expected_quality": "factually_wrong_but_fluent",
    },
    {
        "query": "Can a B2B customer get a refund after 30 days for a Q4 2024 purchase?",
        "contexts": [corpus["hr_002"], corpus["hr_003"]],  # mixes Q4 2024 + Q1 2023 (old) policies
        "answer": (
            # Partially-supported: cites the wrong year's policy
            "No, all sales are final after 14 days per policy."
        ),
        "ground_truth": "Q4 2024 policy allows 30 days; the 14-day rule was Q1 2023 (superseded).",
        "expected_quality": "wrong_year_policy",
    },
    {
        "query": "How does HNSW work?",
        "contexts": [corpus["tech_002"]],
        "answer": (
            # Off-topic: ignores the retrieved content
            "Hierarchical clustering builds dendrograms by repeatedly merging the closest pair "
            "of clusters until one remains."
        ),
        "ground_truth": "HNSW is a graph-based ANN with multi-layer structure for long-range hops.",
        "expected_quality": "off_topic",
    },
]

# %% [markdown]
# ## Step 1 — Ragas with Claude as judge
#
# Ragas defaults to OpenAI. To use Claude, wrap `ChatAnthropic` from `langchain-anthropic`
# and pass it via `evaluator_llm` and `embeddings` arguments.

# %%
from langchain_anthropic import ChatAnthropic
from langchain_voyageai import VoyageAIEmbeddings

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas import EvaluationDataset, evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall

claude_judge = LangchainLLMWrapper(
    ChatAnthropic(model="claude-sonnet-4-5", temperature=0.0)
)
voyage_embed = LangchainEmbeddingsWrapper(
    VoyageAIEmbeddings(model="voyage-3-large")
)

# Build Ragas dataset
ragas_data = EvaluationDataset.from_list([
    {
        "user_input": case["query"],
        "retrieved_contexts": case["contexts"],
        "response": case["answer"],
        "reference": case["ground_truth"],
    }
    for case in EVAL_CASES
])

print("Running Ragas evaluation with Claude as judge...")
ragas_result = evaluate(
    dataset=ragas_data,
    metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()],
    llm=claude_judge,
    embeddings=voyage_embed,
    show_progress=True,
)

print("\n=== Ragas results (Claude judge) ===")
df_ragas = ragas_result.to_pandas()
print(df_ragas[["user_input", "faithfulness", "answer_relevancy", "context_precision", "context_recall"]].to_string())

# %% [markdown]
# ## Observations
#
# - **Case 1 (good answer):** all metrics high.
# - **Case 2 (subtle factual error):** faithfulness drops sharply — claims contradict the context.
# - **Case 3 (wrong-year policy):** faithfulness *seems* OK to the older context but context_precision/recall reveal the wrong context was prioritized. Important: faithfulness alone hides this kind of error.
# - **Case 4 (off-topic):** answer_relevancy crashes; faithfulness is also low because answer doesn't reflect retrieved context at all.
#
# **The lesson:** no single metric tells the whole story. The triad together localizes failures.

# %% [markdown]
# ## Step 2 — Decompile Ragas faithfulness ourselves
#
# Module 13A walks through the algorithm conceptually. Now we implement it in 30 lines so
# the score is no longer a black box.

# %%
from anthropic import Anthropic

client = Anthropic()

DECOMPOSE_PROMPT = """Break the following answer into atomic, self-contained statements.
Each statement must be understandable on its own (no pronouns referring to other statements,
no implicit subjects). Output a JSON list of strings.

Answer: {answer}

Output JSON only:"""

JUDGE_PROMPT = """Given the context, decide whether the statement is entailed by it.
Return JSON: {{"verdict": 1 or 0, "reasoning": "..."}}.

Context: {context}

Statement: {statement}

Output JSON only:"""


def decompose_claims(answer: str) -> List[str]:
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": DECOMPOSE_PROMPT.format(answer=answer)}],
    )
    text = msg.content[0].text.strip()
    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)


def judge_claim(statement: str, context: str) -> Tuple[int, str]:
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": JUDGE_PROMPT.format(context=context, statement=statement),
        }],
    )
    text = msg.content[0].text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    obj = json.loads(text)
    return obj["verdict"], obj.get("reasoning", "")


def my_faithfulness(answer: str, contexts: List[str]) -> Tuple[float, List[Dict]]:
    """Our hand-rolled Ragas-style faithfulness."""
    claims = decompose_claims(answer)
    joined_context = "\n\n".join(contexts)
    detail = []
    for c in claims:
        v, why = judge_claim(c, joined_context)
        detail.append({"claim": c, "verdict": v, "reasoning": why})
    score = sum(d["verdict"] for d in detail) / len(detail) if detail else 0.0
    return score, detail


# Run on the 'subtle factual error' case
case = EVAL_CASES[1]
print("\n=== Hand-rolled faithfulness on Case 2 (factually wrong) ===")
score, details = my_faithfulness(case["answer"], case["contexts"])
print(f"Faithfulness: {score:.2f}")
for d in details:
    print(f"  [{d['verdict']}] {d['claim']}")
    print(f"      ↳ {d['reasoning'][:120]}...")

# %% [markdown]
# Now you can see *exactly* which claim was unsupported and why. This level of visibility
# is what production teams need — "0.65 faithfulness" tells you nothing; the per-claim
# verdicts let you debug.

# %% [markdown]
# ## Step 3 — Bootstrap confidence intervals
#
# Module 13A: scores below ~200 samples are statistically unstable. Always report CIs.

# %%
def bootstrap_ci(values: List[float], n_iterations: int = 1000, ci: float = 0.95) -> Tuple[float, float, float]:
    """Returns (point_estimate, lower, upper) of the mean."""
    arr = np.array(values)
    means = []
    for _ in range(n_iterations):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        means.append(sample.mean())
    means = np.array(means)
    alpha = (1 - ci) / 2
    return arr.mean(), float(np.quantile(means, alpha)), float(np.quantile(means, 1 - alpha))


# Apply to the Ragas faithfulness column
faith_values = df_ragas["faithfulness"].dropna().tolist()
mean, lo, hi = bootstrap_ci(faith_values, n_iterations=1000)
print(f"\n=== Bootstrap CI on faithfulness ===")
print(f"Mean = {mean:.3f}")
print(f"95% CI = [{lo:.3f}, {hi:.3f}]")
print(f"Sample size = {len(faith_values)} (much too small for production decisions)")

# %% [markdown]
# **Key insight:** with only 4 samples the CI is huge (often [0.0, 1.0]). You'd never
# ship a pipeline change with this little data. Production teams want **N ≥ 200** for
# meaningful CIs, **N ≥ 500** for high-stakes decisions.
#
# Try this: increase EVAL_CASES to 50+ via Ragas's synthetic test-set generator
# (`from ragas.testset import TestsetGenerator`). Watch the CI shrink as N grows.

# %% [markdown]
# ## Step 4 — Position-swap bias mitigation
#
# Pairwise LLM-judge comparisons suffer from position bias. Mitigation: ask in both orders, accept the verdict only if both agree.

# %%
PAIRWISE_PROMPT = """Compare these two answers to the same question. Pick the better one.

Question: {q}

Answer A: {a}

Answer B: {b}

Reply with JSON: {{"winner": "A" or "B" or "tie", "reasoning": "..."}}
Output JSON only."""

def pairwise_compare(question: str, answer_a: str, answer_b: str, model: str = "claude-sonnet-4-5") -> str:
    msg = client.messages.create(
        model=model,
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": PAIRWISE_PROMPT.format(q=question, a=answer_a, b=answer_b),
        }],
    )
    text = msg.content[0].text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    return json.loads(text)["winner"]


def position_swap_compare(question: str, answer_x: str, answer_y: str) -> str:
    """Run twice with sides swapped. Only declare a winner if both runs agree."""
    fwd = pairwise_compare(question, answer_x, answer_y)        # X=A, Y=B
    rev = pairwise_compare(question, answer_y, answer_x)        # Y=A, X=B
    # Translate reverse verdict back to X/Y space
    rev_translated = "X" if rev == "B" else ("Y" if rev == "A" else "tie")
    fwd_translated = "X" if fwd == "A" else ("Y" if fwd == "B" else "tie")
    if fwd_translated == rev_translated:
        return fwd_translated
    return "inconsistent"  # the judge has position bias on this pair


# Demo
case_good = EVAL_CASES[0]["answer"]      # correct 401k answer
case_wrong = EVAL_CASES[1]["answer"]     # subtly wrong 401k answer
question = EVAL_CASES[0]["query"]

print("\n=== Position-swap comparison ===")
verdict_naive = pairwise_compare(question, case_good, case_wrong)
print(f"Naive (single-direction): winner={verdict_naive}")
verdict_swap = position_swap_compare(question, case_good, case_wrong)
print(f"Position-swap: winner={verdict_swap}")
print("If 'inconsistent', the judge has position bias on this pair and the result is unreliable.")

# %% [markdown]
# ## Things to try next
#
# 1. **DeepEval comparison** — same cases through DeepEval, expect different scores:
#    ```python
#    from deepeval.metrics import FaithfulnessMetric
#    from deepeval.test_case import LLMTestCase
#    from deepeval.models import AnthropicModel
#    judge = AnthropicModel("claude-sonnet-4-5")
#    metric = FaithfulnessMetric(model=judge)
#    ```
# 2. **Synthetic eval set** — use Ragas's `TestsetGenerator` to grow the eval to 50-200 cases from your corpus.
# 3. **Cross-family judge** — run the same eval with GPT-4 as judge (you'd need an OpenAI key — we can use a different family like Gemini via `langchain-google-genai`).
# 4. **Plot the bootstrap distribution** — `plt.hist(means)` to see the noise visually.
# 5. **Inter-judge agreement** — run two judges (Claude + Gemini), measure Krippendorff's α.
#
# ## What this demonstrated
# - Ragas defaults to OpenAI but can be configured with Claude (or any LangChain LLM) as judge.
# - The faithfulness algorithm is a 2-step LLM pipeline you can implement yourself in 30 lines.
# - Bootstrap CIs are non-negotiable for any "did this metric move?" claim.
# - Position-swap converts an unreliable single-judgment into a reliable consensus or a clear "the judge is biased here" signal.
