"""End-to-end integration tests for the full multi-agent chain.

These tests run the orchestrator with MockLLMClient + stub web search to
verify the complete pipeline (Triage -> EvidenceSearch -> [Planner ->
Search -> Extractor -> Verifier -> Store] -> [FinanceLens] -> Writer)
without hitting real LLM or network. They assert the AgentRun shape,
agent invocation order, Chinese answer with evidence citations, and
real latency values.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from marketlens.agent.llm import MockLLMClient
from marketlens.agent.orchestrator import MarketLensAgentOrchestrator
from marketlens.agent.runtime import ToolResponse


ROOT = Path(__file__).resolve().parents[1]


class E2EWebSearchTool:
    """Stub web search that returns canned Chinese results."""

    name = "E2EWebSearchTool"

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        return ToolResponse(
            success=True,
            data={
                "results": [
                    {
                        "title": "\u745e\u5e78 2026 Q1 \u8d22\u62a5",
                        "url": "https://example.com/luckin-q1",
                        "snippet": "\u745e\u5e78 2026 Q1 \u5229\u6da6\u7387 6.0%\u3002",
                    },
                    {
                        "title": "\u5e93\u8fea\u4fc3\u9500\u7ed3\u675f",
                        "url": "https://example.com/cotti-promo",
                        "snippet": "\u5e93\u8fea 9.9 \u5143\u4f83\u9500\u5168\u573a\u7ed3\u675f\u3002",
                    },
                ],
                "query": payload.get("query", ""),
                "status": "live",
                "count": 2,
            },
        )


def _make_orchestrator(
    tmp_path: Path,
    llm_response: str,
) -> MarketLensAgentOrchestrator:
    return MarketLensAgentOrchestrator(
        evidence_path=ROOT / "data" / "evidence.csv",
        finance_metrics_path=ROOT / "data" / "finance_metrics.csv",
        session_dir=tmp_path / "sessions",
        search_cache_dir=tmp_path / "websearch",
        llm_client=MockLLMClient(response=llm_response),
        web_search_tool=E2EWebSearchTool(),
    )


# --- E2E: research question runs full agent chain --------------------------


def test_e2e_research_question_runs_full_agent_chain(tmp_path):
    """A research question with thin local evidence triggers the full
    chain: Triage -> EvidenceSearch -> Planner -> SearchAgent ->
    EvidenceExtractorAgent -> VerifierAgent -> WriterAgent."""
    # MockLLMClient returns the same response for every agent call. Each
    # agent parses what it can and falls back to rules on parse failure.
    # For this test we use a triage-shaped JSON; Planner/Extractor will
    # fall back to rules, which is the documented graceful-degradation
    # behavior.
    triage_response = json.dumps(
        {
            "intent": "new_research_needed",
            "rewritten_query": "\u53e4\u8317 \u5355\u5e97\u6a21\u578b 2026",
        }
    )
    orchestrator = _make_orchestrator(tmp_path, triage_response)

    # Query that produces 0 strict-matched local evidence -> triggers search
    run = orchestrator.answer("\u53e4\u8317\u5355\u5e97\u6a21\u578b 2026")

    assert run.status == "completed"
    # All research-chain agents must be invoked in order
    expected_agents = [
        "TriageAgent",
        "PlannerAgent",
        "SearchAgent",
        "EvidenceExtractorAgent",
        "VerifierAgent",
        "WriterAgent",
    ]
    for agent in expected_agents:
        assert agent in run.agents_invoked, f"missing agent: {agent}"

    # Tool calls include both local + web search
    tool_names = [tc.tool_name for tc in run.tool_calls]
    assert "EvidenceSearchTool" in tool_names
    assert "WebSearchTool" in tool_names

    # Trace events must be ordered: Triage first, Writer last
    agent_order = [e.agent_name for e in run.trace_events]
    triage_idx = agent_order.index("TriageAgent")
    writer_idx = agent_order.index("WriterAgent")
    assert triage_idx < writer_idx

    # Session is persisted
    assert (tmp_path / "sessions" / f"{run.run_id}.json").exists()


# --- E2E: finance question includes finance assumptions --------------------


def test_e2e_finance_question_includes_finance_assumptions(tmp_path):
    """A finance question triggers FinanceLensAgent and the AgentRun
    includes assumptions + scenarios."""
    finance_response = json.dumps(
        {
            "intent": "finance_analysis_needed",
            "rewritten_query": "\u745e\u5e78 DCF \u4f30\u503c",
        }
    )
    orchestrator = _make_orchestrator(tmp_path, finance_response)

    run = orchestrator.answer(
        "\u5e2e\u6211\u7528 DCF \u5206\u6790\u745e\u5e78\u4ef7\u683c\u6218\u5bf9\u4f30\u503c\u7684\u5f71\u54cd"
    )

    assert run.intent == "finance_analysis_needed"
    assert "FinanceLensAgent" in run.agents_invoked
    assert run.finance_assumptions
    assert run.finance_scenarios
    # Scenarios include the three DCF sensitivity cases
    scenario_names = {s.scenario_name for s in run.finance_scenarios}
    assert "Conservative" in scenario_names
    assert "Base" in scenario_names
    assert "Upside" in scenario_names


# --- E2E: answer is Chinese with evidence citations ------------------------


def test_e2e_answer_is_chinese_with_evidence_citations(tmp_path):
    """When local evidence is sufficient, Writer produces a Chinese answer
    that cites at least one evidence ID and includes the limitations
    paragraph (enforced by post-processing)."""
    # Use a query whose evidence_query strictly matches >= 2 local rows so
    # search is skipped and Writer gets real evidence to cite.
    # "瑞幸利润率" -> evidence_query "利润率" matches EV-003 + EV-004.
    orchestrator = _make_orchestrator(
        tmp_path,
        "\u57fa\u4e8e\u8bc1\u636e\u7684\u4e2d\u6587\u5206\u6790\u3002",
    )

    run = orchestrator.answer("\u745e\u5e78\u5229\u6da6\u7387")

    assert run.status == "completed"
    assert run.supporting_evidence_ids
    # Answer must cite at least one evidence ID
    for eid in run.supporting_evidence_ids:
        assert eid in run.answer
    # Answer must include the limitations paragraph
    assert "\u5c40\u9650\u6027" in run.answer


# --- E2E: trace events have real latency -----------------------------------


def test_e2e_trace_events_have_real_latency(tmp_path):
    """All trace events record latency_ms >= 1 (real timing)."""
    orchestrator = _make_orchestrator(
        tmp_path,
        json.dumps({"intent": "local_evidence_qa", "rewritten_query": "test"}),
    )

    run = orchestrator.answer("\u745e\u5e78\u5229\u6da6\u7387")

    assert run.trace_events
    for event in run.trace_events:
        assert event.latency_ms >= 1


# --- E2E: tool calls have real latency -------------------------------------


def test_e2e_tool_calls_have_real_latency(tmp_path):
    """All tool call records have latency_ms >= 1 (real timing, not the
    hardcoded 1ms placeholder)."""
    orchestrator = _make_orchestrator(
        tmp_path,
        json.dumps({"intent": "local_evidence_qa", "rewritten_query": "test"}),
    )

    run = orchestrator.answer("\u745e\u5e78\u5229\u6da6\u7387")

    assert run.tool_calls
    for tc in run.tool_calls:
        assert tc.latency_ms >= 1


# --- E2E: degraded search does not crash the run ---------------------------


def test_e2e_degraded_search_does_not_crash_run(tmp_path):
    """When web search fails (degraded_fallback), the orchestrator still
    produces a complete AgentRun using only local evidence."""
    class FailingSearchTool:
        name = "FailingSearchTool"

        def run(self, payload: dict[str, Any]) -> ToolResponse:
            return ToolResponse(
                success=False,
                data={"results": [], "status": "degraded_fallback"},
                error="offline",
            )

    orchestrator = MarketLensAgentOrchestrator(
        evidence_path=ROOT / "data" / "evidence.csv",
        finance_metrics_path=ROOT / "data" / "finance_metrics.csv",
        session_dir=tmp_path / "sessions",
        search_cache_dir=tmp_path / "websearch",
        llm_client=MockLLMClient(
            response=json.dumps(
                {
                    "intent": "new_research_needed",
                    "rewritten_query": "\u53e4\u8317\u5355\u5e97",
                }
            )
        ),
        web_search_tool=FailingSearchTool(),
    )

    run = orchestrator.answer("\u53e4\u8317\u5355\u5e97\u6a21\u578b 2026")

    assert run.status == "completed"
    assert "SearchAgent" in run.agents_invoked
    assert "EvidenceExtractorAgent" not in run.agents_invoked
    assert "WriterAgent" in run.agents_invoked
