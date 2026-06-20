from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from marketlens.schemas import EvidenceRow, validate_evidence_row


def load_sources(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_evidence(path: Path) -> list[EvidenceRow]:
    rows: list[EvidenceRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            row = EvidenceRow(
                evidence_id=raw["evidence_id"],
                brand_id=raw["brand_id"],
                lens=raw["lens"],
                claim=raw["claim"],
                source_title=raw["source_title"],
                source_url=raw["source_url"],
                source_type=raw["source_type"],
                source_date=raw["source_date"],
                excerpt=raw["excerpt"],
                confidence=float(raw["confidence"]),
                review_status=raw["review_status"],
                notes=raw.get("notes", ""),
            )
            validate_evidence_row(row)
            rows.append(row)
    return rows
