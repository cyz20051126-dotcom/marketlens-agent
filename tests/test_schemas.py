import pytest

from marketlens.schemas import (
    ALLOWED_BRANDS,
    ALLOWED_LENSES,
    BrandProfile,
    EvidenceRow,
    ValidationError,
    validate_brand_profile,
    validate_evidence_row,
)


def test_allowed_brands_cover_v1_scope():
    assert {
        "luckin",
        "cotti",
        "starbucks",
        "mixue",
        "chagee",
        "guming",
        "chapanda",
    }.issubset(ALLOWED_BRANDS)


def test_evidence_row_requires_core_fields():
    row = EvidenceRow(
        evidence_id="ev_001",
        brand_id="luckin",
        lens="pricing",
        claim="Luckin uses frequent promotions to support high-frequency coffee consumption.",
        source_title="Example source",
        source_url="https://example.com/luckin",
        source_type="news",
        source_date="2026-01-01",
        excerpt="Luckin continued to use price promotions and store density as growth levers.",
        confidence=0.82,
        review_status="reviewed",
        notes="Seed row for schema validation.",
    )

    validate_evidence_row(row)


def test_evidence_row_rejects_unknown_brand():
    row = EvidenceRow(
        evidence_id="ev_002",
        brand_id="unknown",
        lens="pricing",
        claim="Invalid brand.",
        source_title="Example source",
        source_url="https://example.com",
        source_type="news",
        source_date="2026-01-01",
        excerpt="Invalid brand example.",
        confidence=0.5,
        review_status="reviewed",
        notes="",
    )

    with pytest.raises(ValidationError, match="brand_id"):
        validate_evidence_row(row)


def test_evidence_row_rejects_unknown_lens():
    row = EvidenceRow(
        evidence_id="ev_003",
        brand_id="luckin",
        lens="valuation",
        claim="Invalid lens.",
        source_title="Example source",
        source_url="https://example.com",
        source_type="news",
        source_date="2026-01-01",
        excerpt="Invalid lens example.",
        confidence=0.5,
        review_status="reviewed",
        notes="",
    )

    with pytest.raises(ValidationError, match="lens"):
        validate_evidence_row(row)


def test_allowed_lenses_cover_v1_scope():
    assert {
        "pricing",
        "expansion",
        "franchise",
        "positioning",
        "risk",
    }.issubset(ALLOWED_LENSES)


def test_brand_profile_validation_accepts_matrix_coordinates():
    profile = BrandProfile(
        brand_id="chagee",
        name="霸王茶姬",
        category="tea",
        market_position="Premium tea chain with strong brand narrative.",
        price_signal="premium",
        expansion_model="franchise_and_direct",
        franchise_model="franchise-led expansion with brand controls",
        brand_narrative="Chinese-style modern tea brand.",
        risk_signal="category competition and overseas execution",
        matrix_x=0.72,
        matrix_y=0.78,
        evidence_count=5,
        confidence=0.76,
    )

    validate_brand_profile(profile)
