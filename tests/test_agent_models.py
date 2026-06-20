from marketlens.agent.models import (
    AgentRun,
    FinanceAssumption,
    FinanceScenario,
    TodoItem,
    ToolCallRecord,
    TraceEvent,
)


def test_agent_run_serializes_nested_records():
    tool_call = ToolCallRecord(
        tool_name="EvidenceSearchTool",
        input_summary="brand_id=luckin",
        output_summary="2 evidence rows",
        status="success",
        latency_ms=12,
    )
    trace = TraceEvent(
        event_id="trace_001",
        run_id="run_001",
        timestamp="2026-06-20T10:00:00+08:00",
        agent_name="TriageAgent",
        event_type="intent",
        summary="Classified as local_evidence_qa.",
        input_preview="How does Luckin's price war affect margins?",
        output_preview="local_evidence_qa",
        tool_name="",
        tool_status="",
        latency_ms=3,
    )
    todo = TodoItem(
        todo_id="todo_001",
        run_id="run_001",
        title="Review local evidence",
        intent="Find pricing and margin evidence.",
        query="luckin pricing margin",
        status="completed",
        assigned_agent="TriageAgent",
        supporting_source_urls=["https://example.com/source"],
        result_summary="Found source-backed pricing evidence.",
    )
    run = AgentRun(
        run_id="run_001",
        session_id="session_001",
        user_query="How does Luckin's price war affect margins?",
        intent="local_evidence_qa",
        started_at="2026-06-20T10:00:00+08:00",
        completed_at="2026-06-20T10:00:05+08:00",
        status="completed",
        agents_invoked=["TriageAgent", "WriterAgent"],
        tool_calls=[tool_call],
        trace_events=[trace],
        todo_items=[todo],
        answer="Luckin's price war can compress store-level margins.",
        supporting_evidence_ids=["EV-003", "EV-004"],
        finance_assumptions=[],
        finance_scenarios=[],
        error_message="",
    )

    payload = run.to_dict()

    assert payload["run_id"] == "run_001"
    assert payload["tool_calls"][0]["tool_name"] == "EvidenceSearchTool"
    assert payload["trace_events"][0]["agent_name"] == "TriageAgent"
    assert payload["todo_items"][0]["status"] == "completed"


def test_finance_assumption_links_back_to_evidence():
    assumption = FinanceAssumption(
        assumption_id="fa_001",
        brand_id="luckin",
        metric_name="store_level_operating_margin",
        metric_value=0.178,
        unit="ratio",
        period="2025FY",
        formula="store_level_operating_profit / self_operated_store_revenue",
        source_evidence_ids=["EV-004"],
        confidence=0.82,
        notes="Uses public financial result metric.",
    )
    scenario = FinanceScenario(
        scenario_id="fs_001",
        brand_id="luckin",
        scenario_name="Base case",
        revenue_growth=0.15,
        operating_margin=0.1,
        discount_rate=0.12,
        terminal_growth=0.03,
        sensitivity_axis_x="revenue_growth",
        sensitivity_axis_y="operating_margin",
        result_value=1.0,
        notes="Educational sensitivity output.",
    )

    assert assumption.to_dict()["source_evidence_ids"] == ["EV-004"]
    assert scenario.to_dict()["discount_rate"] == 0.12
