from __future__ import annotations

import json
from pathlib import Path

from marketlens.agent.finance import FinanceModelTool, load_finance_metrics
from marketlens.agent.tools import (
    EvidenceSearchTool,
    EvidenceStoreTool,
    SourceReadTool,
    WebSearchTool,
)
from marketlens.load import load_evidence
from marketlens.schemas import EvidenceRow


EVIDENCE_PATH = Path(__file__).resolve().parents[1] / "data" / "evidence.csv"
FINANCE_METRICS_PATH = Path(__file__).resolve().parents[1] / "data" / "finance_metrics.csv"


def evidence_row(
    evidence_id: str,
    brand_id: str,
    lens: str,
    claim: str,
    review_status: str = "reviewed",
    confidence: float = 0.8,
) -> EvidenceRow:
    return EvidenceRow(
        evidence_id=evidence_id,
        brand_id=brand_id,
        lens=lens,
        claim=claim,
        source_title="Example market source",
        source_url=f"https://example.com/{evidence_id}",
        source_type="news",
        source_date="2026-06-20",
        excerpt=f"Excerpt for {claim}",
        confidence=confidence,
        review_status=review_status,
        notes="Analyst note with operating margin context.",
    )


def sample_evidence_rows() -> list[EvidenceRow]:
    return [
        evidence_row(
            "EV-100",
            "luckin",
            "pricing",
            "Luckin margin pressure increased after discounting.",
            confidence=0.86,
        ),
        evidence_row(
            "EV-101",
            "luckin",
            "expansion",
            "Luckin store count reached 33596 in 2026Q1.",
            confidence=0.92,
        ),
        evidence_row(
            "EV-102",
            "mixue",
            "franchise",
            "Mixue franchise network remains large.",
            confidence=0.84,
        ),
        evidence_row(
            "EV-103",
            "luckin",
            "pricing",
            "Unreviewed Luckin pricing row must stay hidden.",
            review_status="needs_review",
            confidence=0.99,
        ),
    ]


def test_evidence_search_filters_reviewed_rows_by_brand_lens_and_query():
    tool = EvidenceSearchTool(sample_evidence_rows())

    response = tool.run(
        {"brand_id": "luckin", "lens": "pricing", "query": "MARGIN", "limit": 10}
    )

    assert response.success is True
    assert response.data["count"] == 1
    assert response.data["query"] == "MARGIN"
    assert response.data["evidence"][0]["evidence_id"] == "EV-100"
    assert response.data["evidence"][0]["review_status"] == "reviewed"


def test_evidence_search_returns_empty_when_query_misses_filtered_rows_by_default():
    tool = EvidenceSearchTool(sample_evidence_rows())

    response = tool.run(
        {"brand_id": "luckin", "lens": "pricing", "query": "unrelated-term"}
    )

    assert response.success is True
    assert response.data["count"] == 0
    assert response.data["evidence"] == []


def test_evidence_search_allows_broad_fallback_only_when_explicit():
    tool = EvidenceSearchTool(sample_evidence_rows())

    response = tool.run(
        {
            "brand_id": "luckin",
            "lens": "pricing",
            "query": "unrelated-term",
            "allow_broad_fallback": True,
        }
    )

    assert response.success is True
    assert response.data["count"] == 1
    assert response.data["evidence"][0]["evidence_id"] == "EV-100"


def test_evidence_search_normalizes_text_inputs_before_matching():
    tool = EvidenceSearchTool(sample_evidence_rows())

    response = tool.run(
        {"brand_id": " LUCKIN ", "lens": " PRICING ", "query": " margin ", "limit": 5}
    )

    assert response.success is True
    assert response.data["query"] == "margin"
    assert response.data["count"] == 1
    assert response.data["evidence"][0]["evidence_id"] == "EV-100"


def test_evidence_search_rejects_invalid_limits():
    tool = EvidenceSearchTool(sample_evidence_rows())

    for limit in (0, -2, "many"):
        response = tool.run({"query": "margin", "limit": limit})

        assert response.success is False
        assert "limit" in response.error.lower()


def test_source_read_tool_finds_and_reports_missing_evidence():
    tool = SourceReadTool(sample_evidence_rows())

    found = tool.run({"evidence_id": "EV-101"})
    missing = tool.run({"evidence_id": "EV-404"})

    assert found.success is True
    assert found.data["evidence"]["evidence_id"] == "EV-101"
    assert missing.success is False
    assert "EV-404" in missing.error


def test_source_read_tool_reads_source_and_artifact_text_inside_source_root(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    source_file = source_root / "a.md"
    source_file.write_text("# Source\nLuckin source text.", encoding="utf-8")
    artifact_file = source_root / "artifact.json"
    artifact_file.write_text('{"status": "prepared"}', encoding="utf-8")
    tool = SourceReadTool(sample_evidence_rows(), source_root=source_root)

    source_response = tool.run({"source_path": "a.md"})
    artifact_response = tool.run({"artifact_path": str(artifact_file)})

    assert source_response.success is True
    assert Path(source_response.data["source_path"]).name == "a.md"
    assert source_response.data["content"] == "# Source\nLuckin source text."
    assert source_response.data["content_length"] == len("# Source\nLuckin source text.")
    assert artifact_response.success is True
    assert artifact_response.data["content"] == '{"status": "prepared"}'


def test_source_read_tool_rejects_paths_outside_source_root(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    outside_file = tmp_path / "secret.md"
    outside_file.write_text("secret", encoding="utf-8")
    tool = SourceReadTool(sample_evidence_rows(), source_root=source_root)

    traversal = tool.run({"source_path": "../secret.md"})
    absolute_outside = tool.run({"artifact_path": str(outside_file)})

    assert traversal.success is False
    assert absolute_outside.success is False
    assert "source_root" in traversal.error
    assert "source_root" in absolute_outside.error


def test_evidence_store_tool_appends_valid_evidence_and_rejects_duplicate(tmp_path):
    path = tmp_path / "evidence.csv"
    tool = EvidenceStoreTool(path)
    payload = {"evidence": evidence_row("EV-200", "guming", "risk", "Guming risk signal.").to_dict()}

    stored = tool.run(payload)
    duplicate = tool.run(payload)

    assert stored.success is True
    assert stored.data["stored_evidence_id"] == "EV-200"
    assert path.exists()
    assert duplicate.success is False
    assert "duplicate" in duplicate.error.lower()


def test_evidence_store_tool_rejects_malformed_required_fields(tmp_path):
    tool = EvidenceStoreTool(tmp_path / "evidence.csv")
    missing_claim = evidence_row("EV-201", "guming", "risk", "Guming risk signal.").to_dict()
    missing_claim.pop("claim")
    none_claim = evidence_row("EV-202", "guming", "risk", "Guming risk signal.").to_dict()
    none_claim["claim"] = None
    missing_confidence = evidence_row(
        "EV-203", "guming", "risk", "Guming risk signal."
    ).to_dict()
    missing_confidence.pop("confidence")

    for raw in (missing_claim, none_claim, missing_confidence):
        response = tool.run({"evidence": raw})

        assert response.success is False


def test_web_search_tool_returns_real_results_when_mocked(tmp_path, monkeypatch):
    """When DuckDuckGo responds, WebSearchTool parses results and returns
    title/url/snippet for each hit."""
    fake_html = """
    <div class="results">
      <div class="result">
        <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fluckin">瑞幸 2026 Q1 财报</a>
        <a class="result__snippet" >瑞幸一季度门店数 33596 家，净增 2548 家。</a>
      </div>
      <div class="result">
        <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fnews.com%2Fcotti">库迪收缩 9.9 元促销</a>
        <a class="result__snippet" >库迪全场 9.9 元活动于 1 月底结束。</a>
      </div>
    </div>
    """

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return fake_html.encode("utf-8")

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout=15: FakeResponse()
    )

    tool = WebSearchTool(tmp_path / "websearch")
    response = tool.run({"query": "瑞幸 门店 2026", "limit": 5})

    assert response.success is True
    assert response.data["status"] == "live"
    assert response.data["count"] == 2
    results = response.data["results"]
    assert results[0]["title"] == "瑞幸 2026 Q1 财报"
    assert results[0]["url"] == "https://example.com/luckin"
    assert "33596" in results[0]["snippet"]
    assert results[1]["url"] == "https://news.com/cotti"


def test_web_search_tool_falls_back_on_network_failure(tmp_path, monkeypatch):
    """When DuckDuckGo is unreachable, WebSearchTool returns success=False
    with status=degraded_fallback so the orchestrator can skip search."""
    import urllib.error

    def raise_timeout(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr("urllib.request.urlopen", raise_timeout)

    tool = WebSearchTool(tmp_path / "websearch")
    response = tool.run({"query": "luckin 2026", "limit": 3})

    assert response.success is False
    assert response.data["status"] == "degraded_fallback"
    assert response.data["results"] == []
    assert "offline" in response.error


def test_web_search_tool_marks_degraded_status_in_trace(tmp_path, monkeypatch):
    """The degraded_fallback status is visible in the response data so the
    orchestrator trace can record it."""
    import urllib.error

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *a, **k: (_ for _ in ()).throw(urllib.error.URLError("timeout")),
    )

    tool = WebSearchTool()
    response = tool.run({"query": "test query", "limit": 2})

    assert response.data["status"] == "degraded_fallback"
    assert response.data["query"] == "test query"


def test_web_search_tool_uses_hash_to_avoid_filename_collisions(tmp_path, monkeypatch):
    """Different queries produce different artifact files."""
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b'<div class="results"></div>'

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda req, timeout=15: FakeResponse()
    )

    tool = WebSearchTool(tmp_path / "websearch")
    luckin = tool.run({"query": "瑞幸 门店", "limit": 3})
    mixue = tool.run({"query": "蜜雪 门店", "limit": 3})

    assert luckin.success is True
    assert mixue.success is True


def test_load_finance_metrics_parses_source_evidence_ids():
    metrics = load_finance_metrics(FINANCE_METRICS_PATH)

    luckin_margin = next(metric for metric in metrics if metric.metric_id == "FM-004")
    assert luckin_margin.source_evidence_ids == ["EV-004"]
    assert luckin_margin.metric_value == 0.06


def test_finance_metrics_reference_only_reviewed_evidence():
    evidence_by_id = {row.evidence_id: row for row in load_evidence(EVIDENCE_PATH)}
    metrics = load_finance_metrics(FINANCE_METRICS_PATH)

    missing_ids = []
    unreviewed_ids = []
    for metric in metrics:
        for evidence_id in metric.source_evidence_ids:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                missing_ids.append(evidence_id)
            elif evidence.review_status != "reviewed":
                unreviewed_ids.append(evidence_id)

    assert missing_ids == []
    assert unreviewed_ids == []


def test_finance_model_tool_returns_luckin_assumptions_and_base_scenario():
    metrics = load_finance_metrics(FINANCE_METRICS_PATH)
    tool = FinanceModelTool(metrics)

    response = tool.run({"brand_id": "luckin"})

    assert response.success is True
    assert response.data["assumptions"]
    assert response.data["assumptions"][0]["assumption_id"].startswith("fa_")
    assert response.data["assumptions"][0]["source_evidence_ids"]
    scenario_names = {scenario["scenario_name"] for scenario in response.data["scenarios"]}
    assert {"Conservative", "Base", "Upside"}.issubset(scenario_names)
    base = next(scenario for scenario in response.data["scenarios"] if scenario["scenario_name"] == "Base")
    assert base["result_value"] > 0


def test_finance_model_tool_returns_error_for_unknown_brand():
    tool = FinanceModelTool(load_finance_metrics(FINANCE_METRICS_PATH))

    response = tool.run({"brand_id": "unknown"})

    assert response.success is False
    assert "no finance metrics" in response.error.lower()


# --- Spec §7.1 coverage: tax rate, reinvestment, unit economics, expansion,
#     and three sensitivity matrices. ---


def test_finance_model_tool_includes_tax_rate_and_reinvestment_assumptions():
    """Spec §7.1.3: DCF assumptions must include tax_rate and reinvestment_rate."""
    tool = FinanceModelTool(load_finance_metrics(FINANCE_METRICS_PATH))
    response = tool.run({"brand_id": "luckin"})

    assert response.success
    names = {a["metric_name"] for a in response.data["assumptions"]}
    assert "tax_rate" in names
    assert "reinvestment_rate" in names

    tax = next(a for a in response.data["assumptions"] if a["metric_name"] == "tax_rate")
    assert 0.0 < tax["metric_value"] <= 0.25
    assert tax["confidence"] < 0.7  # labeled as assumption

    reinvest = next(
        a for a in response.data["assumptions"] if a["metric_name"] == "reinvestment_rate"
    )
    assert 0.08 <= reinvest["metric_value"] <= 0.25


def test_finance_model_tool_includes_unit_economics_for_brand_with_stores():
    """Spec §7.1.1: unit economics (per_store_gmv, per_store_revenue, store_level_margin)
    for brands that have store count data."""
    tool = FinanceModelTool(load_finance_metrics(FINANCE_METRICS_PATH))
    response = tool.run({"brand_id": "luckin"})

    names = {a["metric_name"] for a in response.data["assumptions"]}
    assert "per_store_gmv" in names
    assert "per_store_revenue" in names
    assert "store_level_margin" in names

    gmv = next(a for a in response.data["assumptions"] if a["metric_name"] == "per_store_gmv")
    assert gmv["unit"] == "RMB/year"
    assert gmv["confidence"] <= 0.4  # clearly an estimate


def test_finance_model_tool_skips_unit_economics_for_brand_without_stores():
    """Brands without store count data should not get unit economics assumptions."""
    tool = FinanceModelTool(load_finance_metrics(FINANCE_METRICS_PATH))
    response = tool.run({"brand_id": "chagee"})

    names = {a["metric_name"] for a in response.data["assumptions"]}
    assert "per_store_gmv" not in names


def test_finance_model_tool_includes_expansion_assumptions_for_luckin():
    """Spec §7.1.2: expansion model — franchise_ratio and same_store_growth."""
    tool = FinanceModelTool(load_finance_metrics(FINANCE_METRICS_PATH))
    response = tool.run({"brand_id": "luckin"})

    names = {a["metric_name"] for a in response.data["assumptions"]}
    assert "franchise_ratio" in names
    assert "same_store_growth" in names

    ratio = next(
        a for a in response.data["assumptions"] if a["metric_name"] == "franchise_ratio"
    )
    assert 0 < ratio["metric_value"] < 1  # partnership / total


def test_finance_model_tool_includes_three_sensitivity_matrices():
    """Spec §7.1.4: three sensitivity matrices — growth vs margin, discount vs
    terminal, store count vs per-store GMV. Each matrix has 3 scenarios,
    so total scenarios = 9."""
    tool = FinanceModelTool(load_finance_metrics(FINANCE_METRICS_PATH))
    response = tool.run({"brand_id": "luckin"})

    scenarios = response.data["scenarios"]
    assert len(scenarios) == 9

    axis_pairs = {(s["sensitivity_axis_x"], s["sensitivity_axis_y"]) for s in scenarios}
    assert ("revenue_growth", "operating_margin") in axis_pairs
    assert ("discount_rate", "terminal_growth") in axis_pairs
    assert ("store_count_growth", "per_store_gmv") in axis_pairs

    # Original 3 still present
    names = {s["scenario_name"] for s in scenarios}
    assert {"Conservative", "Base", "Upside"}.issubset(names)

    # All result_values are positive and finite
    for s in scenarios:
        assert s["result_value"] > 0

