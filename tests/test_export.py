import json

from marketlens.export import write_html_brief, write_json, write_markdown_brief
from marketlens.schemas import BriefSection


def test_write_json_creates_parent_directory(tmp_path):
    output_path = tmp_path / "nested" / "payload.json"

    write_json(output_path, {"brand": "luckin"})

    assert json.loads(output_path.read_text(encoding="utf-8")) == {"brand": "luckin"}


def test_write_markdown_brief_includes_confidence_and_evidence_ids(tmp_path):
    output_path = tmp_path / "brief.md"
    sections = [
        BriefSection(
            section_id="pricing",
            title="Pricing Pressure",
            summary="Promotional coffee pricing remains a competitive lever.",
            supporting_evidence_ids=["ev_001", "ev_002"],
            confidence=0.74,
        )
    ]

    write_markdown_brief(output_path, sections)

    markdown = output_path.read_text(encoding="utf-8")
    assert "# MarketLens AI 研究简报" in markdown
    assert "置信度: 0.74" in markdown
    assert "ev_001" in markdown
    assert "ev_002" in markdown


def test_write_html_brief_declares_utf8(tmp_path):
    output_path = tmp_path / "brief.html"
    sections = [
        BriefSection(
            section_id="overview",
            title="市场概览",
            summary="中文简报应该能在浏览器中正常显示。",
            supporting_evidence_ids=["EV-001"],
            confidence=0.88,
        )
    ]

    write_html_brief(output_path, sections)

    html = output_path.read_text(encoding="utf-8")
    assert '<meta charset="utf-8" />' in html
    assert "MarketLens AI 研究简报" in html
    assert "中文简报应该能在浏览器中正常显示。" in html
