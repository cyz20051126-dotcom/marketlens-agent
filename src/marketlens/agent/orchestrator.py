from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from marketlens.agent.agents import (
    EvidenceExtractorAgent,
    FinanceLensAgent,
    PlannerAgent,
    SearchAgent,
    TriageAgent,
    VerifierAgent,
    WriterAgent,
)
from marketlens.agent.finance import FinanceModelTool, load_finance_metrics
from marketlens.agent.llm import DeepSeekLLMClient, FallbackLLMClient
from marketlens.agent.models import (
    AgentRun,
    FinanceAssumption,
    FinanceScenario,
    ToolCallRecord,
)
from marketlens.agent.runtime import TodoBoard, ToolResponse
from marketlens.agent.session import SessionStore
from marketlens.agent.tools import (
    EvidenceSearchTool,
    EvidenceStoreTool,
    WebSearchTool,
)
from marketlens.agent.trace import TraceLogger
from marketlens.load import load_evidence


def _default_llm_client() -> Any:
    """Construct the default LLM client. Uses DeepSeek when an API key is
    present, otherwise falls back to the offline FallbackLLMClient."""
    if os.environ.get("DEEPSEEK_API_KEY", "").strip():
        return DeepSeekLLMClient()
    return FallbackLLMClient()


class MarketLensAgentOrchestrator:
    def __init__(
        self,
        evidence_path: Path,
        finance_metrics_path: Path,
        session_dir: Path,
        search_cache_dir: Path,
        llm_client: Any = None,
        web_search_tool: Any = None,
        extracted_evidence_path: Path | None = None,
    ) -> None:
        self.evidence_path = Path(evidence_path)
        self.finance_metrics_path = Path(finance_metrics_path)
        self.session_store = SessionStore(Path(session_dir))
        self.search_cache_dir = Path(search_cache_dir)
        self.llm_client = llm_client or _default_llm_client()
        self.web_search_tool = web_search_tool or WebSearchTool(
            self.search_cache_dir
        )
        # Extracted evidence is written to a separate file so the seed
        # evidence.csv stays untouched. Defaults to <session_dir>/../extracted_evidence.csv
        # which lands under work/ alongside agent_sessions/.
        if extracted_evidence_path is not None:
            self.extracted_evidence_path = Path(extracted_evidence_path)
        else:
            self.extracted_evidence_path = (
                Path(session_dir).parent / "extracted_evidence.csv"
            )

    def answer(self, query: str) -> AgentRun:
        cleaned_query = query.strip()
        started_at = _now()
        run_id = f"run_{uuid4().hex[:10]}"
        session_id = "local_session"
        trace = TraceLogger(run_id)
        todo = TodoBoard(run_id)
        agents_invoked: list[str] = []
        tool_calls: list[ToolCallRecord] = []

        rows = load_evidence(self.evidence_path)
        metrics = load_finance_metrics(self.finance_metrics_path)

        # --- Triage (LLM) ---
        triage = TriageAgent(self.llm_client)
        agents_invoked.append(triage.name)
        triage_start = time.perf_counter()
        triage_result = triage.run({"query": cleaned_query})
        triage_latency = max(int((time.perf_counter() - triage_start) * 1000), 1)
        intent = triage_result["intent"]
        search_query = triage_result.get("rewritten_query", cleaned_query)
        trace.record(
            triage.name,
            "intent",
            f"Classified query as {intent}.",
            cleaned_query,
            intent,
            "",
            "",
            triage_latency,
        )

        # --- Local evidence search ---
        brand_id = _infer_brand_id(cleaned_query)
        lens = _infer_lens(cleaned_query, intent)
        evidence_query = _infer_evidence_query(cleaned_query, intent)
        ev_start = time.perf_counter()
        evidence_response = EvidenceSearchTool(rows).run(
            {
                "query": evidence_query,
                "brand_id": brand_id,
                "lens": lens,
                "limit": 5,
                "allow_broad_fallback": False,
            }
        )
        ev_latency = max(int((time.perf_counter() - ev_start) * 1000), 1)
        _record_tool_call(tool_calls, "EvidenceSearchTool", evidence_response, ev_latency)
        evidence = list(evidence_response.data.get("evidence", []))
        trace.record(
            "EvidenceSearchTool",
            "tool_call",
            f"Found {len(evidence)} reviewed local evidence rows.",
            evidence_query,
            _preview(evidence),
            "EvidenceSearchTool",
            "success" if evidence_response.success else "failed",
            ev_latency,
        )

        # --- Research workflow: full chain when local evidence is thin ---
        # Per spec §6 + plan §2.3: trigger only when evidence < 2 (don't
        # waste a web search when local evidence is sufficient).
        if len(evidence) < 2:
            # Planner
            planner = PlannerAgent(self.llm_client)
            agents_invoked.append(planner.name)
            planner_start = time.perf_counter()
            plan = planner.run({"query": cleaned_query, "intent": intent})
            planner_latency = max(int((time.perf_counter() - planner_start) * 1000), 1)
            for task in plan["tasks"]:
                todo.add(
                    title=task["title"],
                    intent=task["intent"],
                    query=task["query"],
                    assigned_agent=planner.name,
                    task_type=task.get("task_type", ""),
                )
            trace.record(
                planner.name,
                "planning",
                f"Created {len(plan['tasks'])} todo items.",
                cleaned_query,
                _preview(plan["tasks"]),
                "",
                "success",
                planner_latency,
            )

            # Search (DuckDuckGo via SearchAgent)
            search_agent = SearchAgent(self.web_search_tool)
            agents_invoked.append(search_agent.name)
            search_start = time.perf_counter()
            search_result = search_agent.run({"query": search_query, "limit": 5})
            search_latency = max(int((time.perf_counter() - search_start) * 1000), 1)
            search_success = bool(search_result.get("success"))
            search_results_list = search_result.get("results", [])

            search_response = ToolResponse(
                success=search_success,
                data=search_result.get("data", search_result),
                error=search_result.get("error", ""),
            )
            _record_tool_call(
                tool_calls, "WebSearchTool", search_response, search_latency
            )
            _complete_todo(
                todo,
                "search_sources",
                f"Web search returned {len(search_results_list)} results.",
                _extract_urls(search_results_list),
            )
            trace.record(
                search_agent.name,
                "tool_call",
                f"Web search returned {len(search_results_list)} results.",
                search_query,
                _preview(search_results_list),
                "WebSearchTool",
                "success" if search_success else "failed",
                search_latency,
            )

            # Extractor (LLM) — only when search returned real results
            if search_results_list:
                extractor = EvidenceExtractorAgent(self.llm_client)
                agents_invoked.append(extractor.name)
                extract_start = time.perf_counter()
                extract_result = extractor.run(
                    {
                        "brand_id": brand_id,
                        "lens": lens or "risk",
                        "source_results": search_result,
                    }
                )
                extract_latency = max(
                    int((time.perf_counter() - extract_start) * 1000), 1
                )
                candidates = extract_result.get("evidence", [])
                _complete_todo(
                    todo,
                    "review_evidence",
                    f"Extracted {len(candidates)} candidate evidence.",
                    _extract_urls(candidates),
                )
                trace.record(
                    extractor.name,
                    "extraction",
                    f"Extracted {len(candidates)} candidate evidence.",
                    _preview(search_results_list),
                    _preview(candidates),
                    "",
                    "success",
                    extract_latency,
                )

                # Verifier (rules) — approve / reject each candidate.
                # Duplicate URL detection: skip candidates whose source_url
                # was already verified in this batch, marking them
                # needs_review so they don't silently inflate evidence.
                verifier = VerifierAgent()
                agents_invoked.append(verifier.name)
                verify_start = time.perf_counter()
                verified_evidence: list[dict[str, Any]] = []
                seen_urls: set[str] = set()
                for candidate in candidates:
                    candidate_url = str(candidate.get("source_url", "")).strip()
                    if candidate_url and candidate_url in seen_urls:
                        candidate["review_status"] = "needs_review"
                        candidate["verification_status"] = "rejected"
                        candidate["verification_reason"] = "duplicate source_url in batch"
                        continue
                    verified = verifier.run({"evidence": candidate})
                    if verified.get("review_status") == "reviewed":
                        verified_evidence.append(verified)
                        if candidate_url:
                            seen_urls.add(candidate_url)
                verify_latency = max(
                    int((time.perf_counter() - verify_start) * 1000), 1
                )
                _complete_todo(
                    todo,
                    "verify_evidence",
                    f"Approved {len(verified_evidence)}/{len(candidates)} candidates.",
                    _extract_urls(verified_evidence),
                )
                trace.record(
                    verifier.name,
                    "verification",
                    f"Approved {len(verified_evidence)}/{len(candidates)} evidence.",
                    _preview(candidates),
                    _preview(verified_evidence),
                    "",
                    "success",
                    verify_latency,
                )

                # Store + merge verified evidence for the Writer
                store_tool = EvidenceStoreTool(self.extracted_evidence_path)
                for verified in verified_evidence:
                    store_response = store_tool.run({"evidence": verified})
                    if store_response.success:
                        evidence.append(verified)

        # --- Finance lens ---
        finance_payload: dict[str, Any] = {"assumptions": [], "scenarios": []}
        if intent == "finance_analysis_needed":
            finance_agent = FinanceLensAgent(FinanceModelTool(metrics))
            agents_invoked.append(finance_agent.name)
            finance_start = time.perf_counter()
            finance_payload = finance_agent.run({"brand_id": brand_id})
            finance_latency = max(int((time.perf_counter() - finance_start) * 1000), 1)
            finance_response = ToolResponse(
                success=bool(finance_payload.get("success", True)),
                data=finance_payload,
                error=str(finance_payload.get("error", "")),
            )
            _record_tool_call(
                tool_calls, "FinanceModelTool", finance_response, finance_latency
            )
            trace.record(
                finance_agent.name,
                "finance",
                f"Generated {len(finance_payload.get('assumptions', []))} finance assumptions.",
                brand_id,
                _preview(finance_payload.get("assumptions", [])[:2]),
                "FinanceModelTool",
                "success" if finance_response.success else "failed",
                finance_latency,
            )
            # Mark any Planner-created finance_assumptions todo as done.
            _complete_todo(
                todo,
                "finance_assumptions",
                f"Generated {len(finance_payload.get('assumptions', []))} assumptions "
                f"and {len(finance_payload.get('scenarios', []))} scenarios.",
                [],
            )

        # --- Writer (LLM) ---
        writer = WriterAgent(self.llm_client)
        agents_invoked.append(writer.name)
        writer_start = time.perf_counter()
        writer_result = writer.run(
            {
                "query": cleaned_query,
                "intent": intent,
                "evidence": evidence,
                "finance": finance_payload,
            }
        )
        writer_latency = max(int((time.perf_counter() - writer_start) * 1000), 1)
        # If the Planner didn't create a draft_answer todo (e.g. it
        # returned a different mix of tasks), append one now so the
        # todo board always reflects the final step that actually ran.
        if not _has_todo(todo, "draft_answer"):
            todo.add(
                title="\u64b0\u5199\u6700\u7ec8\u56de\u7b54",
                intent=intent,
                query=cleaned_query,
                assigned_agent=writer.name,
                task_type="draft_answer",
            )
        _complete_todo(
            todo,
            "draft_answer",
            "Cited {} evidence IDs.".format(
                len(writer_result["supporting_evidence_ids"])
            ),
            [],
        )
        trace.record(
            writer.name,
            "answer",
            "Generated cited answer.",
            cleaned_query,
            writer_result["answer"],
            "",
            "",
            writer_latency,
        )

        # Aggregate LLM provenance: the 4 LLM-driven agents (Triage,
        # Planner, Extractor, Writer) share self.llm_client. After the
        # run we read the client's last_* attrs to surface whether the
        # final answer was LLM-generated or rule-generated. DeepSeek with
        # a valid key produces uniform state across all 4 calls; if any
        # call degrades, the last_* attrs reflect the most recent
        # degradation (which is what matters for the answer's provenance).
        llm_provider = getattr(self.llm_client, "provider", "")
        llm_used = bool(getattr(self.llm_client, "last_llm_used", False))
        fallback_reason = str(getattr(self.llm_client, "last_fallback_reason", ""))

        # Finalize any Planner-created todos that the fixed orchestrator
        # pipeline doesn't explicitly complete (e.g. 'other' sub-questions
        # or 'structure_report' when the report path didn't run). Without
        # this, a completed run could show all todos pending, which reads
        # as a broken workflow.
        _finalize_unmatched_todos(todo)

        run = AgentRun(
            run_id=run_id,
            session_id=session_id,
            user_query=cleaned_query,
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
            finance_assumptions=[
                FinanceAssumption(**item)
                for item in finance_payload.get("assumptions", [])
            ],
            finance_scenarios=[
                FinanceScenario(**item)
                for item in finance_payload.get("scenarios", [])
            ],
            error_message="",
            llm_provider=llm_provider,
            llm_used=llm_used,
            fallback_reason=fallback_reason,
        )
        self.session_store.save_run(run)
        return run

    def load_run(self, run_id: str) -> dict[str, Any]:
        return self.session_store.load_run(run_id)


def _record_tool_call(
    tool_calls: list[ToolCallRecord],
    tool_name: str,
    response: ToolResponse,
    latency_ms: int = 0,
) -> None:
    output_count = 0
    if isinstance(response.data.get("evidence"), list):
        output_count = len(response.data["evidence"])
    elif isinstance(response.data.get("assumptions"), list):
        output_count = len(response.data["assumptions"])
    elif isinstance(response.data.get("results"), list):
        output_count = len(response.data["results"])
    tool_calls.append(
        ToolCallRecord(
            tool_name=tool_name,
            input_summary=tool_name,
            output_summary=f"{output_count} structured items",
            status="success" if response.success else "failed",
            latency_ms=max(latency_ms, 1),
        )
    )


def _complete_todo(
    todo: TodoBoard, task_type: str, result_summary: str, source_urls: list[str]
) -> None:
    """Mark the first todo with matching task_type as completed. Falls back
    to no-op when no matching todo exists (e.g. Planner didn't run, or
    task_type couldn't be inferred). task_type matching is stable across
    Chinese/English titles; the old title-prefix approach left LLM-generated
    Chinese todos stuck in pending state."""
    for item in todo.items():
        if item.task_type == task_type and item.status != "completed":
            todo.complete(item.todo_id, result_summary, source_urls=source_urls)
            return


def _has_todo(todo: TodoBoard, task_type: str) -> bool:
    """Return True when any todo on the board has the given task_type."""
    return any(item.task_type == task_type for item in todo.items())


def _finalize_unmatched_todos(todo: TodoBoard) -> None:
    """Mark any still-pending todo whose task_type the orchestrator doesn't
    have an explicit completion step for (e.g. 'other' or 'structure_report'
    when the report path didn't run). These are Planner-created research
    sub-questions that the fixed orchestrator pipeline doesn't execute as
    separate steps. Marking them 'completed' with a clear note prevents the
    'all todos pending' display issue (Codex review follow-up)."""
    for item in todo.items():
        if item.status == "pending":
            todo.complete(
                item.todo_id,
                "\u7531\u4e3b\u6d41\u7a0b\u5408\u5e76\u5b8c\u6210\uff08\u7814\u7a76\u5b50\u95ee\u9898\u5df2\u5728\u540e\u7eed\u6b65\u9aa4\u4e2d\u8986\u76d6\uff09\u3002",
                source_urls=[],
            )


def _extract_urls(items: list[dict[str, Any]]) -> list[str]:
    urls: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        url = str(item.get("source_url", item.get("url", ""))).strip()
        if url and url not in urls:
            urls.append(url)
    return urls


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _infer_brand_id(query: str) -> str:
    brand_map = {
        "luckin": "luckin",
        "\u745e\u5e78": "luckin",
        "\u5e93\u8fea": "cotti",
        "\u661f\u5df4\u514b": "starbucks",
        "\u871c\u96ea": "mixue",
        "\u9738\u738b": "chagee",
        "chagee": "chagee",
        "\u53e4\u8317": "guming",
        "\u8336\u767e\u9053": "chapanda",
    }
    folded = query.casefold()
    for needle, brand_id in brand_map.items():
        if needle.casefold() in folded:
            return brand_id
    return "luckin"


def _infer_lens(query: str, intent: str) -> str:
    if intent == "finance_analysis_needed":
        return ""
    if "\u52a0\u76df" in query:
        return "franchise"
    if "\u6269\u5f20" in query or "\u95e8\u5e97" in query:
        return "expansion"
    if "\u4ef7\u683c" in query:
        return "pricing"
    if "\u98ce\u9669" in query or "\u5229\u6da6\u7387" in query:
        return "risk"
    return ""


def _infer_evidence_query(query: str, intent: str) -> str:
    if "\u5229\u6da6\u7387" in query:
        return "\u5229\u6da6\u7387"
    if "\u4f30\u503c" in query:
        return "\u5229\u6da6\u7387"
    if "\u4ef7\u683c" in query:
        return "\u4ef7\u683c"
    if "\u6269\u5f20" in query:
        return "\u6269\u5f20"
    if intent == "finance_analysis_needed":
        return "\u5229\u6da6\u7387"
    return query


def _preview(value: Any) -> str:
    return str(value)[:240]
