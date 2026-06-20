from __future__ import annotations

import json
import urllib.error
from pathlib import Path

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
from marketlens.agent.llm import DeepSeekLLMClient, FallbackLLMClient, MockLLMClient
from marketlens.agent.runtime import ToolResponse
from marketlens.agent.tools import EvidenceSearchTool
from marketlens.schemas import EvidenceRow, validate_evidence_row


ZH_LUCKIN = "\u745e\u5e78"
ZH_PROFIT_MARGIN = "\u5229\u6da6\u7387"
ZH_VALUATION = "\u4f30\u503c"
ZH_LATEST = "\u6700\u65b0"
ZH_SEARCH = "\u641c\u7d22"
ZH_ONLINE = "\u4e0a\u7f51"
ZH_SUPPLEMENT = "\u8865\u5145"
ZH_NEWS = "\u65b0\u95fb"
ZH_NEW_INFO = "\u65b0\u8d44\u6599"
ZH_SINGLE_STORE = "\u5355\u5e97"
ZH_PAYBACK = "\u56de\u672c"
ZH_EVIDENCE_INSUFFICIENT = "\u8bc1\u636e\u4e0d\u8db3"
ZH_SENSITIVITY = "\u654f\u611f\u6027\u5206\u6790"
ZH_NOT_INVESTMENT_ADVICE = "\u975e\u6295\u8d44\u5efa\u8bae"


def evidence_row(
    evidence_id: str,
    brand_id: str = "luckin",
    claim: str | None = None,
    review_status: str = "reviewed",
) -> EvidenceRow:
    claim_text = claim or f"Luckin {ZH_PROFIT_MARGIN} is affected by discounts."
    return EvidenceRow(
        evidence_id=evidence_id,
        brand_id=brand_id,
        lens="pricing",
        claim=claim_text,
        source_title="Market source",
        source_url=f"https://example.com/{evidence_id}",
        source_type="news",
        source_date="2026-06-20",
        excerpt=f"{claim_text} Supporting margin evidence.",
        confidence=0.86,
        review_status=review_status,
        notes="margin and pricing context",
    )


def valid_evidence_dict(evidence_id: str = "EV-VALID") -> dict:
    return evidence_row(evidence_id).to_dict()


class RecordingSearchTool:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def run(self, payload: dict) -> ToolResponse:
        self.payloads.append(payload)
        return ToolResponse(
            True,
            {"results": [{"title": "News", "url": "https://example.com/news"}]},
        )


class ArtifactSearchTool:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def run(self, payload: dict) -> ToolResponse:
        self.payloads.append(payload)
        return ToolResponse(
            True,
            {
                "results": [{"title": "Prepared search"}],
                "status": "prepared",
                "artifact_path": "work/search.json",
            },
        )


# --- LLM client tests (unchanged, also covered in test_agent_llm.py) -------


def test_fallback_llm_client_returns_fallback_provider_and_echoes_prompt():
    client = FallbackLLMClient()

    result = client.complete("You are concise.", f"{ZH_LUCKIN}{ZH_PROFIT_MARGIN}?")

    assert result.provider == "fallback"
    assert result.content == f"{ZH_LUCKIN}{ZH_PROFIT_MARGIN}?"


def test_deepseek_llm_client_without_api_key_falls_back_without_network(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("network should not be called without an API key")

    monkeypatch.setattr("urllib.request.urlopen", fail_if_called)

    result = DeepSeekLLMClient().complete("system", "user prompt")

    assert result.provider == "fallback"
    assert result.content == "user prompt"


def test_deepseek_llm_client_returns_fallback_on_network_error(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.example")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-test")

    def raise_network_error(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr("urllib.request.urlopen", raise_network_error)

    result = DeepSeekLLMClient().complete("system", "user prompt")

    assert result.provider == "fallback"
    assert result.content == "user prompt"


def test_deepseek_llm_client_rejects_unsafe_base_url_without_network(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "http://evil.example")

    called = False

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("unsafe base URL must not trigger a request")

    monkeypatch.setattr("urllib.request.urlopen", fail_if_called)

    result = DeepSeekLLMClient().complete("system", "user prompt")

    assert result.provider == "fallback"
    assert result.content == "user prompt"
    assert called is False


def test_deepseek_llm_client_success_posts_expected_request(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.example")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-test")
    captured: dict = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return b'{"choices": [{"message": {"content": "model answer"}}]}'

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = DeepSeekLLMClient().complete("system prompt", "user prompt")

    request = captured["request"]
    payload = json.loads(request.data.decode("utf-8"))
    assert result.provider == "deepseek"
    assert result.content == "model answer"
    assert request.full_url == "https://api.deepseek.example/chat/completions"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert payload == {
        "model": "deepseek-test",
        "messages": [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "user prompt"},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    assert "test-key" not in json.dumps(payload)


# --- TriageAgent (LLM-driven) ----------------------------------------------


def test_triage_calls_llm_and_returns_intent_and_rewritten_query():
    """TriageAgent calls LLM and parses the returned JSON to get intent +
    rewritten_query. This is the core LLM-driven path."""
    llm_response = json.dumps(
        {
            "intent": "finance_analysis_needed",
            "rewritten_query": f"{ZH_LUCKIN} {ZH_PROFIT_MARGIN} DCF \u4f30\u503c",
        }
    )
    client = MockLLMClient(response=llm_response)
    agent = TriageAgent(client)

    result = agent.run({"query": f"{ZH_LUCKIN} DCF {ZH_VALUATION} {ZH_PROFIT_MARGIN}?"})

    assert result["intent"] == "finance_analysis_needed"
    assert result["rewritten_query"] == f"{ZH_LUCKIN} {ZH_PROFIT_MARGIN} DCF \u4f30\u503c"
    assert result["query"] == f"{ZH_LUCKIN} DCF {ZH_VALUATION} {ZH_PROFIT_MARGIN}?"


def test_triage_falls_back_to_rules_when_llm_returns_invalid_json():
    """When LLM returns invalid JSON, TriageAgent falls back to rule-based
    routing so the run doesn't crash."""
    client = MockLLMClient(response="not valid json")
    agent = TriageAgent(client)

    result = agent.run(
        {"query": f"{ZH_LUCKIN} DCF {ZH_VALUATION} {ZH_PROFIT_MARGIN}?"}
    )

    assert result["intent"] == "finance_analysis_needed"
    assert result["rewritten_query"] == f"{ZH_LUCKIN} DCF {ZH_VALUATION} {ZH_PROFIT_MARGIN}?"


def test_triage_falls_back_to_rules_for_research_question():
    """Rule-based fallback routes research-keyword questions correctly."""
    client = MockLLMClient(response="broken")
    agent = TriageAgent(client)

    result = agent.run(
        {
            "query": (
                f"{ZH_ONLINE}{ZH_SEARCH} 2026 {ZH_LATEST}{ZH_NEWS}"
                f"{ZH_SUPPLEMENT}{ZH_NEW_INFO}"
            )
        }
    )

    assert result["intent"] == "new_research_needed"


# --- PlannerAgent (LLM-driven) ---------------------------------------------


def test_planner_calls_llm_and_returns_tasks():
    """PlannerAgent calls LLM and parses the returned JSON task list."""
    llm_response = json.dumps(
        {
            "tasks": [
                {
                    "title": "Search new sources",
                    "intent": "new_research_needed",
                    "query": "luckin 2026",
                },
                {
                    "title": "Review local evidence",
                    "intent": "local_evidence_qa",
                    "query": "luckin 2026",
                },
                {
                    "title": "Finance assumptions",
                    "intent": "finance_analysis_needed",
                    "query": "luckin DCF",
                },
                {
                    "title": "Draft final answer",
                    "intent": "finance_analysis_needed",
                    "query": "luckin 2026",
                },
            ]
        }
    )
    client = MockLLMClient(response=llm_response)
    agent = PlannerAgent(client)

    result = agent.run(
        {"query": f"{ZH_LUCKIN} DCF {ZH_VALUATION}?", "intent": "finance_analysis_needed"}
    )

    tasks = result["tasks"]
    assert 3 <= len(tasks) <= 5
    assert all(task["title"] and task["intent"] and task["query"] for task in tasks)
    assert any(task["title"] == "Finance assumptions" for task in tasks)


def test_planner_falls_back_to_rules_when_llm_returns_invalid_json():
    """When LLM returns invalid JSON, PlannerAgent falls back to rule-based
    task generation so the run produces a valid plan."""
    client = MockLLMClient(response="not json")
    agent = PlannerAgent(client)

    result = agent.run(
        {"query": f"{ZH_LUCKIN} DCF {ZH_VALUATION}?", "intent": "finance_analysis_needed"}
    )

    tasks = result["tasks"]
    assert 3 <= len(tasks) <= 5
    assert any(task["title"] == "Finance assumptions" for task in tasks)


def test_planner_fallback_includes_search_for_report_query():
    """Rule-based fallback generates search + finance + draft tasks for
    report-generation intent."""
    client = MockLLMClient(response="broken")
    agent = PlannerAgent(client)

    result = agent.run(
        {
            "query": "Build a 2026 latest search report with DCF valuation.",
            "intent": "report_generation_needed",
        }
    )

    tasks = result["tasks"]
    titles = [task["title"] for task in tasks]
    assert 3 <= len(tasks) <= 5
    assert "Search new sources" in titles
    assert "Finance assumptions" in titles
    assert any("Draft" in title or "Final" in title for title in titles)


# --- SearchAgent (unchanged) -----------------------------------------------


def test_search_agent_calls_search_tool_with_query_and_limit():
    search_tool = RecordingSearchTool()

    result = SearchAgent(search_tool).run({"query": f"luckin 2026 {ZH_NEWS}", "limit": 2})

    assert search_tool.payloads == [{"query": f"luckin 2026 {ZH_NEWS}", "limit": 2}]
    assert result["success"] is True
    assert result["results"] == [{"title": "News", "url": "https://example.com/news"}]
    assert result["error"] == ""


def test_search_agent_returns_error_for_invalid_limit_without_calling_tool():
    search_tool = RecordingSearchTool()

    result = SearchAgent(search_tool).run({"query": "luckin", "limit": "many"})

    assert result["success"] is False
    assert result["results"] == []
    assert "limit" in result["error"].lower()
    assert search_tool.payloads == []


def test_search_agent_preserves_success_response_metadata():
    search_tool = ArtifactSearchTool()

    result = SearchAgent(search_tool).run({"query": "luckin", "limit": 3})

    assert result["success"] is True
    assert result["results"] == [{"title": "Prepared search"}]
    assert result["status"] == "prepared"
    assert result["artifact_path"] == "work/search.json"
    assert result["data"]["status"] == "prepared"


# --- FinanceLensAgent (unchanged) ------------------------------------------


def test_finance_lens_agent_uses_finance_model_tool_and_returns_outputs():
    metrics_path = Path(__file__).resolve().parents[1] / "data" / "finance_metrics.csv"
    tool = FinanceModelTool(load_finance_metrics(metrics_path))

    result = FinanceLensAgent(tool).run({"brand_id": "luckin"})

    assert result["success"] is True
    assert result["assumptions"]
    assert result["scenarios"]
    assert {scenario["scenario_name"] for scenario in result["scenarios"]} >= {
        "Conservative",
        "Base",
        "Upside",
    }


def test_finance_lens_agent_returns_empty_outputs_and_error_on_failure():
    tool = FinanceModelTool([])

    result = FinanceLensAgent(tool).run({"brand_id": "luckin"})

    assert result["success"] is False
    assert result["assumptions"] == []
    assert result["scenarios"] == []
    assert "finance metrics" in result["error"].lower()


# --- WriterAgent (LLM-driven) ----------------------------------------------


def test_writer_calls_llm_and_generates_chinese_answer_with_evidence_ids():
    """WriterAgent calls LLM and returns its content, with evidence IDs
    guaranteed present via post-processing."""
    llm_response = (
        f"\u9488\u5bf9\u745e\u5e78\u5229\u6da6\u7387\u95ee\u9898\uff0c"
        f"\u57fa\u4e8e\u8bc1\u636e EV-900 \u7684\u5206\u6790\u3002\n\n"
        f"\u5c40\u9650\u6027\uff1a\u8bc1\u636e\u53ef\u80fd\u4e0d\u5b8c\u6574\u3002"
    )
    client = MockLLMClient(response=llm_response)
    search_tool = EvidenceSearchTool([evidence_row("EV-900")])
    search_result = search_tool.run(
        {"brand_id": "luckin", "query": ZH_PROFIT_MARGIN, "limit": 5}
    )

    agent = WriterAgent(client)
    result = agent.run(
        {
            "query": f"{ZH_LUCKIN}{ZH_PROFIT_MARGIN}?",
            "intent": "local_evidence_qa",
            "evidence": search_result.data["evidence"],
            "finance": {},
        }
    )

    assert result["supporting_evidence_ids"] == ["EV-900"]
    assert "EV-900" in result["answer"]
    assert "\u5c40\u9650\u6027" in result["answer"]


def test_writer_includes_finance_disclaimer_when_finance_assumptions_exist():
    """When finance assumptions are present, WriterAgent post-processing
    ensures the disclaimer and FinanceLens mention are in the answer."""
    llm_response = (
        f"\u57fa\u4e8e EV-900 \u7684\u5206\u6790\u3002\n\n\u5c40\u9650\u6027\uff1a\u8bc1\u636e\u6709\u9650\u3002"
    )
    client = MockLLMClient(response=llm_response)
    search_tool = EvidenceSearchTool([evidence_row("EV-900")])
    search_result = search_tool.run(
        {"brand_id": "luckin", "query": ZH_PROFIT_MARGIN, "limit": 5}
    )

    agent = WriterAgent(client)
    result = agent.run(
        {
            "query": f"{ZH_LUCKIN}{ZH_PROFIT_MARGIN}?",
            "intent": "finance_analysis_needed",
            "evidence": search_result.data["evidence"],
            "finance": {
                "assumptions": [
                    {"assumption_id": "fa_900", "metric_name": "operating_margin"}
                ],
                "scenarios": [{"scenario_id": "fs_900", "scenario_name": "Base"}],
            },
        }
    )

    assert "EV-900" in result["answer"]
    assert "FinanceLens" in result["answer"]
    assert ZH_SENSITIVITY in result["answer"]
    assert ZH_NOT_INVESTMENT_ADVICE in result["answer"]


def test_writer_returns_evidence_insufficient_answer_without_evidence():
    """Without evidence, WriterAgent returns the insufficient-evidence message
    without calling LLM (short-circuit)."""
    client = MockLLMClient(response="should not be used")
    agent = WriterAgent(client)

    result = agent.run(
        {
            "query": f"{ZH_LUCKIN}{ZH_PROFIT_MARGIN}?",
            "intent": "local_evidence_qa",
            "evidence": [],
            "finance": {},
        }
    )

    assert result["supporting_evidence_ids"] == []
    assert ZH_EVIDENCE_INSUFFICIENT in result["answer"]


def test_writer_ignores_unreviewed_invalid_or_empty_evidence():
    """WriterAgent's _valid_citable_evidence filter still applies: bad rows
    are excluded, and with no valid evidence the insufficient message is
    returned."""
    invalid_rows = [
        {**valid_evidence_dict("EV-NEEDS"), "review_status": "needs_review"},
        {**valid_evidence_dict("EV-REJECTED"), "review_status": "rejected"},
        {**valid_evidence_dict("EV-NO-ID"), "evidence_id": ""},
        {**valid_evidence_dict("EV-NO-TEXT"), "claim": "", "excerpt": ""},
        {**valid_evidence_dict("EV-NO-URL"), "source_url": ""},
        {**valid_evidence_dict("EV-BAD-URL"), "source_url": "ftp://example.com/source"},
        {**valid_evidence_dict("EV-PREFIX-ONLY"), "source_url": "https://"},
        {**valid_evidence_dict("EV-URL-SPACE"), "source_url": "https:// bad"},
    ]
    client = MockLLMClient(response="should not be used")
    agent = WriterAgent(client)

    result = agent.run(
        {
            "query": "Can we cite this?",
            "intent": "local_evidence_qa",
            "evidence": invalid_rows,
            "finance": {},
        }
    )

    assert result["supporting_evidence_ids"] == []
    assert ZH_EVIDENCE_INSUFFICIENT in result["answer"]


def test_writer_cites_only_valid_reviewed_evidence_from_mixed_rows():
    """From mixed valid/invalid rows, WriterAgent cites only the valid ones.
    LLM generates the answer, post-processing ensures all valid IDs appear."""
    llm_response = (
        f"\u57fa\u4e8e\u8bc1\u636e\u7684\u5206\u6790\u3002\n\n\u5c40\u9650\u6027\uff1a\u8bc1\u636e\u6709\u9650\u3002"
    )
    client = MockLLMClient(response=llm_response)
    valid_row = valid_evidence_dict("EV-VALID")
    excerpt_only = {**valid_evidence_dict("EV-EXCERPT"), "claim": ""}
    invalid_rows = [
        {**valid_evidence_dict("EV-NEEDS"), "review_status": "needs_review"},
        {**valid_evidence_dict("EV-BAD-URL"), "source_url": "not-a-url"},
    ]

    agent = WriterAgent(client)
    result = agent.run(
        {
            "query": "Can we cite mixed evidence?",
            "intent": "local_evidence_qa",
            "evidence": [*invalid_rows, valid_row, excerpt_only],
            "finance": {},
        }
    )

    assert result["supporting_evidence_ids"] == ["EV-VALID", "EV-EXCERPT"]
    assert "EV-VALID" in result["answer"]
    assert "EV-EXCERPT" in result["answer"]
    assert "EV-NEEDS" not in result["answer"]
    assert "EV-BAD-URL" not in result["answer"]


# --- EvidenceExtractorAgent (LLM-driven) -----------------------------------


def test_extractor_calls_llm_and_returns_structured_evidence():
    """ExtractorAgent calls LLM to generate claims from snippets, then
    merges with raw item metadata (URL, title) to build evidence rows."""
    llm_response = json.dumps(
        [
            {
                "index": 0,
                "claim": f"Luckin {ZH_PROFIT_MARGIN} improved.",
                "source_type": "news",
                "confidence": 0.8,
            },
            {
                "index": 1,
                "claim": f"{ZH_SINGLE_STORE}{ZH_PAYBACK} cycle changed.",
                "source_type": "news",
                "confidence": 0.7,
            },
        ]
    )
    client = MockLLMClient(response=llm_response)
    agent = EvidenceExtractorAgent(client)

    extraction = agent.run(
        {
            "brand_id": "luckin",
            "lens": "pricing",
            "source_results": {
                "web": [
                    {
                        "title": "Luckin margin update",
                        "url": "https://example.com/luckin-margin",
                        "snippet": f"Luckin {ZH_PROFIT_MARGIN} improved.",
                    }
                ],
                "data": [
                    {
                        "title": "Store economics",
                        "url": "https://example.com/store",
                        "content": f"{ZH_SINGLE_STORE}{ZH_PAYBACK} cycle changed.",
                    }
                ],
            },
        }
    )

    evidence = extraction["evidence"]
    assert len(evidence) == 2
    assert evidence[0]["evidence_id"] == "EV-CAND-001"
    assert evidence[0]["review_status"] == "needs_review"
    assert evidence[0]["brand_id"] == "luckin"
    assert "Luckin" in evidence[0]["claim"]
    assert evidence[0]["source_url"] == "https://example.com/luckin-margin"


def test_extractor_returns_only_structured_json_no_raw_snippet_in_claim():
    """Research isolation: when LLM provides a claim, it replaces the raw
    snippet in the claim field (snippet stays only in excerpt)."""
    llm_response = json.dumps(
        [
            {
                "index": 0,
                "claim": "LLM-generated concise claim.",
                "source_type": "news",
                "confidence": 0.85,
            }
        ]
    )
    client = MockLLMClient(response=llm_response)
    agent = EvidenceExtractorAgent(client)

    extraction = agent.run(
        {
            "brand_id": "luckin",
            "lens": "pricing",
            "source_results": {
                "web": [
                    {
                        "title": "Source",
                        "url": "https://example.com/source",
                        "snippet": "This is a long raw snippet that should not be the claim.",
                    }
                ]
            },
        }
    )

    candidate = extraction["evidence"][0]
    assert candidate["claim"] == "LLM-generated concise claim."
    assert candidate["excerpt"] == "This is a long raw snippet that should not be the claim."


def test_extractor_falls_back_to_snippet_as_claim_when_llm_returns_invalid_json():
    """When LLM returns invalid JSON, ExtractorAgent uses the raw snippet
    as the claim (graceful degradation)."""
    client = MockLLMClient(response="not json")
    agent = EvidenceExtractorAgent(client)

    extraction = agent.run(
        {
            "brand_id": "luckin",
            "lens": "pricing",
            "source_results": {
                "web": [
                    {
                        "title": "Luckin source",
                        "url": "https://example.com/luckin",
                        "snippet": "Fallback snippet becomes claim.",
                    }
                ]
            },
        }
    )

    candidate = extraction["evidence"][0]
    assert candidate["claim"] == "Fallback snippet becomes claim."
    assert candidate["excerpt"] == "Fallback snippet becomes claim."


def test_extractor_generates_schema_compatible_candidates_with_fallbacks():
    """ExtractorAgent preserves schema validation and fallback behavior for
    unsupported lens/brand_id."""
    llm_response = json.dumps(
        [
            {
                "index": 0,
                "claim": "Luckin margin source text.",
                "source_type": "news",
                "confidence": 0.7,
            }
        ]
    )
    client = MockLLMClient(response=llm_response)
    agent = EvidenceExtractorAgent(client)

    extraction = agent.run(
        {
            "brand_id": "luckin",
            "lens": "unsupported-lens",
            "source_results": {
                "web": [
                    {
                        "title": "Luckin source",
                        "url": "https://example.com/luckin",
                        "snippet": "Luckin margin source text.",
                        "source_type": "unsupported-source",
                    }
                ]
            },
        }
    )

    candidate = extraction["evidence"][0]
    row = EvidenceRow(**candidate)

    validate_evidence_row(row)
    assert candidate["lens"] == "risk"
    assert candidate["source_type"] == "news"
    assert candidate["source_date"] == "2026-06-20"
    assert candidate["review_status"] == "needs_review"


def test_extractor_emits_only_schema_valid_candidates_and_skips_bad_sources():
    """ExtractorAgent skips items without valid URL or text, even if LLM
    returns claims for them."""
    llm_response = json.dumps(
        [{"index": 0, "claim": "Valid claim.", "source_type": "news", "confidence": 0.8}]
    )
    client = MockLLMClient(response=llm_response)
    agent = EvidenceExtractorAgent(client)

    extraction = agent.run(
        {
            "brand_id": "unsupported-brand",
            "lens": "unsupported-lens",
            "source_results": {
                "web": [
                    {
                        "title": "Valid fallback source",
                        "url": "https://example.com/valid",
                        "excerpt": "Only excerpt is available.",
                        "source_type": "unsupported-source",
                    },
                    {
                        "title": "Missing URL",
                        "snippet": "This has text but no URL.",
                    },
                    {
                        "title": "Malformed URL",
                        "url": "https://",
                        "snippet": "This has text but a malformed URL.",
                    },
                    {
                        "title": "Missing text",
                        "url": "https://example.com/missing-text",
                    },
                ],
                "data": {
                    "status": "prepared",
                    "artifact_path": "work/search.json",
                },
            },
        }
    )

    evidence = extraction["evidence"]

    assert len(evidence) == 1
    candidate = evidence[0]
    validate_evidence_row(EvidenceRow(**candidate))
    assert candidate["brand_id"] == "luckin"
    assert candidate["lens"] == "risk"
    assert "fallback" in candidate["notes"].lower()


def test_extractor_does_not_treat_search_metadata_as_source():
    """ExtractorAgent does not extract evidence from search metadata fields
    (status, artifact_path) — only from web/results/data item lists."""
    search_result = SearchAgent(ArtifactSearchTool()).run({"query": "luckin", "limit": 3})
    client = MockLLMClient(response="[]")
    agent = EvidenceExtractorAgent(client)

    extraction = agent.run(
        {
            "brand_id": "luckin",
            "lens": "risk",
            "source_results": search_result,
        }
    )

    assert extraction["evidence"] == []


# --- VerifierAgent (unchanged) ---------------------------------------------


def test_verifier_approves_valid_evidence_and_rejects_bad_url():
    """VerifierAgent (rule-based, no LLM) checks URL validity and marks
    review_status accordingly."""
    valid_evidence = valid_evidence_dict("EV-001")
    verifier = VerifierAgent()

    approved = verifier.run({"evidence": valid_evidence})
    rejected = verifier.run(
        {"evidence": {**valid_evidence, "source_url": "https://"}}
    )

    assert approved["review_status"] == "reviewed"
    assert approved["verification_status"] == "approved"
    assert rejected["review_status"] == "rejected"
    assert rejected["verification_status"] == "rejected"
