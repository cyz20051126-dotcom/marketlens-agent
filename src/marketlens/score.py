from __future__ import annotations

from marketlens.schemas import EvidenceRow, validate_evidence_row


SOURCE_WEIGHTS = {
    "annual_report": 0.95,
    "prospectus": 0.92,
    "company_site": 0.82,
    "industry_report": 0.78,
    "job_posting": 0.64,
    "news": 0.58,
}

REVIEW_STATUS_MULTIPLIERS = {
    "reviewed": 1.0,
    "needs_review": 0.72,
    "rejected": 0.0,
}


def score_evidence(row: EvidenceRow) -> float:
    validate_evidence_row(row)

    source_score = SOURCE_WEIGHTS[row.source_type]
    excerpt_score = min(len(row.excerpt.strip()) / 120, 1.0) * 0.12
    confidence_score = row.confidence * 0.18
    url_score = 0.04 if row.source_url.startswith("https://") else 0.02

    raw_score = (source_score * 0.66) + excerpt_score + confidence_score + url_score
    adjusted = raw_score * REVIEW_STATUS_MULTIPLIERS[row.review_status]
    return round(max(0.0, min(adjusted, 1.0)), 4)
