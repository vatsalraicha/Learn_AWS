# %% [markdown]
# # Notebook 14 — Grounding, Citations & Hallucination Detection
#
# **Pairs with:** [Module 14 — Grounding, Citation & Hallucination](../14_grounding_citation_hallucination.md)
#
# **What you'll see:**
# 1. **Anthropic Citations API** — generate answers with parser-validated inline citations.
# 2. **Vectara HHEM-2.1-Open** — local hallucination detection model (NLI-style cross-encoder).
# 3. **Hand-rolled NLI hallucination detector** using DeBERTa-v3-large-mnli as a baseline.
# 4. **Abstention policy** — combine signals into a refuse/answer decision.
#
# **Stack:** anthropic (Citations API), HuggingFace transformers (HHEM, DeBERTa-NLI). **No OpenAI.**

# %% [markdown]
# ## Setup

# %%
import os
import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

assert os.environ.get("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY required"

import sys
sys.path.insert(0, str(Path(__file__).parent / "data"))
from seed_corpus import get_corpus  # noqa: E402

corpus = {c[0]: c[1] for c in get_corpus()}

# %% [markdown]
# ## Part 1 — Anthropic Citations API
#
# Pass documents in a structured `<document>` block; Claude emits responses with
# `cited_text` references that the API parses into validated pointers.
# **Citations are guaranteed to point at real spans** — this is enforced by the parser.

# %%
from anthropic import Anthropic
client = Anthropic()

# Build a document set from the seed corpus (HR policies)
documents = [
    {
        "type": "document",
        "source": {"type": "text", "media_type": "text/plain", "data": corpus["hr_001"]},
        "title": "401k Plan 2024",
        "context": "Acme Corp 401(k) plan document",
        "citations": {"enabled": True},
    },
    {
        "type": "document",
        "source": {"type": "text", "media_type": "text/plain", "data": corpus["hr_002"]},
        "title": "Refund Policy Q4 2024",
        "context": "Current refund policy for B2B customers",
        "citations": {"enabled": True},
    },
    {
        "type": "document",
        "source": {"type": "text", "media_type": "text/plain", "data": corpus["hr_004"]},
        "title": "Parental Leave 2024",
        "context": "Parental leave policy",
        "citations": {"enabled": True},
    },
]

def answer_with_citations(question: str) -> Dict:
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": documents + [{"type": "text", "text": question}],
        }],
    )
    return msg

# Run on a question whose answer spans two documents
question = "What is the 401k vesting schedule, and how many weeks of parental leave do adoptive parents get?"
print(f"\nQUESTION: {question}\n")

response = answer_with_citations(question)

# The response is a list of content blocks, some with citations
print("=== Answer with citations ===")
for block in response.content:
    if block.type == "text":
        print(block.text, end="")
        if hasattr(block, "citations") and block.citations:
            for cite in block.citations:
                # cite has document_index, document_title, cited_text, etc.
                print(f"\n  [cite → {cite.document_title}: \"{cite.cited_text[:80]}...\"]")
        print()

# %% [markdown]
# **Key property:** the parser ensures every `cited_text` *actually exists* in the source.
# The model can't hallucinate a citation pointing at non-existent content.
#
# This is **architecturally** different from a model emitting "[1]" markers and a separate
# system trying to retroactively justify them — the latter is the GTR pattern Module 14 warns against.

# %% [markdown]
# ## Part 2 — Hallucination detection with Vectara HHEM-2.1-Open
#
# A small cross-encoder model (~190 MB) that scores how likely an answer is hallucinated
# given a context. Runs on CPU; first call downloads weights into HF cache.

# %%
print("\nLoading HHEM-2.1-Open from HuggingFace...")
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Vectara's open-weight model
MODEL_ID = "vectara/hallucination_evaluation_model"
hhem_tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
hhem_model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, trust_remote_code=True)
hhem_model.eval()

def hhem_score(premise: str, hypothesis: str) -> float:
    """Returns probability in [0,1] that the hypothesis is supported by the premise.
    Higher = more grounded; lower = more likely hallucinated."""
    pairs = [(premise, hypothesis)]
    score = hhem_model.predict(pairs)
    return float(score[0])

# Test on a faithful answer vs a fabricated one
context = corpus["hr_001"]  # 401k plan
faithful_answer = "The match is 100% up to 4% with 3-year vesting."
fabricated_answer = "The match is 50% up to 6% with immediate vesting and a $500 sign-on bonus."

print(f"\nFaithful   answer score: {hhem_score(context, faithful_answer):.3f}")
print(f"Fabricated answer score: {hhem_score(context, fabricated_answer):.3f}")
print("(Higher = more grounded. Threshold for production: typically 0.5-0.7.)")

# %% [markdown]
# ## Part 3 — Hand-rolled NLI hallucination detector
#
# DeBERTa-v3-large-mnli is a general-purpose NLI model. For each claim in the answer,
# check if it's entailed by the retrieved context. Useful when HHEM is too narrow or you
# want to combine signals.

# %%
from transformers import pipeline

print("\nLoading DeBERTa-v3-large-mnli...")
nli = pipeline("text-classification", model="MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli")

def nli_entailment(premise: str, hypothesis: str) -> Dict:
    """Returns {entailment, neutral, contradiction} probabilities."""
    # The model expects a single sequence: "{premise} </s></s> {hypothesis}"
    result = nli({"text": premise, "text_pair": hypothesis}, top_k=None)
    return {r["label"]: r["score"] for r in result}

# Decompose the fabricated answer into atomic claims (for demo, just pre-split)
claims = [
    "The 401k match is 50%.",
    "The match goes up to 6% of salary.",
    "Vesting is immediate.",
    "There is a $500 sign-on bonus.",
]

print(f"\nClaim-level NLI check against 401k policy context:")
for claim in claims:
    probs = nli_entailment(corpus["hr_001"], claim)
    verdict = max(probs, key=probs.get)
    print(f"  [{verdict:12s} {probs[verdict]:.2f}]  {claim}")

# %% [markdown]
# Note that DeBERTa-NLI returns `entailment`, `neutral`, or `contradiction`. In production:
# - **entailment** → claim supported.
# - **contradiction** → claim contradicts context (intrinsic hallucination).
# - **neutral** → claim not addressed by context (extrinsic hallucination — model invented it).

# %% [markdown]
# ## Part 4 — Compose into an abstention policy
#
# Combine multiple signals: retrieval similarity, HHEM groundedness, NLI claim verification.

# %%
def abstain_decision(
    query: str,
    context_chunks: List[str],
    draft_answer: str,
    claims: List[str],
    *,
    hhem_threshold: float = 0.5,
    nli_unsupported_fraction: float = 0.3,
) -> Dict:
    """Returns {'abstain': bool, 'reasons': List[str]}."""
    reasons = []

    joined_context = "\n\n".join(context_chunks)

    # Signal 1: HHEM groundedness on full draft
    grounded = hhem_score(joined_context, draft_answer)
    if grounded < hhem_threshold:
        reasons.append(f"HHEM groundedness {grounded:.2f} < {hhem_threshold}")

    # Signal 2: per-claim NLI; abstain if too many unsupported
    unsupported = 0
    for claim in claims:
        probs = nli_entailment(joined_context, claim)
        verdict = max(probs, key=probs.get)
        if verdict in ("contradiction", "neutral"):
            unsupported += 1
    fraction_unsupported = unsupported / len(claims) if claims else 0
    if fraction_unsupported > nli_unsupported_fraction:
        reasons.append(f"{unsupported}/{len(claims)} claims unsupported (>{nli_unsupported_fraction:.0%})")

    return {"abstain": bool(reasons), "reasons": reasons, "grounded_score": grounded}


# Test on faithful vs fabricated
print("\n=== Abstention policy on faithful answer ===")
decision = abstain_decision(
    query="What is the 401k match?",
    context_chunks=[corpus["hr_001"]],
    draft_answer=faithful_answer,
    claims=["The match is 100% up to 4%.", "Vesting is over 3 years."],
)
print(json.dumps(decision, indent=2))

print("\n=== Abstention policy on fabricated answer ===")
decision = abstain_decision(
    query="What is the 401k match?",
    context_chunks=[corpus["hr_001"]],
    draft_answer=fabricated_answer,
    claims=claims,
)
print(json.dumps(decision, indent=2))

# %% [markdown]
# ## Things to try next
#
# 1. **Wire it end-to-end** — combine Notebook 05 (hybrid retrieval) + 06 (rerank) + this
#    notebook's abstention policy + Anthropic Citations API for a full grounded RAG demo.
# 2. **Tune thresholds** — generate more test cases (faithful + various flavors of hallucination)
#    and find the threshold that gives best ASR / FRR balance per Module 13B.
# 3. **Add Patronus Lynx** as a third detector — `huggingface.co/PatronusAI/Llama-3-Patronus-Lynx-8B-Instruct`.
#    Compare its verdicts to HHEM and NLI on the same examples.
# 4. **Track citation correctness** — for each Anthropic-cited span, run an NLI check on
#    (claim, cited_span) and flag if not entailed (the FACTUM "citation hallucination" pattern).
#
# ## What this demonstrated
# - **Citations API** gives you parser-validated inline pointers — no fabricated citations possible.
# - **HHEM-2.1-Open** scores hallucination locally on CPU — production-deployable.
# - **NLI claim-level checks** catch extrinsic vs intrinsic hallucinations explicitly.
# - **A composite abstention policy** combining 2-3 signals beats any single signal alone
#   and is what mature production RAG runs.
