import pytest

from marketlens.agent.models import AgentRun
from marketlens.agent.runtime import TodoBoard, ToolRegistry, ToolResponse
from marketlens.agent.session import SessionStore
from marketlens.agent.trace import TraceLogger


class EchoTool:
    name = "echo"
    description = "Echo the provided text."

    def run(self, payload):
        return ToolResponse(success=True, data={"echo": payload["text"]})


class FailingTool:
    name = "fail"
    description = "Raise a predictable error."

    def run(self, payload):
        raise RuntimeError("tool exploded")


class NamedTool:
    description = "Named test tool."

    def __init__(self, name):
        self.name = name

    def run(self, payload):
        return ToolResponse(success=True, data={})


def build_agent_run(run_id="run_001", answer="Saved answer."):
    return AgentRun(
        run_id=run_id,
        session_id="session_001",
        user_query="What changed?",
        intent="local_evidence_qa",
        started_at="2026-06-20T10:00:00+08:00",
        completed_at="2026-06-20T10:00:05+08:00",
        status="completed",
        agents_invoked=["TriageAgent"],
        tool_calls=[],
        trace_events=[],
        todo_items=[],
        answer=answer,
        supporting_evidence_ids=[],
        finance_assumptions=[],
        finance_scenarios=[],
        error_message="",
    )


def test_tool_registry_registers_and_calls_echo_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())

    response = registry.call("echo", {"text": "hello"})

    assert response == ToolResponse(success=True, data={"echo": "hello"})


def test_tool_registry_missing_tool_returns_error_response():
    registry = ToolRegistry()

    response = registry.call("missing", {"text": "hello"})

    assert response.success is False
    assert response.data == {}
    assert "not registered" in response.error


def test_tool_registry_wraps_tool_exceptions():
    registry = ToolRegistry()
    registry.register(FailingTool())

    response = registry.call("fail", {})

    assert response == ToolResponse(False, {}, "tool exploded")


def test_tool_registry_names_are_sorted():
    registry = ToolRegistry()
    registry.register(NamedTool("zeta"))
    registry.register(NamedTool("alpha"))

    assert registry.names() == ["alpha", "zeta"]


def test_trace_logger_records_events_with_stable_ids():
    logger = TraceLogger(run_id="run_001")

    logger.record(
        agent_name="TriageAgent",
        event_type="intent",
        summary="Classified the request.",
        input_payload="What is Luckin doing?",
        output_payload="local_evidence_qa",
    )

    event = logger.events()[0]
    assert event.event_id == "trace_001"
    assert event.agent_name == "TriageAgent"


def test_trace_logger_truncates_input_and_output_previews():
    logger = TraceLogger(run_id="run_001")
    long_text = "x" * 241

    event = logger.record(
        agent_name="TriageAgent",
        event_type="debug",
        summary="Captured long payloads.",
        input_payload=long_text,
        output_payload=long_text,
    )

    assert len(event.input_preview) == 240
    assert len(event.output_preview) == 240


def test_todo_board_adds_and_completes_todos_with_sources():
    board = TodoBoard(run_id="run_001")
    todo = board.add(
        title="Review sources",
        intent="Find evidence.",
        query="luckin pricing margin",
        assigned_agent="EvidenceAgent",
    )

    completed = board.complete(
        todo.todo_id,
        result_summary="Found pricing evidence.",
        source_urls=["https://example.com/source"],
    )

    assert completed.status == "completed"
    assert completed.supporting_source_urls == ["https://example.com/source"]
    assert board.items()[0] == completed


def test_todo_board_complete_without_sources_preserves_existing_sources():
    board = TodoBoard(run_id="run_001")
    todo = board.add(
        title="Review sources",
        intent="Find evidence.",
        query="luckin pricing margin",
        assigned_agent="EvidenceAgent",
        supporting_source_urls=["https://example.com/source"],
    )

    completed = board.complete(todo.todo_id, result_summary="Done.")

    assert completed.supporting_source_urls == ["https://example.com/source"]


def test_todo_board_complete_with_empty_sources_clears_existing_sources():
    board = TodoBoard(run_id="run_001")
    todo = board.add(
        title="Review sources",
        intent="Find evidence.",
        query="luckin pricing margin",
        assigned_agent="EvidenceAgent",
        supporting_source_urls=["https://example.com/source"],
    )

    completed = board.complete(todo.todo_id, source_urls=[])

    assert completed.supporting_source_urls == []


def test_session_store_saves_and_loads_agent_run(tmp_path):
    store = SessionStore(tmp_path / "sessions")
    run = build_agent_run(answer="Saved answer.")

    store.save_run(run)

    loaded = store.load_run("run_001")
    assert loaded["answer"] == "Saved answer."
    assert (tmp_path / "sessions" / "run_001.json").exists()


def test_session_store_rejects_unsafe_run_id_on_save(tmp_path):
    store = SessionStore(tmp_path / "sessions")
    run = build_agent_run(run_id="../outside")

    with pytest.raises(ValueError, match="Invalid run_id"):
        store.save_run(run)


def test_session_store_rejects_unsafe_run_id_on_load(tmp_path):
    store = SessionStore(tmp_path / "sessions")

    with pytest.raises(ValueError, match="Invalid run_id"):
        store.load_run("..\\outside")
