from marketlens.schemas import EvidenceRow
from marketlens.score import score_evidence


def make_row(source_type: str, excerpt: str, review_status: str = "reviewed") -> EvidenceRow:
    return EvidenceRow(
        evidence_id="ev_test",
        brand_id="luckin",
        lens="pricing",
        claim="A source-backed claim.",
        source_title="Example",
        source_url="https://example.com/source",
        source_type=source_type,
        source_date="2026-01-01",
        excerpt=excerpt,
        confidence=0.50,
        review_status=review_status,
        notes="",
    )


def test_score_evidence_rewards_primary_sources():
    row = make_row(
        "prospectus",
        "This is a sufficiently detailed excerpt about expansion and franchise strategy.",
    )

    assert score_evidence(row) >= 0.80


def test_score_evidence_penalizes_needs_review():
    reviewed = make_row("news", "This excerpt has enough detail to support the claim.", "reviewed")
    needs_review = make_row(
        "news",
        "This excerpt has enough detail to support the claim.",
        "needs_review",
    )

    assert score_evidence(needs_review) < score_evidence(reviewed)
