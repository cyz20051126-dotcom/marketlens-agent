# MarketLens AI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete portfolio-ready MarketLens AI project: source-backed fresh beverage competitive intelligence workflow, Python artifact pipeline, premium React/Vite research desk UI, exports, README, SOP, and verification.

**Architecture:** Use a Python package to validate evidence, score confidence, synthesize brand profiles, and export JSON/CSV/Markdown artifacts. Use a React/Vite frontend to render a polished Premium Research Desk using static exported artifacts. Keep live scraping optional and cache-backed so the demo never depends on network availability.

**Tech Stack:** Python 3.11+, standard library dataclasses/csv/json/pathlib, pytest, React, Vite, TypeScript, CSS, optional Firecrawl CLI for source collection, Playwright screenshot verification.

---

## Scope Check

This is one coherent portfolio project, but it has five deliverable surfaces:

- data and evidence artifacts,
- Python pipeline,
- React/Vite web demo,
- documentation package,
- verification outputs.

Do not expand V1 into login, cloud database, fully autonomous crawler, investment recommendation, or resume/job automation. The project must stay explainable in a 2-minute interview.

## Skill Usage During Execution

Use these skills at the relevant implementation phase:

- `firecrawl-search` / `firecrawl-scrape`: collect or refresh public source snippets.
- `python-project-structure`: keep the Python package clean and focused.
- `frontend-design`: implement the Premium Research Desk UI polish.
- `kpi-dashboard-design`: keep metrics and dashboard hierarchy meaningful.
- `github-readme-generator`: structure the README after implementation, but rewrite it for this project.
- `superpowers:verification-before-completion`: run before claiming the project is complete.

## File Structure

Create this structure under `C:\Users\chenyizhe\Desktop\MarketLens_AI`:

```text
MarketLens_AI/
  .gitignore
  README.md
  pyproject.toml
  scripts/
    build_artifacts.py
    collect_sources_firecrawl.ps1
  data/
    sources.json
    evidence.csv
    processed/
      brands.json
      evidence.json
      brief.md
      brief_sections.json
  docs/
    workflow_sop.md
    prompt_templates.md
    interview_talking_points.md
    superpowers/
      specs/
        2026-06-19-marketlens-ai-design.md
      plans/
        2026-06-19-marketlens-ai-implementation.md
  src/
    marketlens/
      __init__.py
      schemas.py
      load.py
      score.py
      synthesize.py
      export.py
  tests/
    test_schemas.py
    test_score.py
    test_export.py
  web/
    package.json
    tsconfig.json
    vite.config.ts
    index.html
    public/
      data/
        brief.md
        evidence.json
    src/
      main.tsx
      App.tsx
      styles.css
      data/
        brands.json
        evidence.json
        brief.md
      components/
        BrandCards.tsx
        EvidenceTable.tsx
        ExecutiveBrief.tsx
        ExportPanel.tsx
        PositioningMatrix.tsx
        ScopeControl.tsx
        WorkflowTrace.tsx
```

## Task 1: Repository And Environment Baseline

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `src/marketlens/__init__.py`
- Create: `scripts/build_artifacts.py`
- Create: `tests/test_schemas.py`

- [ ] **Step 1: Initialize git repository**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI
git init
```

Expected: repository initialized in `C:\Users\chenyizhe\Desktop\MarketLens_AI\.git`.

- [ ] **Step 2: Create `.gitignore`**

Write:

```gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
node_modules/
dist/
web/dist/
.env
.firecrawl/
screenshots/
```

- [ ] **Step 3: Create `pyproject.toml`**

Write:

```toml
[project]
name = "marketlens-ai"
version = "0.1.0"
description = "Source-backed competitive intelligence workflow for fresh beverage brands."
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.2"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 4: Create package marker**

Write `src/marketlens/__init__.py`:

```python
"""MarketLens AI artifact pipeline."""

__all__ = []
```

- [ ] **Step 5: Create a temporary failing import test**

Write `tests/test_schemas.py`:

```python
def test_marketlens_package_imports():
    import marketlens

    assert marketlens.__doc__
```

- [ ] **Step 6: Create virtual environment and install dev dependencies**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Expected: editable package install succeeds.

- [ ] **Step 7: Run the first test**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q
```

Expected: `1 passed`.

- [ ] **Step 8: Commit baseline**

Run:

```powershell
git add .gitignore pyproject.toml src tests
git commit -m "chore: initialize marketlens project"
```

Expected: baseline commit created.

## Task 2: Data Schema And Validation

**Files:**
- Create: `src/marketlens/schemas.py`
- Modify: `tests/test_schemas.py`

- [ ] **Step 1: Replace schema tests with failing validation tests**

Write `tests/test_schemas.py`:

```python
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


def test_brand_profile_validation_accepts_matrix_coordinates():
    profile = BrandProfile(
        brand_id="chagee",
        name="CHAGEE",
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
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_schemas.py -q
```

Expected: FAIL because `marketlens.schemas` does not exist.

- [ ] **Step 3: Implement `src/marketlens/schemas.py`**

Write:

```python
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
    if not 0.0 <= float(value) <= 1.0:
        raise ValidationError(f"{field_name} must be between 0 and 1")


def validate_evidence_row(row: EvidenceRow) -> None:
    _require_text(row.evidence_id, "evidence_id")
    _require_text(row.brand_id, "brand_id")
    _require_text(row.lens, "lens")
    _require_text(row.claim, "claim")
    _require_text(row.source_title, "source_title")
    _require_text(row.source_url, "source_url")
    _require_text(row.source_type, "source_type")
    _require_text(row.excerpt, "excerpt")
    _require_range(row.confidence, "confidence")

    if row.brand_id not in ALLOWED_BRANDS:
        raise ValidationError(f"brand_id is not supported: {row.brand_id}")
    if row.lens not in ALLOWED_LENSES:
        raise ValidationError(f"lens is not supported: {row.lens}")
    if row.source_type not in ALLOWED_SOURCE_TYPES:
        raise ValidationError(f"source_type is not supported: {row.source_type}")
    if row.review_status not in ALLOWED_REVIEW_STATUS:
        raise ValidationError(f"review_status is not supported: {row.review_status}")
    if not row.source_url.startswith(("https://", "http://")):
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
    if profile.category not in {"coffee", "tea"}:
        raise ValidationError(f"category is not supported: {profile.category}")
    if profile.evidence_count < 0:
        raise ValidationError("evidence_count must be non-negative")
```

- [ ] **Step 4: Run schema tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_schemas.py -q
```

Expected: all schema tests pass.

- [ ] **Step 5: Commit schema layer**

Run:

```powershell
git add src/marketlens/schemas.py tests/test_schemas.py
git commit -m "feat: add marketlens schema validation"
```

Expected: schema commit created.

## Task 3: Source Registry And Evidence Dataset

**Files:**
- Create: `data/sources.json`
- Create: `data/evidence.csv`
- Create: `scripts/collect_sources_firecrawl.ps1`

- [ ] **Step 1: Create `data/sources.json` with source registry schema**

Write:

```json
{
  "dataset_version": "2026-06-19-v1",
  "industry": "fresh_beverage_chains_china",
  "brands": [
    {"brand_id": "luckin", "name": "Luckin Coffee", "category": "coffee"},
    {"brand_id": "cotti", "name": "Cotti Coffee", "category": "coffee"},
    {"brand_id": "starbucks", "name": "Starbucks China", "category": "coffee"},
    {"brand_id": "mixue", "name": "Mixue Bingcheng", "category": "tea"},
    {"brand_id": "chagee", "name": "CHAGEE", "category": "tea"},
    {"brand_id": "guming", "name": "Guming", "category": "tea"},
    {"brand_id": "chapanda", "name": "ChaPanda", "category": "tea"}
  ],
  "collection_queries": [
    "Luckin Coffee China price promotion store density 2025 2026",
    "Cotti Coffee price war expansion China 2025 2026",
    "Starbucks China strategy store expansion 2025 2026",
    "Mixue Bingcheng prospectus franchise store expansion",
    "CHAGEE prospectus premium tea expansion 2025 2026",
    "Guming prospectus tea drink franchise expansion",
    "ChaPanda prospectus tea drink franchise expansion",
    "China fresh beverage tea coffee market price war 2025 2026"
  ],
  "source_policy": {
    "allowed_source_types": ["annual_report", "prospectus", "company_site", "news", "industry_report", "job_posting"],
    "claim_rule": "Every brief claim must cite at least one evidence row with source_url and source_type.",
    "review_rule": "Rows with confidence below 0.70 stay visible but are marked needs_review."
  }
}
```

- [ ] **Step 2: Create `data/evidence.csv` header and 28 reviewed rows**

Write CSV with this exact header:

```csv
evidence_id,brand_id,lens,claim,source_title,source_url,source_type,source_date,excerpt,confidence,review_status,notes
```

Use 4 rows per brand, one row per key lens when available. During execution, collect source URLs with Firecrawl or web search before finalizing rows. The completed file must contain:

- 4 Luckin rows,
- 4 Cotti rows,
- 4 Starbucks rows,
- 4 Mixue rows,
- 4 CHAGEE rows,
- 4 Guming rows,
- 4 ChaPanda rows.

Every row must have a real `source_url`, a concise `claim`, and an excerpt under 260 characters.

- [ ] **Step 3: Add Firecrawl collection helper**

Write `scripts/collect_sources_firecrawl.ps1`:

```powershell
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$outDir = Join-Path $root ".firecrawl\marketlens_sources"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$queries = @(
  "Luckin Coffee China price promotion store density 2025 2026",
  "Cotti Coffee price war expansion China 2025 2026",
  "Starbucks China strategy store expansion 2025 2026",
  "Mixue Bingcheng prospectus franchise store expansion",
  "CHAGEE prospectus premium tea expansion 2025 2026",
  "Guming prospectus tea drink franchise expansion",
  "ChaPanda prospectus tea drink franchise expansion",
  "China fresh beverage tea coffee market price war 2025 2026"
)

foreach ($query in $queries) {
  $slug = ($query.ToLower() -replace '[^a-z0-9]+', '-') -replace '(^-|-$)', ''
  $target = Join-Path $outDir "$slug.json"
  firecrawl search $query --limit 5 --format json | Out-File -FilePath $target -Encoding utf8
  Write-Output "Saved $target"
}
```

- [ ] **Step 4: Run source helper only if Firecrawl is authenticated**

Run:

```powershell
firecrawl --status
```

Expected: authenticated status. If authenticated, run:

```powershell
.\scripts\collect_sources_firecrawl.ps1
```

Expected: JSON files saved in `.firecrawl\marketlens_sources`.

- [ ] **Step 5: Commit source registry and evidence dataset**

Run:

```powershell
git add data scripts/collect_sources_firecrawl.ps1
git commit -m "data: add marketlens source registry and evidence seed"
```

Expected: data commit created.

## Task 4: Loading, Scoring, And Synthesis Pipeline

**Files:**
- Create: `src/marketlens/load.py`
- Create: `src/marketlens/score.py`
- Create: `src/marketlens/synthesize.py`
- Create: `tests/test_score.py`

- [ ] **Step 1: Write scoring tests**

Write `tests/test_score.py`:

```python
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
    row = make_row("prospectus", "This is a sufficiently detailed excerpt about expansion and franchise strategy.")

    assert score_evidence(row) >= 0.80


def test_score_evidence_penalizes_needs_review():
    reviewed = make_row("news", "This excerpt has enough detail to support the claim.", "reviewed")
    needs_review = make_row("news", "This excerpt has enough detail to support the claim.", "needs_review")

    assert score_evidence(needs_review) < score_evidence(reviewed)
```

- [ ] **Step 2: Run scoring tests and verify they fail**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_score.py -q
```

Expected: FAIL because `marketlens.score` does not exist.

- [ ] **Step 3: Implement CSV loader**

Write `src/marketlens/load.py`:

```python
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from marketlens.schemas import EvidenceRow, validate_evidence_row


def load_sources(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
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
```

- [ ] **Step 4: Implement evidence scoring**

Write `src/marketlens/score.py`:

```python
from __future__ import annotations

from marketlens.schemas import EvidenceRow


SOURCE_WEIGHTS = {
    "prospectus": 0.88,
    "annual_report": 0.86,
    "company_site": 0.78,
    "industry_report": 0.76,
    "news": 0.70,
    "job_posting": 0.66,
}


def score_evidence(row: EvidenceRow) -> float:
    base = SOURCE_WEIGHTS[row.source_type]
    excerpt_bonus = 0.04 if len(row.excerpt.strip()) >= 48 else 0.0
    url_bonus = 0.02 if row.source_url.startswith("https://") else 0.0
    review_penalty = -0.12 if row.review_status == "needs_review" else 0.0
    rejected_penalty = -0.40 if row.review_status == "rejected" else 0.0
    score = base + excerpt_bonus + url_bonus + review_penalty + rejected_penalty
    return round(max(0.0, min(score, 0.98)), 2)
```

- [ ] **Step 5: Implement synthesis**

Write `src/marketlens/synthesize.py`:

```python
from __future__ import annotations

from collections import defaultdict
from statistics import mean

from marketlens.schemas import BrandProfile, BriefSection, EvidenceRow, validate_brand_profile
from marketlens.score import score_evidence


BRAND_STATIC = {
    "luckin": {
        "name": "Luckin Coffee",
        "category": "coffee",
        "market_position": "High-frequency coffee chain competing through density, convenience, and promotion cadence.",
        "price_signal": "mass-market promotional",
        "expansion_model": "dense store network and delivery-led convenience",
        "franchise_model": "mixed store model with strong digital operations",
        "brand_narrative": "daily coffee with technology-enabled convenience",
        "risk_signal": "promotion intensity and same-store competition",
        "matrix_x": 0.28,
        "matrix_y": 0.36,
    },
    "cotti": {
        "name": "Cotti Coffee",
        "category": "coffee",
        "market_position": "Aggressive challenger using low prices and fast expansion to attack daily coffee occasions.",
        "price_signal": "low-price challenger",
        "expansion_model": "rapid store rollout and promotion-led acquisition",
        "franchise_model": "franchise-heavy expansion",
        "brand_narrative": "accessible coffee under price pressure",
        "risk_signal": "unit economics and promotion sustainability",
        "matrix_x": 0.18,
        "matrix_y": 0.26,
    },
    "starbucks": {
        "name": "Starbucks China",
        "category": "coffee",
        "market_position": "Premium coffee chain balancing brand equity, store experience, and localized competition.",
        "price_signal": "premium",
        "expansion_model": "selective store network and experience-led retail",
        "franchise_model": "direct-operated core model in China",
        "brand_narrative": "third-place coffee experience",
        "risk_signal": "traffic pressure from lower-priced local chains",
        "matrix_x": 0.38,
        "matrix_y": 0.68,
    },
    "mixue": {
        "name": "Mixue Bingcheng",
        "category": "tea",
        "market_position": "Mass-market tea and ice cream chain with large franchise scale and value positioning.",
        "price_signal": "value-for-money",
        "expansion_model": "large-scale franchise network",
        "franchise_model": "franchise-led",
        "brand_narrative": "affordable everyday drinks",
        "risk_signal": "franchise management and low-price competition",
        "matrix_x": 0.76,
        "matrix_y": 0.30,
    },
    "chagee": {
        "name": "CHAGEE",
        "category": "tea",
        "market_position": "Premium modern Chinese tea brand emphasizing cultural narrative and product identity.",
        "price_signal": "premium tea",
        "expansion_model": "brand-led expansion with domestic and overseas ambition",
        "franchise_model": "controlled expansion model",
        "brand_narrative": "modern Chinese tea culture",
        "risk_signal": "premium positioning durability and overseas execution",
        "matrix_x": 0.68,
        "matrix_y": 0.78,
    },
    "guming": {
        "name": "Guming",
        "category": "tea",
        "market_position": "Large tea chain focused on lower-tier city density and franchise expansion.",
        "price_signal": "mid-market",
        "expansion_model": "regional penetration and franchise scale",
        "franchise_model": "franchise-led",
        "brand_narrative": "daily fresh tea drinks",
        "risk_signal": "competition in mid-market tea formats",
        "matrix_x": 0.72,
        "matrix_y": 0.52,
    },
    "chapanda": {
        "name": "ChaPanda",
        "category": "tea",
        "market_position": "Scaled tea chain positioned around broad menu coverage and franchise network growth.",
        "price_signal": "mid-market",
        "expansion_model": "franchise network and broad product coverage",
        "franchise_model": "franchise-led",
        "brand_narrative": "accessible fresh tea drinks",
        "risk_signal": "brand differentiation in crowded tea market",
        "matrix_x": 0.80,
        "matrix_y": 0.48,
    },
}


def build_brand_profiles(evidence_rows: list[EvidenceRow]) -> list[BrandProfile]:
    evidence_by_brand: dict[str, list[EvidenceRow]] = defaultdict(list)
    for row in evidence_rows:
        if row.review_status != "rejected":
            evidence_by_brand[row.brand_id].append(row)

    profiles: list[BrandProfile] = []
    for brand_id, attrs in BRAND_STATIC.items():
        brand_rows = evidence_by_brand[brand_id]
        confidence = mean([score_evidence(row) for row in brand_rows]) if brand_rows else 0.0
        profile = BrandProfile(
            brand_id=brand_id,
            name=attrs["name"],
            category=attrs["category"],
            market_position=attrs["market_position"],
            price_signal=attrs["price_signal"],
            expansion_model=attrs["expansion_model"],
            franchise_model=attrs["franchise_model"],
            brand_narrative=attrs["brand_narrative"],
            risk_signal=attrs["risk_signal"],
            matrix_x=attrs["matrix_x"],
            matrix_y=attrs["matrix_y"],
            evidence_count=len(brand_rows),
            confidence=round(confidence, 2),
        )
        validate_brand_profile(profile)
        profiles.append(profile)
    return profiles


def build_brief_sections(evidence_rows: list[EvidenceRow], profiles: list[BrandProfile]) -> list[BriefSection]:
    reviewed_ids = [row.evidence_id for row in evidence_rows if row.review_status == "reviewed"]
    avg_confidence = round(mean([profile.confidence for profile in profiles]), 2)
    return [
        BriefSection(
            section_id="thesis",
            title="Two growth playbooks are emerging",
            summary=(
                "Coffee chains compete around purchase frequency, store density, convenience, "
                "and price pressure, while tea chains rely more on product storytelling, "
                "franchise scale, and differentiated brand formats."
            ),
            supporting_evidence_ids=reviewed_ids[:8],
            confidence=avg_confidence,
        ),
        BriefSection(
            section_id="coffee_logic",
            title="Coffee competition is efficiency-led",
            summary=(
                "Luckin, Cotti, and Starbucks show different responses to the same category pressure: "
                "high-frequency consumption makes pricing, density, and convenience central."
            ),
            supporting_evidence_ids=[row.evidence_id for row in evidence_rows if row.brand_id in {"luckin", "cotti", "starbucks"}][:8],
            confidence=avg_confidence,
        ),
        BriefSection(
            section_id="tea_logic",
            title="Tea brands compete through format and franchise scale",
            summary=(
                "Mixue, CHAGEE, Guming, and ChaPanda show how value positioning, premium narrative, "
                "and franchise execution create different growth paths within tea drinks."
            ),
            supporting_evidence_ids=[row.evidence_id for row in evidence_rows if row.brand_id in {"mixue", "chagee", "guming", "chapanda"}][:10],
            confidence=avg_confidence,
        ),
    ]
```

- [ ] **Step 6: Run scoring tests and all tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit pipeline core**

Run:

```powershell
git add src/marketlens/load.py src/marketlens/score.py src/marketlens/synthesize.py tests/test_score.py
git commit -m "feat: add evidence scoring and synthesis pipeline"
```

Expected: pipeline commit created.

## Task 5: Export Artifacts CLI

**Files:**
- Create: `src/marketlens/export.py`
- Modify: `scripts/build_artifacts.py`
- Create: `tests/test_export.py`

- [ ] **Step 1: Write export tests**

Write `tests/test_export.py`:

```python
import json
from pathlib import Path

from marketlens.export import write_json, write_markdown_brief
from marketlens.schemas import BriefSection


def test_write_json_creates_parent_directory(tmp_path: Path):
    target = tmp_path / "nested" / "artifact.json"

    write_json(target, [{"brand_id": "luckin"}])

    assert json.loads(target.read_text(encoding="utf-8")) == [{"brand_id": "luckin"}]


def test_write_markdown_brief_includes_evidence_ids(tmp_path: Path):
    target = tmp_path / "brief.md"
    sections = [
        BriefSection(
            section_id="thesis",
            title="Two growth playbooks",
            summary="Coffee and tea chains differ in their growth logic.",
            supporting_evidence_ids=["ev_001", "ev_002"],
            confidence=0.82,
        )
    ]

    write_markdown_brief(target, sections)

    text = target.read_text(encoding="utf-8")
    assert "# MarketLens AI Brief" in text
    assert "ev_001" in text
    assert "Confidence: 0.82" in text
```

- [ ] **Step 2: Run export tests and verify they fail**

Run:

```powershell
.\.venv\Scripts\python -m pytest tests/test_export.py -q
```

Expected: FAIL because `marketlens.export` does not exist.

- [ ] **Step 3: Implement export helpers**

Write `src/marketlens/export.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from marketlens.schemas import BriefSection, EvidenceRow


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown_brief(path: Path, sections: list[BriefSection]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MarketLens AI Brief",
        "",
        "Fresh beverage competitive intelligence demo covering coffee and tea chains.",
        "",
    ]
    for section in sections:
        lines.extend(
            [
                f"## {section.title}",
                "",
                section.summary,
                "",
                f"Confidence: {section.confidence:.2f}",
                "",
                "Supporting evidence: " + ", ".join(section.supporting_evidence_ids),
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def evidence_to_json(rows: list[EvidenceRow]) -> list[dict[str, Any]]:
    return [row.to_dict() for row in rows if row.review_status != "rejected"]
```

- [ ] **Step 4: Implement build script**

Write `scripts/build_artifacts.py`:

```python
from __future__ import annotations

import shutil
from pathlib import Path

from marketlens.export import evidence_to_json, write_json, write_markdown_brief
from marketlens.load import load_evidence
from marketlens.synthesize import build_brand_profiles, build_brief_sections


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
WEB_DATA = ROOT / "web" / "src" / "data"
WEB_PUBLIC_DATA = ROOT / "web" / "public" / "data"


def main() -> None:
    evidence_rows = load_evidence(DATA / "evidence.csv")
    brand_profiles = build_brand_profiles(evidence_rows)
    brief_sections = build_brief_sections(evidence_rows, brand_profiles)

    write_json(PROCESSED / "brands.json", [profile.to_dict() for profile in brand_profiles])
    write_json(PROCESSED / "evidence.json", evidence_to_json(evidence_rows))
    write_json(PROCESSED / "brief_sections.json", [section.to_dict() for section in brief_sections])
    write_markdown_brief(PROCESSED / "brief.md", brief_sections)

    WEB_DATA.mkdir(parents=True, exist_ok=True)
    WEB_PUBLIC_DATA.mkdir(parents=True, exist_ok=True)
    for name in ["brands.json", "evidence.json", "brief.md", "brief_sections.json"]:
        shutil.copyfile(PROCESSED / name, WEB_DATA / name)
        shutil.copyfile(PROCESSED / name, WEB_PUBLIC_DATA / name)

    print(f"Built MarketLens artifacts in {PROCESSED}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests**

Run:

```powershell
.\.venv\Scripts\python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 6: Build artifacts**

Run:

```powershell
.\.venv\Scripts\python scripts\build_artifacts.py
```

Expected:

- `data/processed/brands.json` exists,
- `data/processed/evidence.json` exists,
- `data/processed/brief_sections.json` exists,
- `data/processed/brief.md` exists,
- same files copied to `web/src/data/` and `web/public/data/`.

- [ ] **Step 7: Commit export pipeline**

Run:

```powershell
git add src/marketlens/export.py scripts/build_artifacts.py tests/test_export.py data/processed web/src/data
git commit -m "feat: export marketlens portfolio artifacts"
```

Expected: export commit created.

## Task 6: React/Vite Frontend Scaffold

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/vite.config.ts`
- Create: `web/index.html`
- Create: `web/src/main.tsx`
- Create: `web/src/App.tsx`
- Create: `web/src/styles.css`

- [ ] **Step 1: Create `web/package.json`**

Write:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host 127.0.0.1"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "typescript": "latest",
    "react": "latest",
    "react-dom": "latest",
    "lucide-react": "latest"
  },
  "devDependencies": {
    "@types/react": "latest",
    "@types/react-dom": "latest"
  }
}
```

- [ ] **Step 2: Create `web/tsconfig.json`**

Write:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": []
}
```

- [ ] **Step 3: Create `web/vite.config.ts`**

Write:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});
```

- [ ] **Step 4: Create `web/index.html`**

Write:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MarketLens AI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Create `web/src/main.tsx`**

Write:

```tsx
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 6: Create initial `web/src/App.tsx`**

Write:

```tsx
export default function App() {
  return (
    <main className="app-shell">
      <section className="hero-card">
        <p className="eyebrow">MarketLens AI / Fresh Beverage Intelligence</p>
        <h1>Two Growth Playbooks Are Emerging in Fresh Beverage Chains</h1>
        <p className="lede">
          A source-backed competitive intelligence workflow for tea and coffee brands.
        </p>
      </section>
    </main>
  );
}
```

- [ ] **Step 7: Create initial `web/src/styles.css`**

Write:

```css
:root {
  color: #172025;
  background: #dfe8e4;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  min-height: 100vh;
  background:
    radial-gradient(circle at 22% 12%, rgba(132, 53, 75, 0.14), transparent 26%),
    radial-gradient(circle at 88% 78%, rgba(44, 121, 102, 0.17), transparent 26%),
    linear-gradient(135deg, #dfe8e4 0%, #eef1ea 44%, #dce5e1 100%);
}

button,
input,
select {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
  padding: 24px;
}

.hero-card {
  max-width: 980px;
  margin: 0 auto;
  border: 1px solid rgba(70, 88, 91, 0.22);
  border-radius: 20px;
  padding: 32px;
  background: linear-gradient(135deg, rgba(255, 254, 248, 0.96), rgba(246, 241, 229, 0.84));
  box-shadow: 0 18px 42px rgba(45, 60, 62, 0.11);
}

.eyebrow {
  margin: 0 0 18px;
  color: #84354b;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 12px;
  font-weight: 800;
}

h1 {
  max-width: 780px;
  margin: 0;
  color: #131b20;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(42px, 6vw, 68px);
  line-height: 0.98;
  letter-spacing: -0.052em;
  font-weight: 600;
}

.lede {
  max-width: 680px;
  margin: 20px 0 0;
  color: #4c595d;
  line-height: 1.68;
  font-size: 16px;
}
```

- [ ] **Step 8: Install and build frontend**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI\web
npm install
npm run build
```

Expected: build succeeds and creates `web/dist`.

- [ ] **Step 9: Commit frontend scaffold**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI
git add web/package.json web/package-lock.json web/tsconfig.json web/vite.config.ts web/index.html web/src
git commit -m "feat: scaffold marketlens frontend"
```

Expected: frontend scaffold commit created.

## Task 7: Premium Research Desk Components

**Files:**
- Create: `web/src/components/ExecutiveBrief.tsx`
- Create: `web/src/components/WorkflowTrace.tsx`
- Create: `web/src/components/ScopeControl.tsx`
- Create: `web/src/components/PositioningMatrix.tsx`
- Create: `web/src/components/BrandCards.tsx`
- Create: `web/src/components/EvidenceTable.tsx`
- Create: `web/src/components/ExportPanel.tsx`
- Modify: `web/src/App.tsx`
- Modify: `web/src/styles.css`

- [ ] **Step 1: Define frontend data types inside `App.tsx`**

Use exported JSON files from `web/src/data`.

```tsx
import brands from "./data/brands.json";
import evidence from "./data/evidence.json";
import briefSections from "./data/brief_sections.json";

export type BrandProfile = {
  brand_id: string;
  name: string;
  category: "coffee" | "tea";
  market_position: string;
  price_signal: string;
  expansion_model: string;
  franchise_model: string;
  brand_narrative: string;
  risk_signal: string;
  matrix_x: number;
  matrix_y: number;
  evidence_count: number;
  confidence: number;
};

export type EvidenceRow = {
  evidence_id: string;
  brand_id: string;
  lens: string;
  claim: string;
  source_title: string;
  source_url: string;
  source_type: string;
  source_date: string;
  excerpt: string;
  confidence: number;
  review_status: string;
  notes: string;
};

export type BriefSection = {
  section_id: string;
  title: string;
  summary: string;
  supporting_evidence_ids: string[];
  confidence: number;
};

const brandProfiles = brands as BrandProfile[];
const evidenceRows = evidence as EvidenceRow[];
const sections = briefSections as BriefSection[];
```

- [ ] **Step 2: Create `WorkflowTrace.tsx` with visible number badges**

Write:

```tsx
const steps = [
  ["1", "Search", "Public pages, reports, news", "done"],
  ["2", "Extract", "Brand facts and claims", "done"],
  ["3", "Score", "Source confidence", "review"],
  ["4", "Synthesize", "Matrix and brief", "ready"],
];

export function WorkflowTrace() {
  return (
    <section className="process-card">
      <div className="panel-heading">
        <h2>Visible AI Workflow</h2>
        <span className="soft-badge">Traceable</span>
      </div>
      <div className="workflow-list">
        {steps.map(([number, title, subtitle, status]) => (
          <article className="workflow-step" key={number}>
            <div className="workflow-number" aria-label={`Step ${number}`}>{number}</div>
            <div>
              <strong>{title}</strong>
              <em>{subtitle}</em>
            </div>
            <span className="workflow-status">{status}</span>
          </article>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Create remaining component files**

Each component consumes props and renders no hidden business logic:

```tsx
// ExecutiveBrief.tsx
import type { BriefSection } from "../App";

export function ExecutiveBrief({ sections }: { sections: BriefSection[] }) {
  return (
    <section className="cover-card">
      <p className="eyebrow">Competitive Brief / Tea + Coffee Chains</p>
      <h1>Two Growth Playbooks Are Emerging in Fresh Beverage Chains</h1>
      <p className="lede">
        MarketLens AI turns public sources into an analyst-ready brief: category thesis,
        competitor matrix, source-backed evidence, and exportable research notes.
      </p>
      <div className="thesis-grid">
        {sections.slice(1, 3).map((section) => (
          <article className="thesis-card" key={section.section_id}>
            <strong>{section.title}</strong>
            <span>{section.summary}</span>
          </article>
        ))}
      </div>
    </section>
  );
}
```

```tsx
// PositioningMatrix.tsx
import type { BrandProfile } from "../App";

export function PositioningMatrix({ brands }: { brands: BrandProfile[] }) {
  return (
    <section className="panel matrix-panel">
      <h2>Positioning Matrix <small>price pressure vs. premium narrative</small></h2>
      <div className="matrix">
        <div className="axis top"><span>Lower ticket / high frequency</span><span>Premium narrative</span></div>
        <div className="axis bottom"><span>Coffee density logic</span><span>Tea franchise logic</span></div>
        {brands.map((brand) => (
          <span
            key={brand.brand_id}
            className={`matrix-point ${brand.category}`}
            style={{ left: `${brand.matrix_x * 100}%`, top: `${(1 - brand.matrix_y) * 100}%` }}
            title={brand.name}
          />
        ))}
      </div>
      <div className="legend"><span>Coffee</span><span>Tea</span><span>Premium signal</span></div>
    </section>
  );
}
```

```tsx
// ScopeControl.tsx
import type { BrandProfile } from "../App";

export function ScopeControl({ brands }: { brands: BrandProfile[] }) {
  const lenses = ["Price", "Expansion", "Franchise", "Positioning", "Risk"];
  return (
    <aside className="scope-panel">
      <p className="side-title">Scope Control</p>
      <div className="filter-block">
        <strong>Brands</strong>
        <div className="chip-row">
          {brands.map((brand) => <span className="chip" key={brand.brand_id}>{brand.name}</span>)}
        </div>
      </div>
      <div className="filter-block">
        <strong>Analysis lenses</strong>
        <div className="chip-row">
          {lenses.map((lens) => <span className="chip" key={lens}>{lens}</span>)}
        </div>
      </div>
    </aside>
  );
}
```

```tsx
// BrandCards.tsx
import type { BrandProfile } from "../App";

export function BrandCards({ brands }: { brands: BrandProfile[] }) {
  return (
    <section className="panel">
      <h2>Brand Cards <small>structured profiles</small></h2>
      <div className="brand-grid">
        {brands.map((brand) => (
          <article className="brand-card" key={brand.brand_id}>
            <div className="brand-card-top">
              <strong>{brand.name}</strong>
              <span>{brand.category}</span>
            </div>
            <p>{brand.market_position}</p>
            <dl>
              <div><dt>Price</dt><dd>{brand.price_signal}</dd></div>
              <div><dt>Expansion</dt><dd>{brand.expansion_model}</dd></div>
              <div><dt>Risk</dt><dd>{brand.risk_signal}</dd></div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}
```

```tsx
// EvidenceTable.tsx
import type { EvidenceRow } from "../App";

export function EvidenceTable({ rows }: { rows: EvidenceRow[] }) {
  return (
    <section className="panel">
      <h2>Evidence Review <small>trust layer</small></h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr><th>Brand</th><th>Lens</th><th>Claim</th><th>Source</th><th>Status</th></tr>
          </thead>
          <tbody>
            {rows.slice(0, 12).map((row) => (
              <tr key={row.evidence_id}>
                <td>{row.brand_id}</td>
                <td>{row.lens}</td>
                <td>{row.claim}</td>
                <td><a href={row.source_url} target="_blank" rel="noreferrer">{row.source_type}</a></td>
                <td><span className="status-pill">{row.review_status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
```

```tsx
// ExportPanel.tsx
export function ExportPanel() {
  return (
    <section className="panel export-panel">
      <h2>Portfolio Exports</h2>
      <p>Markdown brief, evidence CSV, brand cards, workflow SOP, and interview talking points.</p>
      <div className="export-actions">
        <a href="/data/brief.md">Brief</a>
        <a href="/data/evidence.json">Evidence JSON</a>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Wire components in `App.tsx`**

Write:

```tsx
import brands from "./data/brands.json";
import evidence from "./data/evidence.json";
import briefSections from "./data/brief_sections.json";
import { BrandCards } from "./components/BrandCards";
import { EvidenceTable } from "./components/EvidenceTable";
import { ExecutiveBrief } from "./components/ExecutiveBrief";
import { ExportPanel } from "./components/ExportPanel";
import { PositioningMatrix } from "./components/PositioningMatrix";
import { ScopeControl } from "./components/ScopeControl";
import { WorkflowTrace } from "./components/WorkflowTrace";

export type BrandProfile = {
  brand_id: string;
  name: string;
  category: "coffee" | "tea";
  market_position: string;
  price_signal: string;
  expansion_model: string;
  franchise_model: string;
  brand_narrative: string;
  risk_signal: string;
  matrix_x: number;
  matrix_y: number;
  evidence_count: number;
  confidence: number;
};

export type EvidenceRow = {
  evidence_id: string;
  brand_id: string;
  lens: string;
  claim: string;
  source_title: string;
  source_url: string;
  source_type: string;
  source_date: string;
  excerpt: string;
  confidence: number;
  review_status: string;
  notes: string;
};

export type BriefSection = {
  section_id: string;
  title: string;
  summary: string;
  supporting_evidence_ids: string[];
  confidence: number;
};

const brandProfiles = brands as BrandProfile[];
const evidenceRows = evidence as EvidenceRow[];
const sections = briefSections as BriefSection[];

export default function App() {
  return (
    <main className="research-shell">
      <aside className="brand-rail">
        <div className="rail-logo">ML</div>
        <div className="rail-text">Market Intelligence Studio</div>
        <div className="rail-date">2026<br />Brief</div>
      </aside>
      <section className="research-board">
        <nav className="top-nav">
          <div className="brand-lockup"><strong>MarketLens AI</strong><span>Fresh Beverage Intelligence</span></div>
          <div className="nav-tabs"><span>Brief</span><span>Matrix</span><span>Evidence</span><span>Export</span></div>
        </nav>
        <div className="hero-grid">
          <ExecutiveBrief sections={sections} />
          <WorkflowTrace />
        </div>
        <div className="workbench-grid">
          <ScopeControl brands={brandProfiles} />
          <div className="main-stack">
            <div className="two-column">
              <PositioningMatrix brands={brandProfiles} />
              <section className="panel"><h2>Executive Takeaways</h2>{sections.map((section) => <article className="takeaway" key={section.section_id}><strong>{section.title}</strong><span>{section.summary}</span></article>)}</section>
            </div>
            <BrandCards brands={brandProfiles} />
            <div className="two-column">
              <EvidenceTable rows={evidenceRows} />
              <ExportPanel />
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 5: Extend CSS from visual mockup**

Port the approved `Premium Research Desk v2` styles into `web/src/styles.css`, using these required selectors:

```css
.workflow-number {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: #fbf8ee;
  background: #243842;
  box-shadow: 0 5px 12px rgba(36, 56, 66, 0.18);
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
}

.workflow-step:nth-child(2) .workflow-number {
  background: #2f7966;
}

.workflow-step:nth-child(3) .workflow-number {
  background: #84354b;
}

.workflow-step:nth-child(4) .workflow-number {
  background: #506b8a;
}
```

- [ ] **Step 6: Build frontend**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI\web
npm run build
```

Expected: TypeScript and Vite build succeed.

- [ ] **Step 7: Commit components**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI
git add web/src
git commit -m "feat: build premium research desk UI"
```

Expected: UI commit created.

## Task 8: Documentation Package

**Files:**
- Create: `README.md`
- Create: `docs/workflow_sop.md`
- Create: `docs/prompt_templates.md`
- Create: `docs/interview_talking_points.md`

- [ ] **Step 1: Write README**

README must include:

- one-sentence project pitch,
- why this maps to AI Agent / brand operations JD,
- architecture diagram in text,
- run instructions for Python and frontend,
- output artifacts,
- source discipline and no-private-data note,
- screenshots section with path `screenshots/marketlens-desktop.png`.

- [ ] **Step 2: Write workflow SOP**

`docs/workflow_sop.md` must include:

```markdown
# MarketLens AI Workflow SOP

## Goal

Turn public source material into a structured competitive intelligence brief.

## Steps

1. Define brand scope and analysis lenses.
2. Collect public sources with search and Firecrawl.
3. Extract claim-level evidence rows.
4. Validate evidence fields.
5. Score confidence based on source type, excerpt quality, URL, and review status.
6. Synthesize brand profiles and brief sections.
7. Review low-confidence rows manually.
8. Export Markdown brief and evidence table.

## Reuse For Another Industry

Replace brand list, collection queries, and static positioning assumptions. Keep the evidence schema, scoring rules, and export contract.
```

- [ ] **Step 3: Write prompt templates**

`docs/prompt_templates.md` must include prompts for:

- source extraction,
- evidence row review,
- brief synthesis,
- interview explanation.

Use this extraction prompt:

```markdown
You are extracting source-backed competitive intelligence evidence.

Return rows with:
- brand_id
- lens
- claim
- source_title
- source_url
- source_type
- source_date
- excerpt under 260 characters
- confidence from 0 to 1
- review_status
- notes

Only include claims directly supported by the source text. If the source is weak, set review_status to needs_review.
```

- [ ] **Step 4: Write interview talking points**

`docs/interview_talking_points.md` must include:

- 30-second project intro,
- 2-minute workflow explanation,
- JD alignment table,
- honest limitations,
- next iteration ideas.

- [ ] **Step 5: Commit documentation**

Run:

```powershell
git add README.md docs/workflow_sop.md docs/prompt_templates.md docs/interview_talking_points.md
git commit -m "docs: add marketlens portfolio documentation"
```

Expected: documentation commit created.

## Task 9: Verification And Screenshots

**Files:**
- Create: `screenshots/marketlens-desktop.png`
- Modify: `README.md`

- [ ] **Step 1: Run Python verification**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts\build_artifacts.py
```

Expected:

- all tests pass,
- artifacts rebuild without errors.

- [ ] **Step 2: Run frontend build**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI\web
npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Start local frontend server**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI\web
npm run dev -- --port 5173
```

Expected: app available at `http://127.0.0.1:5173`.

- [ ] **Step 4: Capture screenshot**

Use Playwright or browser screenshot to save:

```text
C:\Users\chenyizhe\Desktop\MarketLens_AI\screenshots\marketlens-desktop.png
```

The screenshot must show:

- left brand rail,
- executive brief,
- visible workflow numbers 1/2/3/4,
- positioning matrix,
- evidence section.

- [ ] **Step 5: Review UI for common visual failures**

Check manually:

- no overlapping text,
- workflow number badges visible,
- text inside cards does not overflow,
- no excessive pure white emptiness,
- no large dark block except narrow rail,
- matrix dots are visible,
- table links are readable.

- [ ] **Step 6: Update README screenshot reference**

Add:

```markdown
## Screenshot

![MarketLens AI desktop demo](screenshots/marketlens-desktop.png)
```

- [ ] **Step 7: Commit verification assets**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI
git add README.md screenshots data/processed web/src/data
git commit -m "chore: verify marketlens demo"
```

Expected: verification commit created.

## Task 10: Final Portfolio Review

**Files:**
- Read: `README.md`
- Read: `docs/workflow_sop.md`
- Read: `docs/interview_talking_points.md`
- Read: `data/processed/brief.md`
- Read: `data/evidence.csv`

- [ ] **Step 1: Check JD alignment**

Confirm README and interview notes explicitly mention:

- reusable AI-assisted workflow,
- structured information summarization,
- evidence confidence scoring,
- basic visualization,
- brief and CSV export,
- SOP and prompt templates.

- [ ] **Step 2: Check honesty and defensibility**

Confirm no file claims:

- formal internship experience,
- internal company data,
- investment recommendation,
- fully autonomous production system,
- guaranteed business outcome.

- [ ] **Step 3: Check data completeness**

Confirm:

- 7 brand profiles exist,
- at least 28 evidence rows exist,
- every evidence row has source URL,
- every brand has at least 4 evidence rows,
- every brief section has supporting evidence IDs.

- [ ] **Step 4: Run final command set**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python scripts\build_artifacts.py
cd web
npm run build
```

Expected:

- pytest passes,
- artifacts rebuild,
- frontend builds.

- [ ] **Step 5: Commit final polish**

Run:

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI
git status --short
git add .
git commit -m "docs: finalize marketlens portfolio package"
```

Expected: only intentional project files committed.
