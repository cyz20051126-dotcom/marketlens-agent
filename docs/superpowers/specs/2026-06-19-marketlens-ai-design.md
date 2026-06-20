# MarketLens AI Design Spec

Status: Draft for user review
Date: 2026-06-19

## 1. Product Positioning

MarketLens AI is a portfolio-grade competitive intelligence workflow for the fresh beverage market, focused on Chinese tea and coffee chains.

The project should not look like a generic AI summarizer or a job-search toy. It should demonstrate a reusable AI-assisted research workflow:

1. collect public source material,
2. extract structured claims,
3. score evidence confidence,
4. synthesize a competitive brief,
5. show the results in a polished research workspace,
6. export a Markdown brief and evidence table.

The first demo industry is fresh beverage chains, comparing coffee brands and tea brands across pricing, expansion, franchise model, brand positioning, and risk signals.

Target brands:

- Luckin Coffee
- Cotti Coffee
- Starbucks China
- Mixue Bingcheng
- CHAGEE
- Guming
- ChaPanda

## 2. JD Alignment

### Shanghai Xingzhi Qixin / Tenth Global AI Agent Intern

Relevant JD signals:

- reusable AI Agent and automation workflow,
- real business scenarios,
- AI knowledge base and standardized process,
- ability to explain the full process from problem discovery to solution delivery,
- heavy use of AI tools and prompt/workflow design.

MarketLens AI will match this by exposing a clear workflow:

- Problem: public market information is scattered, repetitive to review, and hard to trace back to evidence.
- Solution: a reusable source-to-brief workflow with search, extraction, scoring, synthesis, and export stages.
- Deliverables: web demo, evidence table, research brief, workflow SOP, prompt templates, and README.
- Reusability: the same schema can be reused for another sector by changing brand list, source list, and analysis lenses.

### GaoYi Asset Brand Operations Support Intern

Relevant JD signals:

- AI prompt optimization,
- structured information summarization,
- basic visualization,
- AI Agent / vibe coding tools,
- data tracking,
- material analysis,
- office workflow automation.

MarketLens AI will match this by producing:

- structured brand profiles,
- positioning matrix and comparison cards,
- evidence review table,
- Markdown research brief,
- reusable prompts and SOP for AI-assisted material analysis.

## 3. MVP Scope

The MVP is a complete portfolio package, not only a UI.

### In Scope

1. Premium research desk web demo
   - Brief overview
   - Positioning matrix
   - Brand cards
   - Evidence table
   - Workflow trace
   - Export section

2. Realistic sample dataset
   - 7 brands
   - 20 to 30 evidence rows
   - Source title, URL, source type, extracted claim, related brand, related lens, confidence, review status

3. AI-assisted research pipeline
   - Source collection from public pages, with cached sample data for repeatable demo runs
   - Structured extraction schema
   - Evidence scoring rules
   - Brief synthesis
   - Markdown and CSV export

4. Documentation
   - README
   - Workflow SOP
   - Prompt templates
   - Example output brief
   - Interview talking points

5. Verification
   - Data validation tests
   - Export tests
   - UI smoke test / screenshot check

### Out of Scope For V1

- User login
- Cloud database
- Fully autonomous broad web crawling
- Real-time monitoring
- Investment recommendation
- Fabricated private data
- Auto-apply or resume matching
- Heavy multi-agent orchestration that cannot be explained simply in interview

## 4. Visual Direction

Design direction: Premium Research Desk.

The interface should feel like an editorial consulting workspace, not a white SaaS admin panel and not a dark AI command center.

Visual constraints:

- background: mist green-gray, not pure white,
- content cards: ivory paper-like cards,
- accents: wine red, deep green, muted indigo,
- structure: left narrow brand rail, top executive brief, right workflow trace, main matrix and evidence panels,
- typography: refined editorial heading, readable compact body text,
- avoid large dark blocks,
- avoid purple/blue AI gradients,
- avoid generic card-heavy landing-page composition,
- workflow number badges must be independent components with explicit foreground/background colors.

The product should be screenshot-worthy for GitHub and resume use.

## 5. Information Architecture

### Page 1: Brief

Purpose: show the core business thesis and project credibility within the first screen.

Content:

- product name and demo scope,
- executive thesis,
- coffee growth logic,
- tea growth logic,
- workflow trace,
- research signal counters.

### Page 2: Matrix

Purpose: visually compare the 7 brands.

Content:

- positioning matrix,
- axes:
  - price pressure vs premium narrative,
  - coffee density logic vs tea franchise logic,
- brand dots,
- legend,
- short interpretation notes.

### Page 3: Brand Cards

Purpose: make each brand inspectable.

Each card contains:

- brand name,
- category,
- pricing signal,
- expansion model,
- positioning summary,
- risk signal,
- evidence count,
- confidence status.

### Page 4: Evidence

Purpose: prove source discipline.

Columns:

- brand,
- analysis lens,
- claim,
- source title,
- source type,
- URL,
- confidence,
- review status,
- note.

### Page 5: Workflow / SOP

Purpose: show JD-relevant process thinking.

Content:

- Search
- Extract
- Normalize
- Score
- Synthesize
- Export
- Reuse guidance for another industry

### Page 6: Export

Purpose: create portfolio artifacts.

Exports:

- `outputs/marketlens_brief.md`
- `outputs/marketlens_evidence.csv`
- `outputs/marketlens_brand_cards.json`

## 6. Architecture

Use a hybrid structure:

- Python pipeline for source processing and artifact generation.
- React/Vite frontend for a polished visual demo.
- Static JSON/CSV artifacts as the contract between pipeline and UI.

This is more suitable than a pure Streamlit app because the portfolio needs strong visual polish. Streamlit can be used later for quick internal tools, but the primary demo should be a custom frontend.

Suggested structure:

```text
marketlens-ai/
  README.md
  docs/
    workflow_sop.md
    prompt_templates.md
    interview_talking_points.md
  data/
    raw/
    processed/
    sources.yaml
    evidence.csv
    brands.json
    brief.md
  src/
    marketlens/
      __init__.py
      schemas.py
      collect.py
      extract.py
      score.py
      synthesize.py
      export.py
  tests/
    test_schemas.py
    test_exports.py
    test_scoring.py
  web/
    package.json
    src/
      App.tsx
      data/
      components/
      styles/
```

## 7. Data Model

### Brand Profile

Fields:

- `brand_id`
- `name`
- `category`
- `market_position`
- `price_signal`
- `expansion_model`
- `franchise_model`
- `brand_narrative`
- `risk_signal`
- `matrix_x`
- `matrix_y`
- `evidence_count`
- `confidence`

### Evidence Row

Fields:

- `evidence_id`
- `brand_id`
- `lens`
- `claim`
- `source_title`
- `source_url`
- `source_type`
- `source_date`
- `excerpt`
- `confidence`
- `review_status`
- `notes`

### Brief Section

Fields:

- `section_id`
- `title`
- `summary`
- `supporting_evidence_ids`
- `confidence`

## 8. Pipeline Data Flow

```text
sources.yaml
  -> collect public material
  -> raw markdown/text cache
  -> extract evidence rows
  -> validate evidence schema
  -> score confidence
  -> generate brand profiles
  -> synthesize brief
  -> export JSON/CSV/Markdown
  -> React demo reads exported artifacts
```

V1 can include manually reviewed sample evidence rows. This is acceptable because the point is to demonstrate an AI-assisted workflow with human review, not to pretend that every step is fully autonomous.

## 9. Error Handling

### Source Collection

- If a URL fails, keep a failed status and continue.
- If Firecrawl or network is unavailable, use cached raw sources.
- Do not block the demo on live scraping.

### Extraction

- Reject evidence rows missing brand, claim, source URL, or lens.
- Mark low-confidence rows as `needs_review`.
- Never allow unsourced claims into the final brief.

### Export

- Fail clearly if required output folders are missing.
- Validate CSV and JSON before writing.
- Include export timestamp and dataset version.

### UI

- Show empty states if data is missing.
- Show source confidence and review status visibly.
- Avoid hiding methodology behind decorative UI.

## 10. Testing And Verification

Required checks before calling the project complete:

1. Python tests
   - schema validation,
   - confidence scoring,
   - export generation.

2. Data checks
   - every brief claim links to at least one evidence row,
   - every evidence row has source URL and source type,
   - all 7 target brands appear in brand profiles.

3. UI checks
   - page loads locally,
   - no overlapping text,
   - workflow badges visible,
   - desktop screenshot looks professional,
   - mobile layout remains readable.

4. Portfolio checks
   - README explains JD alignment,
   - workflow SOP is understandable,
   - brief and evidence CSV exist,
   - no false claims about internship or internal data.

## 11. Resume Story

Suggested resume bullet:

Designed and implemented MarketLens AI, an AI-assisted competitive intelligence workflow for fresh beverage brands. Built a source-to-brief pipeline covering public source collection, structured evidence extraction, confidence scoring, brand comparison, positioning visualization, and Markdown/CSV export; produced a polished research workspace, evidence table, and reusable workflow SOP to improve public material analysis and business brief drafting efficiency.

Chinese version:

设计并实现 MarketLens AI 竞品情报工作流，围绕新茶饮/连锁咖啡行业搭建“公开资料收集-结构化证据抽取-置信度评分-品牌对比-研究简报导出”的 AI 辅助分析流程；输出品牌定位矩阵、证据表和可复用研究 SOP，用于提升公开资料整理与商业分析初稿产出效率。
## 12. Success Criteria

The project is successful when:

- it can be run locally from README instructions,
- the UI looks like a polished research product,
- it includes real source-backed sample data,
- it generates a Markdown brief and evidence CSV,
- the workflow can be explained in 2 minutes,
- the resume bullet honestly matches what the project does,
- the project clearly maps to AI Agent / AI operations / brand operations JD requirements.

