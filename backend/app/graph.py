"""
LangGraph workflow definition — Phase 2.

Single-contract pipeline (workflow_mode="single", the default):

    User Query / PDF Upload
        -> Legal Intake Agent
        -> Legal Research Agent
        -> Legal Document Intelligence Agent   (Agent 6)
        -> Compliance Agent                    (Agent 7)
        -> Red Flag Detection Agent            (Agent 8)
        -> Legal Risk Assessment Agent         (Agent 4, Phase 1 — preserved)
        -> Legal Report Generation Agent       (Agent 5, Phase 1 — preserved)
        -> Final Legal Intelligence Report

Comparison pipeline (workflow_mode="comparison"):

    Contract A + Contract B
        -> Legal Intake Agent
        -> Legal Research Agent
        -> Contract Comparison Agent           (Agent 9, replaces Agent 6)
        -> Compliance Agent
        -> Red Flag Detection Agent
        -> Legal Risk Assessment Agent
        -> Legal Report Generation Agent
        -> Final Legal Intelligence Report (with comparison section)

Conditional routing is implemented with `add_conditional_edges` on a
single "route_after_research" branch point, keyed off
`state["workflow_mode"]`. Everything downstream of that branch point is
shared between both modes, since both produce a `document_intelligence`
payload (Agent 6 for single mode; Agent 9 populates it from Contract B
for comparison mode) that Compliance/Red Flag/Risk all consume
identically.

The original Phase 1 5-agent linear graph logic is preserved intact —
Agents 1, 2, 4, and 5 are unchanged; only Agent 3 (clause extraction)
is superseded in-graph by Agent 6, while remaining available standalone
in `app/agents/clause_agent.py`.
"""
from langgraph.graph import StateGraph, START, END

from app.agents.state import LegalAnalysisState
from app.agents.intake_agent import intake_node
from app.agents.research_agent import research_node
from app.agents.document_intelligence_agent import document_intelligence_node
from app.agents.compliance_agent import compliance_node
from app.agents.red_flag_agent import red_flag_node
from app.agents.comparison_agent import comparison_node
from app.agents.risk_agent import risk_node
from app.agents.report_agent import report_node


def _route_after_research(state: LegalAnalysisState) -> str:
    if state.get("workflow_mode") == "comparison":
        return "contract_comparison"
    return "document_intelligence_agent"


def build_legal_graph():
    graph = StateGraph(LegalAnalysisState)

    graph.add_node("legal_intake", intake_node)
    graph.add_node("legal_research", research_node)
    graph.add_node("document_intelligence_agent", document_intelligence_node)
    graph.add_node("contract_comparison", comparison_node)
    graph.add_node("compliance_check", compliance_node)
    graph.add_node("red_flag_detection", red_flag_node)
    graph.add_node("risk_assessment", risk_node)
    graph.add_node("report_generation", report_node)

    graph.add_edge(START, "legal_intake")
    graph.add_edge("legal_intake", "legal_research")

    graph.add_conditional_edges(
    "legal_research",
    _route_after_research,
    {
        "document_intelligence_agent": "document_intelligence_agent",
        "contract_comparison": "contract_comparison",
    },
)

    # Both branches converge back into the shared compliance -> red flag
    # -> risk -> report tail.
    graph.add_edge("document_intelligence_agent", "compliance_check")
    graph.add_edge("contract_comparison", "compliance_check")

    graph.add_edge("compliance_check", "red_flag_detection")
    graph.add_edge("red_flag_detection", "risk_assessment")
    graph.add_edge("risk_assessment", "report_generation")
    graph.add_edge("report_generation", END)

    return graph.compile()


# Compiled once, reused across requests (LangGraph compiled graphs are stateless/thread-safe).
legal_graph = build_legal_graph()


def run_legal_pipeline(
    query: str,
    document_id=None,
    document_text: str | None = None,
    session_id=None,
    workflow_mode: str = "single",
    document_id_b=None,
    document_text_b: str | None = None,
) -> LegalAnalysisState:
    """Convenience entrypoint used by the API routes.

    Set workflow_mode="comparison" (with document_text_b populated) to
    run the Contract Comparison branch instead of Document Intelligence.
    """
    initial_state: LegalAnalysisState = {
        "query": query,
        "document_id": document_id,
        "document_text": document_text,
        "session_id": session_id,
        "workflow_mode": workflow_mode,
        "document_id_b": document_id_b,
        "document_text_b": document_text_b,
        "errors": [],
    }
    final_state = legal_graph.invoke(initial_state)
    return final_state
