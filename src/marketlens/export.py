from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

from marketlens.schemas import BriefSection, EvidenceRow


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_markdown_brief(path: Path, sections: list[BriefSection]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# MarketLens AI 研究简报", ""]

    for section in sections:
        evidence_ids = ", ".join(section.supporting_evidence_ids) or "None"
        lines.extend(
            [
                f"## {section.title}",
                "",
                section.summary,
                "",
                f"置信度: {section.confidence:.2f}",
                f"支持证据 ID: {evidence_ids}",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8-sig")


def write_html_brief(path: Path, sections: list[BriefSection]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    section_html = []

    for section in sections:
        evidence_ids = ", ".join(section.supporting_evidence_ids) or "无"
        section_html.append(
            f"""
      <section class="brief-section">
        <div class="brief-section__meta">置信度 {section.confidence:.2f}</div>
        <h2>{escape(section.title)}</h2>
        <p>{escape(section.summary)}</p>
        <div class="evidence-ids">支持证据 ID：{escape(evidence_ids)}</div>
      </section>"""
        )

    html = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>MarketLens AI 研究简报</title>
    <style>
      :root {{
        color: #223029;
        background: #dfe7df;
        font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif;
      }}
      body {{
        margin: 0;
        padding: 32px;
        background:
          linear-gradient(90deg, rgba(24, 49, 40, 0.04) 1px, transparent 1px),
          linear-gradient(0deg, rgba(24, 49, 40, 0.04) 1px, transparent 1px),
          #dfe7df;
        background-size: 28px 28px;
      }}
      main {{
        max-width: 980px;
        margin: 0 auto;
        border: 1px solid rgba(43, 79, 64, 0.16);
        background: #fbf7ed;
        padding: 40px;
        box-shadow: 0 18px 55px rgba(33, 47, 39, 0.13);
      }}
      h1 {{
        margin: 0 0 10px;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 46px;
        line-height: 1;
      }}
      .subtitle {{
        margin: 0 0 28px;
        color: #64726a;
      }}
      .brief-section {{
        border-top: 1px solid rgba(34, 48, 41, 0.14);
        padding: 24px 0 4px;
      }}
      .brief-section__meta {{
        display: inline-flex;
        margin-bottom: 10px;
        border: 1px solid rgba(142, 59, 70, 0.2);
        background: #f1ddd9;
        color: #8e3b46;
        padding: 4px 10px;
        font-size: 13px;
        font-weight: 700;
      }}
      h2 {{
        margin: 0 0 12px;
        font-size: 25px;
      }}
      p {{
        color: #3c4b42;
        line-height: 1.8;
      }}
      .evidence-ids {{
        margin-top: 14px;
        color: #64726a;
        font-size: 14px;
      }}
      @media (max-width: 680px) {{
        body {{ padding: 14px; }}
        main {{ padding: 24px; }}
        h1 {{ font-size: 36px; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>MarketLens AI 研究简报</h1>
      <p class="subtitle">由公开来源证据表生成，所有结论均保留支持证据 ID。</p>
      {"".join(section_html)}
    </main>
  </body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def evidence_to_json(rows: list[EvidenceRow]) -> list[dict[str, Any]]:
    return [row.to_dict() for row in rows if row.review_status != "rejected"]
