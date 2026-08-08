"""
LangGraph Workflow Tests

Verifies:
  - The graph builds and compiles without error.
  - `workflow_mode="single"` routes through document_intelligence.
  - `workflow_mode="comparison"` routes through contract_comparison.
  - Both modes converge into compliance -> red_flag -> risk -> report.
  - The full pipeline runs end-to-end without crashing when every LLM
    call is mocked (fast, no network/DB dependency).
"""
import app.graph as graph_mod
from app.agents.state import LegalAnalysisState
from langgraph.graph import StateGraph, START, END


def test_graph_builds_and_compiles():
    compiled = graph_mod.build_legal_graph()
    assert compiled is not None


def test_route_after_research_single_mode():
    assert graph_mod._route_after_research({"workflow_mode": "single"}) == "document_intelligence"
    assert graph_mod._route_after_research({}) == "document_intelligence"  # default


def test_route_after_research_comparison_mode():
    assert graph_mod._route_after_research({"workflow_mode": "comparison"}) == "contract_comparison"


def _build_test_graph_with_stub_nodes(calls: list[str]):
    """Builds a structurally identical graph but with lightweight stub
    nodes (instead of real agents) so routing can be tested without
    any LLM/DB calls."""

    def make_node(name):
        def node(state):
            calls.append(name)
            return {}
        return node

    graph = StateGraph(LegalAnalysisState)
    for name in [
        "legal_intake", "legal_research", "document_intelligence",
        "contract_comparison", "compliance_check", "red_flag_detection",
        "risk_assessment", "report_generation",
    ]:
        graph.add_node(name, make_node(name))

    graph.add_edge(START, "legal_intake")
    graph.add_edge("legal_intake", "legal_research")
    graph.add_conditional_edges(
        "legal_research",
        graph_mod._route_after_research,
        {"document_intelligence": "document_intelligence", "contract_comparison": "contract_comparison"},
    )
    graph.add_edge("document_intelligence", "compliance_check")
    graph.add_edge("contract_comparison", "compliance_check")
    graph.add_edge("compliance_check", "red_flag_detection")
    graph.add_edge("red_flag_detection", "risk_assessment")
    graph.add_edge("risk_assessment", "report_generation")
    graph.add_edge("report_generation", END)
    return graph.compile()


def test_single_mode_visits_document_intelligence_not_comparison():
    calls: list[str] = []
    compiled = _build_test_graph_with_stub_nodes(calls)
    compiled.invoke({"workflow_mode": "single", "errors": []})

    assert "document_intelligence" in calls
    assert "contract_comparison" not in calls
    assert calls == [
        "legal_intake", "legal_research", "document_intelligence",
        "compliance_check", "red_flag_detection", "risk_assessment", "report_generation",
    ]


def test_comparison_mode_visits_comparison_not_document_intelligence():
    calls: list[str] = []
    compiled = _build_test_graph_with_stub_nodes(calls)
    compiled.invoke({"workflow_mode": "comparison", "errors": []})

    assert "contract_comparison" in calls
    assert "document_intelligence" not in calls
    assert calls == [
        "legal_intake", "legal_research", "contract_comparison",
        "compliance_check", "red_flag_detection", "risk_assessment", "report_generation",
    ]


def test_full_pipeline_single_mode_end_to_end(monkeypatch):
    """Runs the REAL compiled graph (real agent nodes) with every LLM
    call mocked, and research_node stubbed to avoid a live DB."""
    import app.agents.intake_agent as intake_mod
    import app.agents.document_intelligence_agent as doc_intel_mod
    import app.agents.compliance_agent as compliance_mod
    import app.agents.red_flag_agent as red_flag_mod
    import app.agents.risk_agent as risk_mod
    import app.agents.research_agent as research_mod

    def fake_llm(system_prompt, user_prompt, temperature=0.1):
        if "Legal Intake Agent" in system_prompt:
            return {"task_type": "Contract Review", "topics": ["liability"]}
        if "Legal Document Intelligence Agent" in system_prompt:
            return {"liability_clause": {"present": True, "summary": "Uncapped liability", "evidence": [{"label": "Clause 8"}]}}
        if "Compliance Agent" in system_prompt:
            return {"compliance_issues": []}
        if "Red Flag Detection Agent" in system_prompt:
            return {"risk_flags": [{"flag_type": "Unlimited Liability", "severity": "Critical", "explanation": "...", "evidence": []}], "severity": "Critical"}
        if "Legal Risk Assessment Agent" in system_prompt:
            return {"risks": [], "overall_risk_level": "Critical"}
        return {}

    monkeypatch.setattr(intake_mod, "chat_completion_json", fake_llm)
    monkeypatch.setattr(doc_intel_mod, "chat_completion_json", fake_llm)
    monkeypatch.setattr(compliance_mod, "chat_completion_json", fake_llm)
    monkeypatch.setattr(red_flag_mod, "chat_completion_json", fake_llm)
    monkeypatch.setattr(risk_mod, "chat_completion_json", fake_llm)
    monkeypatch.setattr(research_mod, "research_node", lambda state: {"retrieved_context": [], "sources": [], "errors": []})

    # Rebuild the graph so it picks up the monkeypatched research_node reference
    import importlib
    importlib.reload(graph_mod)
    monkeypatch.setattr(graph_mod, "research_node", research_mod.research_node)
    compiled = graph_mod.build_legal_graph()

    final_state = compiled.invoke({
        "query": "Review this contract",
        "document_text": "sample contract text " * 20,
        "workflow_mode": "single",
        "errors": [],
    })

    assert final_state["overall_risk_level"] == "Critical"
    assert final_state["compliance_results"]["compliance_score"] >= 0
    assert len(final_state["risk_flags"]) == 1
    assert "Legal Intelligence Report" in final_state["report_markdown"]
    assert "Red Flag Analysis" in final_state["report_markdown"]
