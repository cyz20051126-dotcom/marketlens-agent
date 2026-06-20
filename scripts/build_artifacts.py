"""Build MarketLens AI artifacts."""

from __future__ import annotations

import shutil
from pathlib import Path

from marketlens.agent.orchestrator import MarketLensAgentOrchestrator
from marketlens.export import evidence_to_json, write_html_brief, write_json, write_markdown_brief
from marketlens.load import load_evidence
from marketlens.synthesize import build_brand_profiles, build_brief_sections


def copy_artifacts(processed_dir: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "brands.json",
        "evidence.json",
        "brief_sections.json",
        "brief.md",
        "brief.html",
        "agent_demo.json",
    ):
        shutil.copy2(processed_dir / name, target_dir / name)


def build_agent_demo(
    root: Path,
    session_dir: Path | None = None,
    search_cache_dir: Path | None = None,
) -> dict:
    orchestrator = MarketLensAgentOrchestrator(
        evidence_path=root / "data" / "evidence.csv",
        finance_metrics_path=root / "data" / "finance_metrics.csv",
        session_dir=session_dir or root / "work" / "agent_sessions",
        search_cache_dir=search_cache_dir or root / ".search_cache",
    )
    query = "\u5e2e\u6211\u7528 DCF \u5206\u6790\u745e\u5e78\u4ef7\u683c\u6218\u5bf9\u4f30\u503c\u7684\u5f71\u54cd"
    return orchestrator.answer(query).to_dict()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    processed_dir = data_dir / "processed"
    evidence_path = data_dir / "evidence.csv"

    evidence_rows = load_evidence(evidence_path)
    profiles = build_brand_profiles(evidence_rows)
    sections = build_brief_sections(evidence_rows, profiles)

    write_json(processed_dir / "brands.json", [profile.to_dict() for profile in profiles])
    write_json(processed_dir / "evidence.json", evidence_to_json(evidence_rows))
    write_json(processed_dir / "brief_sections.json", [section.to_dict() for section in sections])
    write_markdown_brief(processed_dir / "brief.md", sections)
    write_html_brief(processed_dir / "brief.html", sections)
    write_json(processed_dir / "agent_demo.json", build_agent_demo(root))

    copy_artifacts(processed_dir, root / "web" / "src" / "data")
    copy_artifacts(processed_dir, root / "web" / "public" / "data")


if __name__ == "__main__":
    main()
