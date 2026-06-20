from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ALLOWED_BRANDS = {
    "luckin",
    "cotti",
    "starbucks",
    "mixue",
    "chagee",
    "guming",
    "chapanda",
}

ALLOWED_LENSES = {
    "pricing",
    "expansion",
    "franchise",
    "positioning",
    "risk",
}

ALLOWED_SOURCE_TYPES = {
    "annual_report",
    "prospectus",
    "company_site",
    "news",
    "industry_report",
    "job_posting",
}

ALLOWED_REVIEW_STATUS = {"reviewed", "needs_review", "rejected"}


class ValidationError(ValueError):
    """Raised when a MarketLens artifact row is invalid."""


@dataclass(frozen=True)
class EvidenceRow:
    evidence_id: str
    brand_id: str
    lens: str
    claim: str
    source_title: str
    source_url: str
    source_type: str
    source_date: str
    excerpt: str
    confidence: float
    review_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrandProfile:
    brand_id: str
    name: str
    category: str
    market_position: str
    price_signal: str
    expansion_model: str
    franchise_model: str
    brand_narrative: str
    risk_signal: str
    matrix_x: float
    matrix_y: float
    evidence_count: int
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BriefSection:
    section_id: str
    title: str
    summary: str
    supporting_evidence_ids: list[str]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} must be a non-empty string")


def _require_range(value: float, field_name: str) -> None:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be numeric") from exc
    if not 0.0 <= numeric <= 1.0:
        raise ValidationError(f"{field_name} must be between 0 and 1")


def validate_evidence_row(row: EvidenceRow) -> None:
    _require_text(row.evidence_id, "evidence_id")
    _require_text(row.brand_id, "brand_id")
    _require_text(row.lens, "lens")
    _require_text(row.claim, "claim")
    _require_text(row.source_title, "source_title")
    _require_text(row.source_url, "source_url")
    _require_text(row.source_type, "source_type")
    _require_text(row.source_date, "source_date")
    _require_text(row.excerpt, "excerpt")
    _require_text(row.review_status, "review_status")
    _require_range(row.confidence, "confidence")

    if row.brand_id not in ALLOWED_BRANDS:
        raise ValidationError(f"brand_id is not supported: {row.brand_id}")
    if row.lens not in ALLOWED_LENSES:
        raise ValidationError(f"lens is not supported: {row.lens}")
    if row.source_type not in ALLOWED_SOURCE_TYPES:
        raise ValidationError(f"source_type is not supported: {row.source_type}")
    if row.review_status not in ALLOWED_REVIEW_STATUS:
        raise ValidationError(f"review_status is not supported: {row.review_status}")
    if not row.source_url.startswith(("http://", "https://")):
        raise ValidationError("source_url must start with http:// or https://")


def validate_brand_profile(profile: BrandProfile) -> None:
    _require_text(profile.brand_id, "brand_id")
    _require_text(profile.name, "name")
    _require_text(profile.category, "category")
    _require_text(profile.market_position, "market_position")
    _require_text(profile.price_signal, "price_signal")
    _require_text(profile.expansion_model, "expansion_model")
    _require_text(profile.franchise_model, "franchise_model")
    _require_text(profile.brand_narrative, "brand_narrative")
    _require_text(profile.risk_signal, "risk_signal")
    _require_range(profile.matrix_x, "matrix_x")
    _require_range(profile.matrix_y, "matrix_y")
    _require_range(profile.confidence, "confidence")

    if profile.brand_id not in ALLOWED_BRANDS:
        raise ValidationError(f"brand_id is not supported: {profile.brand_id}")
    if profile.evidence_count < 0:
        raise ValidationError("evidence_count must be non-negative")
