# MarketLens Agent v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build MarketLens Agent v2 as a real AI research console with a custom lightweight agent runtime, local evidence Q&A, DeepSeek fallback support, Firecrawl-ready research tools, finance analysis, trace logs, and a React Agent Console.

**Architecture:** Keep the current static evidence pipeline and React dashboard, then add a focused Python agent layer beside it. A local FastAPI server exposes `/api/agent/chat`; React calls that endpoint and renders chat answers, todo items, tool calls, trace events, evidence IDs, and finance assumptions. The agent runtime is self-built and small enough to explain in interviews.

**Tech Stack:** Python 3.11 dataclasses, pytest, FastAPI, uvicorn, standard-library HTTP client for DeepSeek-compatible calls, existing CSV/JSON data artifacts, React 18, TypeScript, Vite, lucide-react.

---

## Scope Check

This is one plan because the runtime, API, and frontend are tightly coupled into one testable product slice: a user asks a research question and sees an agent run with evidence and finance output. The plan is split into milestones that each produce working, testable software:

1. agent data models,
2. runtime primitives,
3. evidence and finance tools,
4. LLM provider and specialized agents,
5. orchestrator and FastAPI API,
6. React Agent Console,
7. documentation and verification.

## File Structure

Create or modify these files:

- Modify: `pyproject.toml`
  Add FastAPI/uvicorn runtime dependency and httpx test dependency.

- Create: `src/marketlens/agent/__init__.py`
  Public exports for the new agent package.

- Create: `src/marketlens/agent/models.py`
  Agent run, trace, todo, tool call, finance metric, finance assumption, finance scenario dataclasses.

- Create: `src/marketlens/agent/runtime.py`
  `ToolResponse`, `Tool`, `ToolRegistry`, `BaseAgent`, `TodoBoard`.

- Create: `src/marketlens/agent/session.py`
  JSON-backed `SessionStore`.

- Create: `src/marketlens/agent/trace.py`
  In-memory and JSON-serializable `TraceLogger`.

- Create: `src/marketlens/agent/tools.py`
  `EvidenceSearchTool`, `FirecrawlSearchTool`, `SourceReadTool`, `EvidenceStoreTool`.

- Create: `src/marketlens/agent/finance.py`
  Finance metric loader, `FinanceModelTool`, unit economics and DCF-style sensitivity helpers.

- Create: `src/marketlens/agent/llm.py`
  `FallbackLLMClient` and `DeepSeekLLMClient`.

- Create: `src/marketlens/agent/agents.py`
  `TriageAgent`, `PlannerAgent`, `SearchAgent`, `EvidenceExtractorAgent`, `VerifierAgent`, `FinanceLensAgent`, `WriterAgent`.

- Create: `src/marketlens/agent/orchestrator.py`
  `MarketLensAgentOrchestrator` for one end-to-end chat run.

- Create: `src/marketlens/api.py`
  FastAPI app with `/api/agent/chat` and `/api/agent/runs/{run_id}`.

- Create: `data/finance_metrics.csv`
  Seed metrics for Luckin, Mixue, CHAGEE, and Guming using public-source-backed figures.

- Modify: `scripts/build_artifacts.py`
  Export a deterministic `agent_demo.json` for frontend fallback and screenshots.

- Create: `web/src/types/agent.ts`
  TypeScript types matching Python API payloads.

- Create: `web/src/components/AgentConsole.tsx`
  Chat input and agent response surface.

- Create: `web/src/components/AgentTrace.tsx`
  Todo board, trace timeline, and tool call cards.

- Create: `web/src/components/FinanceLens.tsx`
  Finance assumptions and scenario output.

- Modify: `web/src/App.tsx`
  Import and render `AgentConsole` above the existing dashboard.

- Modify: `web/src/styles.css`
  Add Agent Console styles while preserving current design language.

- Modify: `web/vite.config.ts`
  Add dev proxy from `/api` to `http://127.0.0.1:8765`.

- Create tests:
  - `tests/test_agent_models.py`
  - `tests/test_agent_runtime.py`
  - `tests/test_agent_tools.py`
  - `tests/test_agent_agents.py`
  - `tests/test_agent_orchestrator.py`
  - `tests/test_api.py`

- Modify docs:
  - `README.md`
  - `docs/interview_talking_points.md`
  - `docs/application_materials/ai_agent_application_version.md`

---

### Task 1: Agent Models And Dependencies

**Files:**
- Modify: `pyproject.toml`
- Create: `src/marketlens/agent/__init__.py`
- Create: `src/marketlens/agent/models.py`
- Test: `tests/test_agent_models.py`

- [x] **Step 1: Write failing model tests**

Create `tests/test_agent_models.py`:

```python
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
        input_preview="瑞幸价格战影响",
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
        user_query="瑞幸价格战对利润率有什么影响？",
        intent="local_evidence_qa",
        started_at="2026-06-20T10:00:00+08:00",
        completed_at="2026-06-20T10:00:05+08:00",
        status="completed",
        agents_invoked=["TriageAgent", "WriterAgent"],
        tool_calls=[tool_call],
        trace_events=[trace],
        todo_items=[todo],
        answer="瑞幸价格战会压缩店级利润率。",
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
```

- [x] **Step 2: Run model tests and verify failure**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_models.py -q
```

Expected: failure because `marketlens.agent.models` does not exist.

- [x] **Step 3: Add dependencies**

Modify `pyproject.toml`:

```toml
[project]
name = "marketlens-ai"
version = "0.1.0"
description = "Source-backed competitive intelligence workflow for fresh beverage brands."
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.116",
  "uvicorn[standard]>=0.35",
]

[project.optional-dependencies]
dev = ["pytest>=8.2", "httpx>=0.28"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

Then install the new dependencies:

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Expected: install succeeds.

- [x] **Step 4: Create agent package exports**

Create `src/marketlens/agent/__init__.py`:

```python
"""Agentic research runtime for MarketLens."""

from marketlens.agent.models import AgentRun, FinanceAssumption, FinanceScenario

__all__ = ["AgentRun", "FinanceAssumption", "FinanceScenario"]
```

- [x] **Step 5: Implement model dataclasses**

Create `src/marketlens/agent/models.py`:

```python
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
```

- [x] **Step 6: Run model tests and full tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_models.py -q
.\.venv\Scripts\python -m pytest -q
```

Expected: all tests pass.

- [x] **Step 7: Commit Task 1**

```powershell
git add pyproject.toml src/marketlens/agent/__init__.py src/marketlens/agent/models.py tests/test_agent_models.py
git commit -m "feat: add agent data models"
```

---

### Task 2: Runtime, Session Store, Trace Logger

**Files:**
- Create: `src/marketlens/agent/runtime.py`
- Create: `src/marketlens/agent/session.py`
- Create: `src/marketlens/agent/trace.py`
- Test: `tests/test_agent_runtime.py`

- [x] **Step 1: Write failing runtime tests**

Create `tests/test_agent_runtime.py`:

```python
from pathlib import Path

from marketlens.agent.models import AgentRun
from marketlens.agent.runtime import Tool, ToolRegistry, ToolResponse, TodoBoard
from marketlens.agent.session import SessionStore
from marketlens.agent.trace import TraceLogger


class EchoTool(Tool):
    name = "EchoTool"
    description = "Echoes a payload."

    def run(self, payload):
        return ToolResponse(success=True, data={"echo": payload["text"]}, error="")


def test_tool_registry_calls_registered_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())

    response = registry.call("EchoTool", {"text": "hello"})

    assert response.success is True
    assert response.data == {"echo": "hello"}


def test_tool_registry_reports_missing_tool():
    registry = ToolRegistry()

    response = registry.call("MissingTool", {})

    assert response.success is False
    assert "not registered" in response.error


def test_trace_logger_records_ordered_events():
    logger = TraceLogger(run_id="run_001")
    logger.record(
        agent_name="TriageAgent",
        event_type="intent",
        summary="Classified the query.",
        input_preview="query",
        output_preview="local_evidence_qa",
        tool_name="",
        tool_status="",
        latency_ms=1,
    )

    events = logger.events()

    assert len(events) == 1
    assert events[0].event_id == "trace_001"
    assert events[0].agent_name == "TriageAgent"


def test_todo_board_tracks_completion():
    board = TodoBoard(run_id="run_001")
    item = board.add(
        title="Search evidence",
        intent="Find sources",
        query="luckin margin",
        assigned_agent="PlannerAgent",
    )
    board.complete(item.todo_id, "Found margin evidence.", ["https://example.com"])

    assert board.items()[0].status == "completed"
    assert board.items()[0].supporting_source_urls == ["https://example.com"]


def test_session_store_persists_run(tmp_path):
    store = SessionStore(tmp_path / "sessions")
    run = AgentRun(
        run_id="run_001",
        session_id="session_001",
        user_query="hello",
        intent="local_evidence_qa",
        started_at="2026-06-20T10:00:00+08:00",
        completed_at="2026-06-20T10:00:01+08:00",
        status="completed",
        agents_invoked=[],
        tool_calls=[],
        trace_events=[],
        todo_items=[],
        answer="answer",
        supporting_evidence_ids=[],
        finance_assumptions=[],
        finance_scenarios=[],
        error_message="",
    )

    store.save_run(run)
    loaded = store.load_run("run_001")

    assert loaded["answer"] == "answer"
    assert Path(tmp_path / "sessions" / "run_001.json").exists()
```

- [x] **Step 2: Run runtime tests and verify failure**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_runtime.py -q
```

Expected: failure because runtime modules do not exist.

- [x] **Step 3: Implement runtime primitives**

Create `src/marketlens/agent/runtime.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from marketlens.agent.models import TodoItem


@dataclass(frozen=True)
class ToolResponse:
    success: bool
    data: dict[str, Any]
    error: str = ""


class Tool(Protocol):
    name: str
    description: str

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def call(self, tool_name: str, payload: dict[str, Any]) -> ToolResponse:
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResponse(
                success=False,
                data={},
                error=f"Tool is not registered: {tool_name}",
            )
        try:
            return tool.run(payload)
        except Exception as exc:
            return ToolResponse(success=False, data={}, error=str(exc))

    def names(self) -> list[str]:
        return sorted(self._tools)


class BaseAgent:
    name = "BaseAgent"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class TodoBoard:
    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._items: list[TodoItem] = []

    def add(self, title: str, intent: str, query: str, assigned_agent: str) -> TodoItem:
        item = TodoItem(
            todo_id=f"todo_{len(self._items) + 1:03d}",
            run_id=self._run_id,
            title=title,
            intent=intent,
            query=query,
            status="pending",
            assigned_agent=assigned_agent,
            supporting_source_urls=[],
            result_summary="",
        )
        self._items.append(item)
        return item

    def complete(self, todo_id: str, result_summary: str, source_urls: list[str]) -> None:
        self._items = [
            TodoItem(
                todo_id=item.todo_id,
                run_id=item.run_id,
                title=item.title,
                intent=item.intent,
                query=item.query,
                status="completed" if item.todo_id == todo_id else item.status,
                assigned_agent=item.assigned_agent,
                supporting_source_urls=source_urls if item.todo_id == todo_id else item.supporting_source_urls,
                result_summary=result_summary if item.todo_id == todo_id else item.result_summary,
            )
            for item in self._items
        ]

    def items(self) -> list[TodoItem]:
        return list(self._items)
```

- [x] **Step 4: Implement session store**

Create `src/marketlens/agent/session.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from marketlens.agent.models import AgentRun


class SessionStore:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def save_run(self, run: AgentRun) -> Path:
        path = self._root / f"{run.run_id}.json"
        path.write_text(
            json.dumps(run.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load_run(self, run_id: str) -> dict[str, Any]:
        path = self._root / f"{run_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))
```

- [x] **Step 5: Implement trace logger**

Create `src/marketlens/agent/trace.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

from marketlens.agent.models import TraceEvent


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class TraceLogger:
    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._events: list[TraceEvent] = []

    def record(
        self,
        agent_name: str,
        event_type: str,
        summary: str,
        input_preview: str,
        output_preview: str,
        tool_name: str,
        tool_status: str,
        latency_ms: int,
    ) -> TraceEvent:
        event = TraceEvent(
            event_id=f"trace_{len(self._events) + 1:03d}",
            run_id=self._run_id,
            timestamp=now_iso(),
            agent_name=agent_name,
            event_type=event_type,
            summary=summary,
            input_preview=input_preview[:240],
            output_preview=output_preview[:240],
            tool_name=tool_name,
            tool_status=tool_status,
            latency_ms=latency_ms,
        )
        self._events.append(event)
        return event

    def events(self) -> list[TraceEvent]:
        return list(self._events)
```

- [x] **Step 6: Run runtime tests and full tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_runtime.py -q
.\.venv\Scripts\python -m pytest -q
```

Expected: all tests pass.

- [x] **Step 7: Commit Task 2**

```powershell
git add src/marketlens/agent/runtime.py src/marketlens/agent/session.py src/marketlens/agent/trace.py tests/test_agent_runtime.py
git commit -m "feat: add agent runtime primitives"
```

---

### Task 3: Evidence Search And Finance Tools

**Files:**
- Create: `data/finance_metrics.csv`
- Create: `src/marketlens/agent/tools.py`
- Create: `src/marketlens/agent/finance.py`
- Test: `tests/test_agent_tools.py`

- [x] **Step 1: Write failing tool tests**

Create `tests/test_agent_tools.py`:

```python
from pathlib import Path

from marketlens.agent.finance import FinanceModelTool, load_finance_metrics
from marketlens.agent.tools import EvidenceSearchTool
from marketlens.load import load_evidence


ROOT = Path(__file__).resolve().parents[1]


def test_evidence_search_tool_finds_brand_and_lens_rows():
    rows = load_evidence(ROOT / "data" / "evidence.csv")
    tool = EvidenceSearchTool(rows)

    response = tool.run({"query": "瑞幸 利润率", "brand_id": "luckin", "lens": "risk"})

    assert response.success is True
    assert response.data["evidence"]
    assert response.data["evidence"][0]["brand_id"] == "luckin"


def test_finance_metric_loader_parses_seed_metrics():
    metrics = load_finance_metrics(ROOT / "data" / "finance_metrics.csv")

    assert any(metric.brand_id == "luckin" for metric in metrics)
    assert all(metric.source_evidence_ids for metric in metrics)


def test_finance_model_tool_returns_assumptions_and_scenarios():
    metrics = load_finance_metrics(ROOT / "data" / "finance_metrics.csv")
    tool = FinanceModelTool(metrics)

    response = tool.run({"brand_id": "luckin"})

    assert response.success is True
    assert response.data["assumptions"]
    assert response.data["scenarios"]
    assert response.data["assumptions"][0]["source_evidence_ids"]
```

- [x] **Step 2: Run tool tests and verify failure**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_tools.py -q
```

Expected: failure because tools and finance metrics do not exist.

- [x] **Step 3: Add finance seed metrics**

Create `data/finance_metrics.csv`:

```csv
metric_id,brand_id,metric_name,metric_value,unit,period,formula,source_evidence_ids,confidence,notes
FM-001,luckin,total_stores,33596,stores,2026Q1,,EV-001,0.92,瑞幸一季度末全球门店数。
FM-002,luckin,partnership_stores,11789,stores,2026Q1,,EV-002,0.91,瑞幸联营门店数。
FM-003,luckin,same_store_sales_growth,-0.001,ratio,2026Q1,,EV-003,0.82,瑞幸自营同店销售增长率。
FM-004,luckin,gaap_operating_margin,0.06,ratio,2026Q1,gaap_operating_income / total_net_revenue,EV-004,0.82,瑞幸 GAAP 营业利润率。
FM-005,mixue,store_count_proxy,53000,stores,2025H1,,EV-014,0.78,蜜雪门店规模使用当前证据库中加盟扩张证据作为支撑。
FM-006,mixue,franchise_network_signal,1,flag,2025H1,,EV-015,0.78,蜜雪加盟网络为扩张核心。
FM-007,chagee,revenue_growth_signal,0.354,ratio,2026Q1,,EV-018,0.78,霸王茶姬一季度收入增长信号。
FM-008,chagee,valuation_risk_signal,1,flag,2025FY,,EV-019,0.76,霸王茶姬 20-F/年报相关风险信号。
FM-009,guming,annual_report_available,1,flag,2025FY,,EV-021,0.83,古茗 2025 年报作为经营指标来源。
FM-010,guming,franchise_model_signal,1,flag,2025FY,,EV-023,0.80,古茗加盟模型证据。
```

- [x] **Step 4: Implement evidence tools**

Create `src/marketlens/agent/tools.py`:

```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from marketlens.agent.runtime import ToolResponse
from marketlens.schemas import EvidenceRow


class EvidenceSearchTool:
    name = "EvidenceSearchTool"
    description = "Searches local reviewed evidence rows."

    def __init__(self, evidence_rows: list[EvidenceRow]) -> None:
        self._rows = evidence_rows

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        query = str(payload.get("query", "")).lower()
        brand_id = str(payload.get("brand_id", "")).strip()
        lens = str(payload.get("lens", "")).strip()
        matches = []
        for row in self._rows:
            if row.review_status == "rejected":
                continue
            if brand_id and row.brand_id != brand_id:
                continue
            if lens and row.lens != lens:
                continue
            haystack = f"{row.claim} {row.excerpt} {row.source_title}".lower()
            if query and query not in haystack and not any(token in haystack for token in query.split()):
                continue
            matches.append(row.to_dict())
        return ToolResponse(success=True, data={"evidence": matches[:8]}, error="")


class FirecrawlSearchTool:
    name = "FirecrawlSearchTool"
    description = "Runs Firecrawl search and stores the raw JSON response."

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        query = str(payload["query"])
        slug = "".join(ch if ch.isalnum() else "-" for ch in query.lower())[:80].strip("-")
        output_path = self._output_dir / f"agent-search-{slug}.json"
        command = [
            "firecrawl",
            "search",
            query,
            "--limit",
            str(payload.get("limit", 5)),
            "--sources",
            "web",
            "-o",
            str(output_path),
            "--json",
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
            return ToolResponse(success=False, data={}, error=str(exc))
        data = json.loads(output_path.read_text(encoding="utf-8"))
        return ToolResponse(success=True, data={"path": str(output_path), "results": data.get("data", {})}, error="")


class SourceReadTool:
    name = "SourceReadTool"
    description = "Reads local cached source text."

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        path = Path(str(payload["path"]))
        if not path.exists():
            return ToolResponse(success=False, data={}, error=f"Source path does not exist: {path}")
        return ToolResponse(success=True, data={"text": path.read_text(encoding="utf-8")}, error="")


class EvidenceStoreTool:
    name = "EvidenceStoreTool"
    description = "Stores validated evidence rows in memory for the current run."

    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] = []

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        rows = list(payload.get("evidence", []))
        self._rows.extend(rows)
        return ToolResponse(success=True, data={"stored_count": len(self._rows), "evidence": self._rows}, error="")
```

- [x] **Step 5: Implement finance loader and tool**

Create `src/marketlens/agent/finance.py`:

```python
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from marketlens.agent.models import FinanceAssumption, FinanceMetric, FinanceScenario
from marketlens.agent.runtime import ToolResponse


def load_finance_metrics(path: Path) -> list[FinanceMetric]:
    metrics: list[FinanceMetric] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            metrics.append(
                FinanceMetric(
                    metric_id=raw["metric_id"],
                    brand_id=raw["brand_id"],
                    metric_name=raw["metric_name"],
                    metric_value=float(raw["metric_value"]),
                    unit=raw["unit"],
                    period=raw["period"],
                    formula=raw.get("formula", ""),
                    source_evidence_ids=[item.strip() for item in raw["source_evidence_ids"].split(";") if item.strip()],
                    confidence=float(raw["confidence"]),
                    notes=raw.get("notes", ""),
                )
            )
    return metrics


class FinanceModelTool:
    name = "FinanceModelTool"
    description = "Creates finance assumptions and DCF-style sensitivity scenarios from source-backed metrics."

    def __init__(self, metrics: list[FinanceMetric]) -> None:
        self._metrics = metrics

    def run(self, payload: dict[str, Any]) -> ToolResponse:
        brand_id = str(payload["brand_id"])
        brand_metrics = [metric for metric in self._metrics if metric.brand_id == brand_id]
        if not brand_metrics:
            return ToolResponse(success=False, data={}, error=f"No finance metrics for brand_id: {brand_id}")
        assumptions = [
            FinanceAssumption(
                assumption_id=f"fa_{index:03d}",
                brand_id=metric.brand_id,
                metric_name=metric.metric_name,
                metric_value=metric.metric_value,
                unit=metric.unit,
                period=metric.period,
                formula=metric.formula,
                source_evidence_ids=metric.source_evidence_ids,
                confidence=metric.confidence,
                notes=metric.notes,
            )
            for index, metric in enumerate(brand_metrics, start=1)
        ]
        base_growth = _metric_value(brand_metrics, "same_store_sales_growth", 0.08)
        base_margin = _metric_value(brand_metrics, "gaap_operating_margin", 0.10)
        scenarios = [
            FinanceScenario(
                scenario_id="fs_001",
                brand_id=brand_id,
                scenario_name="Base case",
                revenue_growth=round(max(base_growth, 0.03), 4),
                operating_margin=round(max(base_margin, 0.06), 4),
                discount_rate=0.12,
                terminal_growth=0.03,
                sensitivity_axis_x="revenue_growth",
                sensitivity_axis_y="operating_margin",
                result_value=round((1 + max(base_growth, 0.03)) * max(base_margin, 0.06) / 0.12, 4),
                notes="Educational DCF-style sensitivity proxy; not investment advice.",
            ),
            FinanceScenario(
                scenario_id="fs_002",
                brand_id=brand_id,
                scenario_name="Margin pressure",
                revenue_growth=round(max(base_growth, 0.03), 4),
                operating_margin=round(max(base_margin - 0.03, 0.03), 4),
                discount_rate=0.13,
                terminal_growth=0.02,
                sensitivity_axis_x="discount_rate",
                sensitivity_axis_y="operating_margin",
                result_value=round((1 + max(base_growth, 0.03)) * max(base_margin - 0.03, 0.03) / 0.13, 4),
                notes="Shows downside if price competition compresses margins.",
            ),
        ]
        return ToolResponse(
            success=True,
            data={
                "assumptions": [assumption.to_dict() for assumption in assumptions],
                "scenarios": [scenario.to_dict() for scenario in scenarios],
            },
            error="",
        )


def _metric_value(metrics: list[FinanceMetric], metric_name: str, fallback: float) -> float:
    for metric in metrics:
        if metric.metric_name == metric_name:
            return metric.metric_value
    return fallback
```

- [x] **Step 6: Run tool tests and full tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_tools.py -q
.\.venv\Scripts\python -m pytest -q
```

Expected: all tests pass.

- [x] **Step 7: Commit Task 3**

```powershell
git add data/finance_metrics.csv src/marketlens/agent/tools.py src/marketlens/agent/finance.py tests/test_agent_tools.py
git commit -m "feat: add evidence and finance tools"
```

---

### Task 4: LLM Provider And Specialized Agents

**Files:**
- Create: `.env.example`
- Create: `src/marketlens/agent/llm.py`
- Create: `src/marketlens/agent/agents.py`
- Test: `tests/test_agent_agents.py`

- [x] **Step 1: Write failing agent tests**

Create `tests/test_agent_agents.py`:

```python
from pathlib import Path

from marketlens.agent.agents import (
    FinanceLensAgent,
    PlannerAgent,
    TriageAgent,
    WriterAgent,
)
from marketlens.agent.finance import FinanceModelTool, load_finance_metrics
from marketlens.agent.tools import EvidenceSearchTool
from marketlens.load import load_evidence


ROOT = Path(__file__).resolve().parents[1]


def test_triage_agent_routes_finance_question():
    agent = TriageAgent()

    result = agent.run({"query": "瑞幸价格战对 DCF 和利润率有什么影响？"})

    assert result["intent"] == "finance_analysis_needed"


def test_planner_agent_creates_three_to_five_tasks():
    agent = PlannerAgent()

    result = agent.run({"query": "分析霸王茶姬扩张是否过快"})

    assert 3 <= len(result["tasks"]) <= 5
    assert all("query" in task for task in result["tasks"])


def test_finance_lens_agent_uses_finance_tool():
    metrics = load_finance_metrics(ROOT / "data" / "finance_metrics.csv")
    agent = FinanceLensAgent(FinanceModelTool(metrics))

    result = agent.run({"brand_id": "luckin"})

    assert result["assumptions"]
    assert result["scenarios"]


def test_writer_agent_cites_evidence_ids():
    rows = load_evidence(ROOT / "data" / "evidence.csv")
    evidence_response = EvidenceSearchTool(rows).run({"query": "利润率", "brand_id": "luckin"})
    agent = WriterAgent()

    result = agent.run(
        {
            "query": "瑞幸价格战对利润率有什么影响？",
            "intent": "local_evidence_qa",
            "evidence": evidence_response.data["evidence"],
            "finance": {},
        }
    )

    assert "EV-" in result["answer"]
    assert result["supporting_evidence_ids"]
```

- [x] **Step 2: Run agent tests and verify failure**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_agents.py -q
```

Expected: failure because `llm.py` and `agents.py` do not exist.

- [x] **Step 3: Add environment example**

Create `.env.example`:

```text
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
MARKETLENS_AGENT_MODE=fallback
MARKETLENS_API_HOST=127.0.0.1
MARKETLENS_API_PORT=8765
```

- [x] **Step 4: Implement LLM clients**

Create `src/marketlens/agent/llm.py`:

```python
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResult:
    content: str
    provider: str


class FallbackLLMClient:
    provider = "fallback"

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResult:
        return LLMResult(content=user_prompt, provider=self.provider)


class DeepSeekLLMClient:
    provider = "deepseek"

    def __init__(self) -> None:
        self._api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self._base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        self._model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResult:
        if not self._api_key:
            return FallbackLLMClient().complete(system_prompt, user_prompt)
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return LLMResult(content=content, provider=self.provider)
```

- [x] **Step 5: Implement deterministic specialized agents**

Create `src/marketlens/agent/agents.py`:

```python
from __future__ import annotations

from typing import Any

from marketlens.agent.finance import FinanceModelTool


class TriageAgent:
    name = "TriageAgent"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = str(payload["query"])
        lowered = query.lower()
        finance_terms = ("dcf", "估值", "利润率", "毛利率", "单店", "回本", "margin", "valuation")
        research_terms = ("最新", "搜索", "上网", "补充", "新闻", "2026", "新资料")
        if any(term in lowered for term in finance_terms):
            intent = "finance_analysis_needed"
        elif any(term in lowered for term in research_terms):
            intent = "new_research_needed"
        elif "报告" in query or "简报" in query:
            intent = "report_generation_needed"
        else:
            intent = "local_evidence_qa"
        return {"intent": intent}


class PlannerAgent:
    name = "PlannerAgent"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = str(payload["query"])
        tasks = [
            {
                "title": "Business context",
                "intent": "Clarify brand, period, and business question.",
                "query": query,
            },
            {
                "title": "Operating evidence",
                "intent": "Find store count, GMV, revenue, margin, or franchise evidence.",
                "query": f"{query} 门店 GMV 收入 利润率 加盟",
            },
            {
                "title": "Risk and contradiction check",
                "intent": "Find risk signals and conflicting evidence.",
                "query": f"{query} 风险 同店 增长 放缓 竞争",
            },
        ]
        if "DCF" in query.upper() or "估值" in query:
            tasks.append(
                {
                    "title": "Finance assumptions",
                    "intent": "Collect assumptions for DCF-style sensitivity.",
                    "query": f"{query} DCF 折现率 估值 假设",
                }
            )
        return {"tasks": tasks[:5]}


class SearchAgent:
    name = "SearchAgent"

    def __init__(self, search_tool: Any) -> None:
        self._search_tool = search_tool

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._search_tool.run({"query": payload["query"], "limit": payload.get("limit", 5)})
        return {"success": response.success, "results": response.data, "error": response.error}


class EvidenceExtractorAgent:
    name = "EvidenceExtractorAgent"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        source_results = payload.get("source_results", {})
        extracted = []
        for index, item in enumerate(source_results.get("web", [])[:5], start=1):
            extracted.append(
                {
                    "evidence_id": f"AGENT-EV-{index:03d}",
                    "brand_id": payload.get("brand_id", "unknown"),
                    "lens": payload.get("lens", "risk"),
                    "claim": item.get("title", ""),
                    "source_title": item.get("title", ""),
                    "source_url": item.get("url", ""),
                    "source_type": "news",
                    "source_date": payload.get("source_date", "2026-06-20"),
                    "excerpt": item.get("description", ""),
                    "confidence": 0.62,
                    "review_status": "needs_review",
                    "notes": "Agent-extracted candidate evidence.",
                }
            )
        return {"evidence": extracted}


class VerifierAgent:
    name = "VerifierAgent"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        approved = []
        rejected = []
        for row in payload.get("evidence", []):
            if row.get("source_url", "").startswith(("http://", "https://")) and row.get("claim"):
                approved.append(row)
            else:
                rejected.append(row)
        return {"approved": approved, "rejected": rejected}


class FinanceLensAgent:
    name = "FinanceLensAgent"

    def __init__(self, finance_tool: FinanceModelTool) -> None:
        self._finance_tool = finance_tool

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._finance_tool.run({"brand_id": payload["brand_id"]})
        if not response.success:
            return {"assumptions": [], "scenarios": [], "error": response.error}
        return response.data


class WriterAgent:
    name = "WriterAgent"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        query = str(payload["query"])
        evidence = payload.get("evidence", [])
        finance = payload.get("finance", {})
        evidence_ids = [row["evidence_id"] for row in evidence[:5] if row.get("evidence_id")]
        if not evidence_ids:
            return {
                "answer": "当前证据不足，系统需要先补充公开来源后再回答。",
                "supporting_evidence_ids": [],
            }
        evidence_sentence = "、".join(evidence_ids)
        finance_sentence = ""
        if finance.get("assumptions"):
            finance_sentence = " FinanceLensAgent 已生成经营假设和敏感性分析；这些输出仅用于学习研究，不构成投资建议。"
        answer = (
            f"针对“{query}”，当前证据显示需要重点看价格/扩张对利润率和增长质量的影响。"
            f"支持证据包括 {evidence_sentence}。{finance_sentence}"
        )
        return {"answer": answer, "supporting_evidence_ids": evidence_ids}
```

- [x] **Step 6: Run agent tests and full tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_agents.py -q
.\.venv\Scripts\python -m pytest -q
```

Expected: all tests pass.

- [x] **Step 7: Commit Task 4**

```powershell
git add .env.example src/marketlens/agent/llm.py src/marketlens/agent/agents.py tests/test_agent_agents.py
git commit -m "feat: add market research agents"
```

---

### Task 5: Orchestrator And FastAPI API

**Files:**
- Create: `src/marketlens/agent/orchestrator.py`
- Create: `src/marketlens/api.py`
- Test: `tests/test_agent_orchestrator.py`
- Test: `tests/test_api.py`

- [x] **Step 1: Write failing orchestrator tests**

Create `tests/test_agent_orchestrator.py`:

```python
from pathlib import Path

from marketlens.agent.orchestrator import MarketLensAgentOrchestrator


ROOT = Path(__file__).resolve().parents[1]


def test_orchestrator_answers_local_evidence_question(tmp_path):
    orchestrator = MarketLensAgentOrchestrator(
        evidence_path=ROOT / "data" / "evidence.csv",
        finance_metrics_path=ROOT / "data" / "finance_metrics.csv",
        session_dir=tmp_path / "sessions",
        firecrawl_output_dir=tmp_path / "firecrawl",
    )

    run = orchestrator.answer("瑞幸价格战对利润率有什么影响？")

    assert run.status == "completed"
    assert run.supporting_evidence_ids
    assert "TriageAgent" in run.agents_invoked
    assert run.trace_events


def test_orchestrator_finance_question_returns_assumptions(tmp_path):
    orchestrator = MarketLensAgentOrchestrator(
        evidence_path=ROOT / "data" / "evidence.csv",
        finance_metrics_path=ROOT / "data" / "finance_metrics.csv",
        session_dir=tmp_path / "sessions",
        firecrawl_output_dir=tmp_path / "firecrawl",
    )

    run = orchestrator.answer("帮我用 DCF 分析瑞幸价格战对估值的影响")

    assert run.intent == "finance_analysis_needed"
    assert run.finance_assumptions
    assert run.finance_scenarios
```

- [x] **Step 2: Write failing API tests**

Create `tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from marketlens.api import create_app


def test_agent_chat_endpoint_returns_run_payload():
    app = create_app()
    client = TestClient(app)

    response = client.post("/api/agent/chat", json={"query": "瑞幸价格战对利润率有什么影响？"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"].startswith("run_")
    assert payload["answer"]
    assert payload["trace_events"]


def test_agent_chat_endpoint_rejects_empty_query():
    app = create_app()
    client = TestClient(app)

    response = client.post("/api/agent/chat", json={"query": "  "})

    assert response.status_code == 422
```

- [x] **Step 3: Run orchestrator/API tests and verify failure**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_orchestrator.py tests/test_api.py -q
```

Expected: failure because orchestrator and API do not exist.

- [x] **Step 4: Implement orchestrator**

Create `src/marketlens/agent/orchestrator.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from marketlens.agent.agents import FinanceLensAgent, PlannerAgent, TriageAgent, WriterAgent
from marketlens.agent.finance import FinanceModelTool, load_finance_metrics
from marketlens.agent.models import AgentRun, FinanceAssumption, FinanceScenario, ToolCallRecord
from marketlens.agent.runtime import TodoBoard
from marketlens.agent.session import SessionStore
from marketlens.agent.tools import EvidenceSearchTool, FirecrawlSearchTool
from marketlens.agent.trace import TraceLogger
from marketlens.load import load_evidence


class MarketLensAgentOrchestrator:
    def __init__(
        self,
        evidence_path: Path,
        finance_metrics_path: Path,
        session_dir: Path,
        firecrawl_output_dir: Path,
    ) -> None:
        self._evidence_path = evidence_path
        self._finance_metrics_path = finance_metrics_path
        self._session_store = SessionStore(session_dir)
        self._firecrawl_output_dir = firecrawl_output_dir

    def answer(self, query: str) -> AgentRun:
        started_at = _now()
        run_id = f"run_{uuid4().hex[:10]}"
        session_id = "local_session"
        trace = TraceLogger(run_id)
        todo = TodoBoard(run_id)
        agents_invoked: list[str] = []
        tool_calls: list[ToolCallRecord] = []

        rows = load_evidence(self._evidence_path)
        metrics = load_finance_metrics(self._finance_metrics_path)

        triage = TriageAgent()
        agents_invoked.append(triage.name)
        triage_result = triage.run({"query": query})
        intent = triage_result["intent"]
        trace.record(triage.name, "intent", f"Classified query as {intent}.", query, intent, "", "", 1)

        brand_id = _infer_brand_id(query)
        lens = _infer_lens(query, intent)
        evidence_tool = EvidenceSearchTool(rows)
        evidence_response = evidence_tool.run({"query": query, "brand_id": brand_id, "lens": lens})
        tool_calls.append(
            ToolCallRecord(
                tool_name=evidence_tool.name,
                input_summary=f"brand_id={brand_id}, lens={lens}",
                output_summary=f"{len(evidence_response.data.get('evidence', []))} rows",
                status="success" if evidence_response.success else "failed",
                latency_ms=1,
            )
        )
        trace.record(
            "EvidenceSearchTool",
            "tool_call",
            f"Found {len(evidence_response.data.get('evidence', []))} local evidence rows.",
            query,
            str(evidence_response.data.get("evidence", [])[:2]),
            evidence_tool.name,
            "success" if evidence_response.success else "failed",
            1,
        )

        evidence = evidence_response.data.get("evidence", [])
        planner = PlannerAgent()
        if intent == "new_research_needed" or len(evidence) < 2:
            agents_invoked.append(planner.name)
            plan = planner.run({"query": query})
            for task in plan["tasks"]:
                item = todo.add(task["title"], task["intent"], task["query"], planner.name)
                todo.complete(item.todo_id, "Planned for research escalation.", [])
            search_tool = FirecrawlSearchTool(self._firecrawl_output_dir)
            tool_calls.append(
                ToolCallRecord(
                    tool_name=search_tool.name,
                    input_summary="research escalation prepared",
                    output_summary="not executed in fallback tests",
                    status="prepared",
                    latency_ms=0,
                )
            )
            trace.record(planner.name, "planning", f"Created {len(plan['tasks'])} research tasks.", query, str(plan["tasks"]), "", "", 1)

        finance_payload = {"assumptions": [], "scenarios": []}
        if intent == "finance_analysis_needed":
            finance_agent = FinanceLensAgent(FinanceModelTool(metrics))
            agents_invoked.append(finance_agent.name)
            finance_payload = finance_agent.run({"brand_id": brand_id})
            trace.record(
                finance_agent.name,
                "finance",
                f"Generated {len(finance_payload.get('assumptions', []))} finance assumptions.",
                brand_id,
                str(finance_payload.get("assumptions", [])[:2]),
                "FinanceModelTool",
                "success",
                1,
            )

        finance_assumptions = [
            FinanceAssumption(**item) for item in finance_payload.get("assumptions", [])
        ]
        finance_scenarios = [
            FinanceScenario(**item) for item in finance_payload.get("scenarios", [])
        ]

        writer = WriterAgent()
        agents_invoked.append(writer.name)
        writer_result = writer.run(
            {
                "query": query,
                "intent": intent,
                "evidence": evidence,
                "finance": finance_payload,
            }
        )
        trace.record(writer.name, "answer", "Generated cited answer.", query, writer_result["answer"], "", "", 1)

        run = AgentRun(
            run_id=run_id,
            session_id=session_id,
            user_query=query,
            intent=intent,
            started_at=started_at,
            completed_at=_now(),
            status="completed",
            agents_invoked=agents_invoked,
            tool_calls=tool_calls,
            trace_events=trace.events(),
            todo_items=todo.items(),
            answer=writer_result["answer"],
            supporting_evidence_ids=writer_result["supporting_evidence_ids"],
            finance_assumptions=finance_assumptions,
            finance_scenarios=finance_scenarios,
            error_message="",
        )
        self._session_store.save_run(run)
        return run


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _infer_brand_id(query: str) -> str:
    brand_map = {
        "瑞幸": "luckin",
        "luckin": "luckin",
        "库迪": "cotti",
        "星巴克": "starbucks",
        "蜜雪": "mixue",
        "霸王": "chagee",
        "chagee": "chagee",
        "古茗": "guming",
        "茶百道": "chapanda",
    }
    lowered = query.lower()
    for key, brand_id in brand_map.items():
        if key.lower() in lowered:
            return brand_id
    return "luckin"


def _infer_lens(query: str, intent: str) -> str:
    if intent == "finance_analysis_needed":
        return ""
    if "加盟" in query:
        return "franchise"
    if "扩张" in query or "门店" in query:
        return "expansion"
    if "价格" in query:
        return "pricing"
    if "风险" in query or "利润率" in query:
        return "risk"
    return ""
```

- [x] **Step 5: Implement FastAPI app**

Create `src/marketlens/api.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from marketlens.agent.orchestrator import MarketLensAgentOrchestrator


class ChatRequest(BaseModel):
    query: str = Field(min_length=1)


def create_app() -> FastAPI:
    app = FastAPI(title="MarketLens Agent API")
    root = Path(__file__).resolve().parents[2]
    orchestrator = MarketLensAgentOrchestrator(
        evidence_path=root / "data" / "evidence.csv",
        finance_metrics_path=root / "data" / "finance_metrics.csv",
        session_dir=root / "work" / "agent_sessions",
        firecrawl_output_dir=root / ".firecrawl",
    )

    @app.post("/api/agent/chat")
    def chat(request: ChatRequest) -> dict[str, Any]:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=422, detail="query must not be empty")
        return orchestrator.answer(query).to_dict()

    @app.get("/api/agent/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        session_path = root / "work" / "agent_sessions" / f"{run_id}.json"
        if not session_path.exists():
            raise HTTPException(status_code=404, detail="run not found")
        import json

        return json.loads(session_path.read_text(encoding="utf-8"))

    return app


app = create_app()
```

- [x] **Step 6: Run orchestrator/API tests and full tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_agent_orchestrator.py tests/test_api.py -q
.\.venv\Scripts\python -m pytest -q
```

Expected: all tests pass.

- [x] **Step 7: Smoke test local API**

Run:

```powershell
.\.venv\Scripts\python -m uvicorn marketlens.api:app --host 127.0.0.1 --port 8765
```

In another terminal:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/api/agent/chat -ContentType 'application/json' -Body '{"query":"瑞幸价格战对利润率有什么影响？"}'
```

Expected: JSON payload includes `run_id`, `answer`, `trace_events`, and `supporting_evidence_ids`.

- [x] **Step 8: Commit Task 5**

```powershell
git add src/marketlens/agent/orchestrator.py src/marketlens/api.py tests/test_agent_orchestrator.py tests/test_api.py
git commit -m "feat: expose marketlens agent api"
```

---

### Task 6: Agent Demo Artifact And React Agent Console

**Files:**
- Modify: `scripts/build_artifacts.py`
- Create: `web/src/types/agent.ts`
- Create: `web/src/components/AgentTrace.tsx`
- Create: `web/src/components/FinanceLens.tsx`
- Create: `web/src/components/AgentConsole.tsx`
- Modify: `web/src/App.tsx`
- Modify: `web/src/styles.css`
- Modify: `web/vite.config.ts`

- [x] **Step 1: Add deterministic agent demo artifact generation**

Modify `scripts/build_artifacts.py` imports:

```python
from marketlens.agent.orchestrator import MarketLensAgentOrchestrator
```

Add this helper above `main()`:

```python
def write_agent_demo(root: Path, evidence_path: Path) -> None:
    orchestrator = MarketLensAgentOrchestrator(
        evidence_path=evidence_path,
        finance_metrics_path=root / "data" / "finance_metrics.csv",
        session_dir=root / "work" / "agent_demo_sessions",
        firecrawl_output_dir=root / ".firecrawl",
    )
    demo_run = orchestrator.answer("瑞幸价格战对利润率和 DCF 假设有什么影响？")
    write_json(root / "data" / "processed" / "agent_demo.json", demo_run.to_dict())
```

Call it in `main()` after brief exports:

```python
    write_agent_demo(root, evidence_path)
```

Add `"agent_demo.json"` to `copy_artifacts()`:

```python
    for name in ("brands.json", "evidence.json", "brief_sections.json", "brief.md", "brief.html", "agent_demo.json"):
```

- [x] **Step 2: Run artifact build**

Run:

```powershell
.\.venv\Scripts\python scripts/build_artifacts.py
```

Expected: `web/src/data/agent_demo.json` and `web/public/data/agent_demo.json` exist.

- [x] **Step 3: Add TypeScript agent types**

Create `web/src/types/agent.ts`:

```ts
export type ToolCallRecord = {
  tool_name: string;
  input_summary: string;
  output_summary: string;
  status: string;
  latency_ms: number;
};

export type TraceEvent = {
  event_id: string;
  run_id: string;
  timestamp: string;
  agent_name: string;
  event_type: string;
  summary: string;
  input_preview: string;
  output_preview: string;
  tool_name: string;
  tool_status: string;
  latency_ms: number;
};

export type TodoItem = {
  todo_id: string;
  run_id: string;
  title: string;
  intent: string;
  query: string;
  status: string;
  assigned_agent: string;
  supporting_source_urls: string[];
  result_summary: string;
};

export type FinanceAssumption = {
  assumption_id: string;
  brand_id: string;
  metric_name: string;
  metric_value: number;
  unit: string;
  period: string;
  formula: string;
  source_evidence_ids: string[];
  confidence: number;
  notes: string;
};

export type FinanceScenario = {
  scenario_id: string;
  brand_id: string;
  scenario_name: string;
  revenue_growth: number;
  operating_margin: number;
  discount_rate: number;
  terminal_growth: number;
  sensitivity_axis_x: string;
  sensitivity_axis_y: string;
  result_value: number;
  notes: string;
};

export type AgentRun = {
  run_id: string;
  session_id: string;
  user_query: string;
  intent: string;
  started_at: string;
  completed_at: string;
  status: string;
  agents_invoked: string[];
  tool_calls: ToolCallRecord[];
  trace_events: TraceEvent[];
  todo_items: TodoItem[];
  answer: string;
  supporting_evidence_ids: string[];
  finance_assumptions: FinanceAssumption[];
  finance_scenarios: FinanceScenario[];
  error_message: string;
};
```

- [x] **Step 4: Add trace component**

Create `web/src/components/AgentTrace.tsx`:

```tsx
import { Activity, CheckCircle2, ListTodo, Wrench } from "lucide-react";
import type { AgentRun } from "../types/agent";

function AgentTrace({ run }: { run: AgentRun }) {
  return (
    <section className="agent-trace" aria-label="Agent execution trace">
      <div className="agent-block">
        <div className="agent-block__header">
          <ListTodo size={17} />
          <h3>Todo Board</h3>
        </div>
        <div className="todo-stack">
          {run.todo_items.length === 0 ? (
            <p className="agent-muted">Local evidence was sufficient; no research escalation needed.</p>
          ) : (
            run.todo_items.map((item) => (
              <article className="todo-card" key={item.todo_id}>
                <span>{item.status}</span>
                <strong>{item.title}</strong>
                <p>{item.intent}</p>
              </article>
            ))
          )}
        </div>
      </div>

      <div className="agent-block">
        <div className="agent-block__header">
          <Activity size={17} />
          <h3>Trace Timeline</h3>
        </div>
        <ol className="trace-list">
          {run.trace_events.map((event) => (
            <li key={event.event_id}>
              <CheckCircle2 size={15} />
              <div>
                <strong>{event.agent_name}</strong>
                <p>{event.summary}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div className="agent-block">
        <div className="agent-block__header">
          <Wrench size={17} />
          <h3>Tool Calls</h3>
        </div>
        <div className="tool-grid">
          {run.tool_calls.map((call) => (
            <article className="tool-card" key={`${call.tool_name}-${call.input_summary}`}>
              <strong>{call.tool_name}</strong>
              <span>{call.status}</span>
              <p>{call.output_summary}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export { AgentTrace };
```

- [x] **Step 5: Add finance component**

Create `web/src/components/FinanceLens.tsx`:

```tsx
import { Calculator } from "lucide-react";
import type { AgentRun } from "../types/agent";

function formatMetric(value: number, unit: string) {
  if (unit === "ratio") return `${(value * 100).toFixed(1)}%`;
  if (unit === "stores") return Math.round(value).toLocaleString("zh-CN");
  return String(value);
}

function FinanceLens({ run }: { run: AgentRun }) {
  return (
    <section className="finance-lens" aria-label="Finance Lens">
      <div className="agent-block__header">
        <Calculator size={17} />
        <h3>Finance Lens</h3>
      </div>
      {run.finance_assumptions.length === 0 ? (
        <p className="agent-muted">This answer did not require finance assumptions.</p>
      ) : (
        <>
          <div className="assumption-grid">
            {run.finance_assumptions.map((assumption) => (
              <article className="assumption-card" key={assumption.assumption_id}>
                <span>{assumption.period}</span>
                <strong>{assumption.metric_name.replaceAll("_", " ")}</strong>
                <b>{formatMetric(assumption.metric_value, assumption.unit)}</b>
                <p>{assumption.notes}</p>
                <small>Evidence: {assumption.source_evidence_ids.join(", ")}</small>
              </article>
            ))}
          </div>
          <div className="scenario-table">
            {run.finance_scenarios.map((scenario) => (
              <article key={scenario.scenario_id}>
                <strong>{scenario.scenario_name}</strong>
                <span>Growth {(scenario.revenue_growth * 100).toFixed(1)}%</span>
                <span>Margin {(scenario.operating_margin * 100).toFixed(1)}%</span>
                <span>Discount {(scenario.discount_rate * 100).toFixed(1)}%</span>
                <b>{scenario.result_value.toFixed(2)}</b>
              </article>
            ))}
          </div>
          <p className="agent-caveat">DCF-style output is educational analysis, not investment advice.</p>
        </>
      )}
    </section>
  );
}

export { FinanceLens };
```

- [x] **Step 6: Add Agent Console component**

Create `web/src/components/AgentConsole.tsx`:

```tsx
import { Bot, Send, Sparkles } from "lucide-react";
import { useState } from "react";
import demoRun from "../data/agent_demo.json";
import type { AgentRun } from "../types/agent";
import { AgentTrace } from "./AgentTrace";
import { FinanceLens } from "./FinanceLens";

const starterQuestions = [
  "瑞幸价格战对利润率有什么影响？",
  "帮我用 DCF 分析瑞幸价格战对估值的影响",
  "霸王茶姬扩张是不是过快？",
];

function AgentConsole() {
  const [query, setQuery] = useState(starterQuestions[0]);
  const [run, setRun] = useState<AgentRun>(demoRun as AgentRun);
  const [isLoading, setIsLoading] = useState(false);

  async function submit(nextQuery = query) {
    const trimmed = nextQuery.trim();
    if (!trimmed) return;
    setQuery(trimmed);
    setIsLoading(true);
    try {
      const response = await fetch("/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setRun((await response.json()) as AgentRun);
    } catch {
      setRun(demoRun as AgentRun);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="agent-console" aria-label="MarketLens Agent Console">
      <div className="agent-chat">
        <p className="eyebrow">
          <Sparkles size={15} />
          Agentic Research Console
        </p>
        <h1>MarketLens Agent</h1>
        <p className="hero-subtitle">
          Ask a brand research question. The agent checks local evidence, plans new research when needed,
          calls tools, records traces, and turns operating evidence into finance assumptions.
        </p>
        <div className="chat-box">
          <Bot size={19} />
          <textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={3} />
          <button onClick={() => submit()} disabled={isLoading}>
            <Send size={17} />
            {isLoading ? "Running" : "Run"}
          </button>
        </div>
        <div className="starter-row">
          {starterQuestions.map((question) => (
            <button key={question} onClick={() => submit(question)}>
              {question}
            </button>
          ))}
        </div>
        <article className="agent-answer">
          <span>{run.intent}</span>
          <p>{run.answer}</p>
          <small>Evidence: {run.supporting_evidence_ids.join(", ") || "Needs research"}</small>
        </article>
      </div>
      <AgentTrace run={run} />
      <FinanceLens run={run} />
    </section>
  );
}

export { AgentConsole };
```

- [x] **Step 7: Render Agent Console in App**

Modify `web/src/App.tsx`:

```tsx
import { AgentConsole } from "./components/AgentConsole";
```

Then inside `<section className="workspace">`, render it before the existing `<header className="hero-panel">`:

```tsx
        <AgentConsole />
```

- [x] **Step 8: Add Vite proxy**

Modify `web/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8765",
    },
  },
});
```

- [x] **Step 9: Add Agent Console styles**

Append to `web/src/styles.css`:

```css
.agent-console {
  display: grid;
  grid-template-columns: minmax(360px, 0.9fr) minmax(420px, 1.1fr) minmax(320px, 0.85fr);
  gap: 16px;
  margin-bottom: 18px;
}

.agent-chat,
.agent-trace,
.finance-lens,
.agent-block {
  border: 1px solid rgba(43, 79, 64, 0.15);
  background: rgba(251, 247, 237, 0.94);
  box-shadow: 0 11px 36px rgba(33, 47, 39, 0.09);
}

.agent-chat,
.agent-trace,
.finance-lens {
  padding: 22px;
}

.agent-chat h1 {
  font-size: clamp(38px, 4.8vw, 64px);
}

.chat-box {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  margin: 18px 0 12px;
  border: 1px solid rgba(34, 48, 41, 0.16);
  background: #fffaf0;
  padding: 12px;
}

.chat-box textarea {
  width: 100%;
  resize: vertical;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--ink);
  line-height: 1.45;
}

.chat-box button,
.starter-row button {
  border: 1px solid rgba(34, 48, 41, 0.16);
  background: var(--rail);
  color: #fff8e9;
  padding: 10px 12px;
  font-weight: 800;
  cursor: pointer;
}

.starter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.starter-row button {
  background: rgba(255, 250, 240, 0.72);
  color: var(--green);
}

.agent-answer {
  margin-top: 16px;
  border-left: 4px solid var(--wine);
  background: var(--wine-soft);
  padding: 14px;
}

.agent-answer span,
.todo-card span,
.tool-card span,
.assumption-card span {
  display: inline-flex;
  width: fit-content;
  margin-bottom: 8px;
  color: var(--wine);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.agent-answer p,
.agent-muted,
.todo-card p,
.tool-card p,
.assumption-card p,
.agent-caveat {
  color: var(--muted);
  line-height: 1.55;
}

.agent-block {
  padding: 16px;
  margin-bottom: 12px;
}

.agent-block__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--green);
}

.agent-block__header h3 {
  margin: 0;
  font-size: 16px;
}

.todo-stack,
.tool-grid,
.assumption-grid,
.scenario-table {
  display: grid;
  gap: 10px;
}

.todo-card,
.tool-card,
.assumption-card,
.scenario-table article {
  border: 1px solid rgba(34, 48, 41, 0.12);
  background: rgba(255, 250, 240, 0.72);
  padding: 12px;
}

.todo-card strong,
.tool-card strong,
.assumption-card strong,
.scenario-table strong {
  display: block;
  margin-bottom: 6px;
}

.trace-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.trace-list li {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr);
  gap: 8px;
  align-items: start;
}

.trace-list p {
  margin: 4px 0 0;
  color: var(--muted);
  line-height: 1.45;
}

.assumption-card b,
.scenario-table b {
  display: block;
  color: var(--ink);
  font-family: Georgia, "Times New Roman", serif;
  font-size: 24px;
}

.assumption-card small {
  color: var(--indigo);
  font-weight: 800;
}

.scenario-table article {
  display: grid;
  grid-template-columns: 1.2fr repeat(4, auto);
  gap: 8px;
  align-items: center;
}

@media (max-width: 1180px) {
  .agent-console {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .chat-box {
    grid-template-columns: 1fr;
  }

  .scenario-table article {
    grid-template-columns: 1fr;
  }
}
```

- [x] **Step 10: Build frontend**

Run:

```powershell
cd web
npm run build
cd ..
```

Expected: TypeScript and Vite build succeed.

- [x] **Step 11: Run full verification**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q
cd web
npm run build
cd ..
```

Expected: all tests pass and frontend builds.

- [x] **Step 12: Commit Task 6**

```powershell
git add scripts/build_artifacts.py web/src/types/agent.ts web/src/components/AgentTrace.tsx web/src/components/FinanceLens.tsx web/src/components/AgentConsole.tsx web/src/App.tsx web/src/styles.css web/vite.config.ts web/src/data/agent_demo.json web/public/data/agent_demo.json data/processed/agent_demo.json
git commit -m "feat: add agent research console"
```

---

### Task 7: Documentation, Resume Story, Screenshots, Final Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/interview_talking_points.md`
- Modify: `docs/application_materials/ai_agent_application_version.md`
- Optional update after resume regeneration: files under `deliverables/` stay ignored.

- [ ] **Step 1: Update README positioning**

Modify `README.md` so the top section starts with this positioning:

```markdown
# MarketLens Agent

MarketLens Agent is a lightweight multi-agent research console for Chinese fresh beverage brands. It combines local evidence Q&A, Agentic RAG, Firecrawl-ready web research, source-backed evidence extraction, traceable tool calls, and finance-oriented analysis.

The project is designed as an AI Agent / business analysis portfolio project. It is not an investment recommendation tool and does not use private company data.

## What The Agent Demonstrates

- AI Research Chat over a local evidence database
- Triage, planning, evidence search, finance analysis, and cited writing agents
- ToolResponse, ToolRegistry, SessionStore, TraceLogger, and TodoBoard primitives
- Evidence IDs on every supported answer
- FinanceLens assumptions for store count, margin, franchise model, and DCF-style sensitivity
- React Agent Console with todo board, trace timeline, tool calls, evidence, and finance output
```

- [ ] **Step 2: Add run instructions to README**

Add:

````markdown
## Run Locally

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python scripts/build_artifacts.py
.\.venv\Scripts\python -m uvicorn marketlens.api:app --host 127.0.0.1 --port 8765
```

In another terminal:

```powershell
cd web
npm install
npm run dev
```

Open the Vite URL and ask one of:

- 瑞幸价格战对利润率有什么影响？
- 帮我用 DCF 分析瑞幸价格战对估值的影响
- 霸王茶姬扩张是不是过快？
````

- [ ] **Step 3: Update AI Agent application material**

Modify `docs/application_materials/ai_agent_application_version.md` with this project label:

```markdown
# AI Agent / AI Workflow Application Version

## Project Label

MarketLens Agent: multi-agent research console for source-backed brand and finance analysis

## Resume Bullet

自研 MarketLens Agent 多智能体研究系统，基于 DeepSeek-compatible LLM 接口与 Firecrawl-ready 搜索工具实现 Triage / Planner / Search / Evidence Extractor / Verifier / FinanceLens / Writer 协作，支持证据库问答、自动补证、工具调用轨迹、会话记忆及品牌单店模型/DCF 假设分析。

## 60-Second Interview Explanation

这个项目最开始只是一个 source-to-brief 工作流，但我后来把它升级成了轻量 Agent Runtime。用户可以在 Chat 里提出品牌研究问题，系统会先判断本地证据库是否足够，如果不够就用 Planner 拆任务，再通过 SearchAgent 调 Firecrawl 搜索公开资料，Extractor 抽取结构化证据，Verifier 做来源和冲突检查。涉及金融问题时，FinanceLensAgent 会把门店数、GMV、毛利率、加盟服务收入这些证据转成单店模型和 DCF 假设。前端会展示 todo board、tool calls、trace logs 和 evidence IDs，所以它不是只调 API 写总结，而是一个有规划、工具、记忆、证据和可观测性的 Agent 系统。
```

- [ ] **Step 4: Update interview talking points**

Modify `docs/interview_talking_points.md` with a new section:

```markdown
## MarketLens Agent v2 Talking Points

- Why it is an Agent: it has intent triage, planning, tool calls, state, trace logs, and evidence-grounded output.
- Why it is not only RAG: local Evidence DB is the first retrieval layer; when evidence is insufficient, the agent can escalate to web research.
- Why finance matters: public operating metrics are mapped into assumptions such as store growth, store-level margin, franchise economics, and DCF-style sensitivity.
- How hallucination is controlled: WriterAgent refuses unsupported claims, VerifierAgent rejects missing-source rows, and every answer includes evidence IDs.
- What I built myself: lightweight runtime, data model, tools, orchestration, API, and React console.
```

- [ ] **Step 5: Run final tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts/build_artifacts.py
cd web
npm run build
cd ..
```

Expected:

- pytest passes,
- artifact build succeeds,
- TypeScript/Vite build succeeds.

- [ ] **Step 6: Start servers for visual verification**

Run API server:

```powershell
.\.venv\Scripts\python -m uvicorn marketlens.api:app --host 127.0.0.1 --port 8765
```

Run frontend in another terminal:

```powershell
cd web
npm run dev
```

Expected:

- API is reachable at `http://127.0.0.1:8765/api/agent/chat`,
- frontend is reachable at Vite local URL,
- Agent Console is the first major product surface,
- asking a finance question returns evidence IDs and Finance Lens output.

- [ ] **Step 7: Capture screenshots**

Use Playwright or the existing screenshot workflow to capture:

- desktop Agent Console,
- mobile Agent Console,
- Evidence DB tab,
- Finance Lens output.

Save screenshots under `screenshots/` with names:

```text
screenshots/marketlens-agent-desktop.png
screenshots/marketlens-agent-mobile.png
screenshots/marketlens-agent-finance.png
```

- [ ] **Step 8: Commit documentation and verification assets**

```powershell
git add README.md docs/interview_talking_points.md docs/application_materials/ai_agent_application_version.md screenshots/marketlens-agent-desktop.png screenshots/marketlens-agent-mobile.png screenshots/marketlens-agent-finance.png
git commit -m "docs: document marketlens agent workflow"
```

---

## Final Acceptance Checklist

- [ ] `.\.venv\Scripts\python -m pytest -q` passes.
- [ ] `.\.venv\Scripts\python scripts/build_artifacts.py` succeeds.
- [ ] `npm run build` succeeds in `web/`.
- [ ] API returns an AgentRun payload from `/api/agent/chat`.
- [ ] Frontend renders Agent Console before the old dashboard.
- [ ] Chat answer includes evidence IDs.
- [ ] Trace timeline shows agent/tool events.
- [ ] FinanceLens shows assumptions for a finance query.
- [ ] README explains local setup and Agent architecture.
- [ ] Resume story does not overclaim investment advice or private data.
