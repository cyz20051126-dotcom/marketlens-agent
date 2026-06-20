from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SerializableRecord:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolCallRecord(SerializableRecord):
    tool_name: str
    input_summary: str
    output_summary: str
    status: str
    latency_ms: int


@dataclass(frozen=True)
class TraceEvent(SerializableRecord):
    event_id: str
    run_id: str
    timestamp: str
    agent_name: str
    event_type: str
    summary: str
    input_preview: str
    output_preview: str
    tool_name: str
    tool_status: str
    latency_ms: int


@dataclass(frozen=True)
class TodoItem(SerializableRecord):
    todo_id: str
    run_id: str
    title: str
    intent: str
    query: str
    status: str
    assigned_agent: str
    supporting_source_urls: list[str] = field(default_factory=list)
    result_summary: str = ""
    task_type: str = ""


@dataclass(frozen=True)
class FinanceMetric(SerializableRecord):
    metric_id: str
    brand_id: str
    metric_name: str
    metric_value: float
    unit: str
    period: str
    formula: str
    source_evidence_ids: list[str]
    confidence: float
    notes: str


@dataclass(frozen=True)
class FinanceAssumption(SerializableRecord):
    assumption_id: str
    brand_id: str
    metric_name: str
    metric_value: float
    unit: str
    period: str
    formula: str
    source_evidence_ids: list[str]
    confidence: float
    notes: str


@dataclass(frozen=True)
class FinanceScenario(SerializableRecord):
    scenario_id: str
    brand_id: str
    scenario_name: str
    revenue_growth: float
    operating_margin: float
    discount_rate: float
    terminal_growth: float
    sensitivity_axis_x: str
    sensitivity_axis_y: str
    result_value: float
    notes: str


@dataclass(frozen=True)
class AgentRun(SerializableRecord):
    run_id: str
    session_id: str
    user_query: str
    intent: str
    started_at: str
    completed_at: str
    status: str
    agents_invoked: list[str]
    tool_calls: list[ToolCallRecord]
    trace_events: list[TraceEvent]
    todo_items: list[TodoItem]
    answer: str
    supporting_evidence_ids: list[str]
    finance_assumptions: list[FinanceAssumption]
    finance_scenarios: list[FinanceScenario]
    error_message: str = ""
    # Codex finding #1: surface whether the run actually called the LLM
    # or degraded to the fallback client, so the answer's trustworthiness
    # is visible in the run record and the frontend.
    llm_provider: str = ""
    llm_used: bool = False
    fallback_reason: str = ""
