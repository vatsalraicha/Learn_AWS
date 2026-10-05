# mlflow3_tracing.py
# MLflow 3.0 GenAI tracing for a LangGraph agent backed by Anthropic Claude.
# Pairs with Module 12 (MLflow 3 deep) and Module 15 (Agent Framework).
#
# Demonstrates:
# - One-line autolog for LangChain + Anthropic
# - Prompt registry with versioning + aliases
# - Trajectory-level tracing (every node, every LLM call, every tool call)
#
# Stack convention: no OpenAI; Anthropic via Databricks FMAPI.

# %% Setup
import mlflow
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

# %% Enable MLflow autolog — one line each
mlflow.langchain.autolog()
mlflow.anthropic.autolog()

# Set the experiment (workspace path)
mlflow.set_experiment("/Shared/topic_02/clinical_agent_demo")


# %% Register prompts in MLflow Prompt Registry
def register_prompts() -> None:
    """One-time setup: register prompts so production code references them by alias."""
    mlflow.prompts.register(
        name="claim_summary",
        template="""You are a clinical reviewer assistant. Summarize this claim line for review by a registered nurse.
Be concise. Flag missing information explicitly.

Claim line:
{claim_line}

Member context:
{member_context}

Summary:""",
        version="v1",
        tags={"team": "claims-review", "phi_class": "high"},
    )

    # Promote to "champion" alias
    mlflow.prompts.set_alias("claim_summary", alias="champion", version="v1")


# %% Build the agent — LangGraph state machine
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    claim_line: dict
    member_context: dict


def retrieve_node(state: AgentState) -> AgentState:
    """Stub: in production, this calls Mosaic AI Vector Search."""
    # Example: vector_search.similarity_search(...)
    member_id = state["claim_line"].get("member_id")
    state["member_context"] = {
        "member_id": member_id,
        "active_diagnoses": ["E11.9"],  # Type 2 diabetes (placeholder)
    }
    return state


def generate_node(state: AgentState) -> AgentState:
    """Use the prompt-registry champion to summarize."""
    prompt = mlflow.prompts.load("claim_summary", alias="champion")
    filled = prompt.template.format(
        claim_line=state["claim_line"],
        member_context=state["member_context"],
    )

    llm = ChatAnthropic(
        model="claude-haiku-4-5",  # Anthropic Claude via Databricks FMAPI
        temperature=0.0,
        max_tokens=500,
    )
    response = llm.invoke([HumanMessage(content=filled)])
    state["messages"].append(response)
    return state


def build_agent() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


# %% Run with full tracing
def run_agent_demo() -> None:
    register_prompts()
    agent = build_agent()

    sample_claim = {
        "claim_id": "CLM-12345",
        "claim_line_id": "1",
        "member_id": "MBR-DEID-9876",
        "service_date": "2026-04-15",
        "procedure_code": "99213",
        "billed_amount": 175.0,
        "paid_amount": 100.0,
    }

    with mlflow.start_run(run_name="agent_invoke_demo") as run:
        mlflow.log_param("agent_version", "v1")
        mlflow.log_param("model", "claude-haiku-4-5")

        result = agent.invoke(
            {
                "messages": [],
                "claim_line": sample_claim,
                "member_context": {},
            }
        )

        # Log the final response
        mlflow.log_text(
            text=result["messages"][-1].content,
            artifact_file="response.txt",
        )

        print(f"Run ID: {run.info.run_id}")
        print(f"Trace UI: open the MLflow experiment in Databricks workspace")
        print(f"Response: {result['messages'][-1].content}")


# %% Production discipline notes
"""
What's traced automatically (one-line autolog):
- Every LangGraph node entry / exit
- Every Anthropic LLM call (input messages, output, token counts, latency)
- Tool invocations (if you add them)
- Vector Search retrieval (when you wire it in)
- Nested traces propagated via LangChain Callbacks

What this gives you in production:
- Debugging "why did the agent hallucinate?" — open the trace, see the retrieved context
- Cost / latency breakdown per request
- A/B testing — change the champion alias and trace separates the two cohorts

What's NOT traced unless you opt in:
- DSPy compile traces (use mlflow.dspy.autolog(log_traces_from_compile=True))
- Custom tools wrapped outside MLflow conventions

What changes for HIPAA workspaces:
- The MLflow trace store sits in the Databricks-hosted plane (managed-services CMK applies)
- Traces can contain PHI from prompts/responses — tag the experiment phi_class=high
- For cross-platform observability, use OTEL export to a self-hosted backend in your BAA scope
"""

if __name__ == "__main__":
    run_agent_demo()
