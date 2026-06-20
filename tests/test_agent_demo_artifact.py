from pathlib import Path

from scripts.build_artifacts import build_agent_demo


ROOT = Path(__file__).resolve().parents[1]


def test_build_agent_demo_returns_serialized_agent_run(tmp_path):
    payload = build_agent_demo(
        ROOT,
        session_dir=tmp_path / "sessions",
        firecrawl_output_dir=tmp_path / "firecrawl",
    )

    assert payload["run_id"].startswith("run_")
    assert payload["answer"]
    assert payload["supporting_evidence_ids"]
    assert payload["trace_events"]
    assert payload["tool_calls"]
