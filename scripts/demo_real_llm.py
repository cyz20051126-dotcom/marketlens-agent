"""Run orchestrator with real DeepSeek LLM, print a full AgentRun for inspection.

Run with:
    C:\\Users\\chenyizhe\\.workbuddy\\binaries\\python\\envs\\marketlens\\Scripts\\python.exe scripts/demo_real_llm.py
"""
import json
import os
import sys
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from marketlens.agent.orchestrator import MarketLensAgentOrchestrator  # noqa: E402

root = Path(__file__).resolve().parent.parent
orchestrator = MarketLensAgentOrchestrator(
    evidence_path=root / "data" / "evidence.csv",
    finance_metrics_path=root / "data" / "finance_metrics.csv",
    session_dir=root / "work" / "agent_sessions",
    search_cache_dir=root / "work" / "websearch",
)

queries = [
    "\u745e\u5e78\u4ef7\u683c\u6218\u5bf9\u5229\u6da6\u7387\u6709\u4ec0\u4e48\u5f71\u54cd\uff1f",
    "\u5e2e\u6211\u7528 DCF \u5206\u6790\u745e\u5e78\u4ef7\u683c\u6218\u5bf9\u4f30\u503c\u7684\u5f71\u54cd",
]

for query in queries:
    print("=" * 70)
    print(f"QUERY: {query}")
    print("=" * 70)
    run = orchestrator.answer(query)
    print(f"run_id: {run.run_id}")
    print(f"intent: {run.intent}")
    print(f"agents_invoked: {run.agents_invoked}")
    print(f"supporting_evidence_ids: {run.supporting_evidence_ids}")
    print()
    print("ANSWER:")
    print(run.answer)
    print()
    print(f"trace events: {len(run.trace_events)}")
    for event in run.trace_events:
        print(f"  - [{event.agent_name}] {event.event_type}: {event.summary}")
    print()
    print(f"tool calls: {len(run.tool_calls)}")
    for tc in run.tool_calls:
        print(f"  - {tc.tool_name} -> {tc.status}")
    print()
    print()
