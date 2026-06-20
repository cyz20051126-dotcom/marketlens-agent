# MarketLens Agent v2 Design Spec

Status: ready for user review
Date: 2026-06-20

> **v2.1 Update (2026-06-20)**: This document is the original v2 design. The v2.1 implementation has these changes:
> - **Search**: Firecrawl → DuckDuckGo HTML (free, no API key; see `plans/2026-06-20-marketlens-real-llm-websearch.md`)
> - **LLM**: Triage/Planner/Extractor/Writer all call DeepSeek (original design used rule-based fast paths)
> - **FinanceLens**: spec §7.1 fully completed (unit economics / expansion model / DCF assumptions incl. tax rate + reinvestment rate / 3 sensitivity matrices)
> - All references to Firecrawl / FirecrawlSearchTool in this document have been replaced by WebSearchTool + DuckDuckGo in the actual implementation.

## 1. One-Line Positioning

MarketLens Agent is a self-built, lightweight multi-agent research system for Chinese fresh beverage brands. It combines Agentic RAG, web research, evidence management, and finance-oriented analysis: it takes a research question via chat, checks whether the local evidence database is sufficient, and when it is not, automatically plans search tasks, calls tools to fetch public material, extracts structured evidence, verifies sources, then turns operating evidence into per-store / franchise / DCF assumptions and outputs a cited research answer or report.

## 2. Why v1 Is Not Enough

The existing MarketLens v1 is useful but too close to a source-to-brief workflow:

1. It has evidence rows and a polished dashboard.
2. It can generate a brief from structured data.
3. It does not yet show an autonomous agent loop.
4. It does not yet expose planning, tool calls, memory, handoffs, or run traces.
5. It does not yet include a real AI chat entry point over the evidence database.
6. It does not yet turn business evidence into finance-style assumptions.

The v2 goal is to make the project a real agent system with runtime, tool calling, evidence flow, and observability, rather than a source-to-brief report generator.

## 3. Research Findings

### 3.2 Agent Architecture References

| Reference | Useful pattern | How we adapt it |
| --- | --- | --- |
| HelloAgents Chapter 14 | TODO Planner, Task Summarizer, Report Writer, SearchTool, NoteTool | Use Planner/Searcher/Extractor/Verifier/FinanceLens/Writer agents. |
| LangChain Deep Agents | Decompose research questions, delegate to sub-agents, synthesize citations | Keep chat as entry; let orchestrator delegate specialized tasks. |
| GPT Researcher | Planner + execution agents + publisher | Add research plan, crawl/search execution, source tracking, final report. |
| OpenAI Agents SDK | Agent definitions, tools, handoffs, guardrails, state, observability, evals | Recreate the core concepts in a small custom runtime to keep the dependency surface minimal and the code readable. |
| LangGraph | Durable execution, streaming, human-in-the-loop, persistence | Borrow state/trace ideas without requiring LangGraph in v2 MVP. |
| IBM Agentic RAG | RAG plus agents retrieves from multiple sources and handles complex workflows | Local Evidence DB is the first source; web search is the escalation path. |

Primary links:

- https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter14/Chapter14-Automated-Deep-Research-Agent.md
- https://docs.langchain.com/oss/python/deepagents/deep-research
- https://github.com/assafelovic/gpt-researcher
- https://developers.openai.com/api/docs/guides/agents
- https://docs.langchain.com/oss/python/langgraph/overview
- https://www.ibm.com/think/topics/agentic-rag

### 3.3 Finance Lens Evidence

The fresh beverage sector has public operating metrics that can support a finance-oriented research layer:

| Brand/source | Relevant public metric | Finance use |
| --- | --- | --- |
| Luckin Coffee 2025 results | Store count, net revenue, same-store sales growth, store-level operating margin, partnership store revenue | Revenue drivers, store-level margin, operating leverage, price war impact. |
| Mixue 2025 interim reporting | Global store count, franchise openings/closures, revenue, net profit, product/equipment sales margin, franchise service margin | Franchise model, supply chain margin, store expansion runway. |
| CHAGEE SEC filing | Teahouse count, GMV, DCF discount rate updates, peer P/E movement | DCF assumptions, GMV/store, growth outlook, valuation sensitivity. |
| Guming IPO reporting | GMV, store count, revenue, adjusted profit, IPO proceeds use | Expansion model, IT/supply-chain investment, franchise support. |

Primary links:

- https://www.globenewswire.com/news-release/2026/02/26/3245426/0/en/luckin-coffee-announces-fourth-quarter-and-fiscal-year-2025-financial-results.html
- https://stcn.com/article/detail/3281427.html
- https://investor.chagee.com/node/6811/html
- https://m.bjnews.com.cn/detail/1738747334168064.html

## 4. Product Shape

The first screen should be an AI research workstation, not a landing page and not only a static dashboard.

Core layout:

1. Left panel: AI Research Chat
2. Center panel: Agent Todo Board and Trace Timeline
3. Right panel: Evidence DB, citations, and Finance Lens
4. Bottom or secondary tab: generated report and export artifacts

The user can ask:

- "霸王茶姬扩张是不是过快？"
- "瑞幸价格战对利润率和估值有什么影响？"
- "蜜雪冰城的加盟模型和古茗有什么区别？"
- "帮我用 DCF 假设框架分析 CHAGEE 的增长风险。"

The system answers with:

1. direct answer,
2. evidence IDs,
3. whether the answer came from local DB or new web research,
4. finance assumptions if relevant,
5. uncertainty and source-quality notes.

## 5. Functional Scope

### 5.1 In Scope

1. Custom lightweight agent runtime:
   - `BaseAgent`
   - `AgentMessage`
   - `Tool`
   - `ToolRegistry`
   - `ToolResponse`
   - `AgentRun`
   - `SessionStore`
   - `TraceLogger`
   - `TodoBoard`

2. LLM provider layer:
   - DeepSeek-compatible OpenAI-style client
   - deterministic fallback mode for tests and demo
   - structured JSON output parsing
   - retry and validation boundary

3. Agent set:
   - `TriageAgent`: decides local answer vs new research vs finance analysis
   - `PlannerAgent`: decomposes research question into focused tasks
   - `SearchAgent`: calls Firecrawl/search and returns source candidates
   - `EvidenceExtractorAgent`: extracts evidence rows from source text
   - `VerifierAgent`: checks duplicate, weak, conflicting, or stale evidence
   - `FinanceLensAgent`: maps evidence to operating and valuation assumptions
   - `WriterAgent`: writes answers and reports with evidence IDs

4. Tools:
   - `EvidenceSearchTool`: query local evidence
   - `FirecrawlSearchTool`: search web when evidence is insufficient
   - `SourceReadTool`: read cached or scraped source text
   - `EvidenceStoreTool`: append/merge validated evidence
   - `FinanceModelTool`: compute unit economics and DCF-style sensitivity
   - `BriefExportTool`: export Markdown/JSON/CSV

5. Frontend:
   - chat input and answer panel
   - live run timeline
   - todo board
   - tool call cards
   - evidence table with source links
   - finance lens table/chart
   - final report tab

6. Deliverables:
   - README
   - architecture diagram
   - demo script

### 5.2 Out of Scope For v2 MVP

1. No investment advice or buy/sell recommendation.
2. No fake private data.
3. No full production vector database requirement.
4. No login or deployment requirement.
5. No automatic Gmail applications in this implementation cycle.
6. No claim that the system is a complete financial valuation platform.
7. No copied HelloAgents framework code; borrow ideas, implement a small explainable runtime.

## 6. Agentic RAG Behavior

The system should not answer every question by immediately searching the web.

Expected decision flow:

```text
User question
  -> TriageAgent
  -> classify intent:
       local_evidence_qa
       new_research_needed
       finance_analysis_needed
       report_generation_needed
  -> if local evidence is enough:
       EvidenceSearchTool -> WriterAgent answer
  -> if evidence is insufficient or stale:
       PlannerAgent -> SearchAgent -> EvidenceExtractorAgent -> VerifierAgent
       -> EvidenceStoreTool -> WriterAgent answer
  -> if finance is involved:
       EvidenceSearchTool + FinanceLensAgent + FinanceModelTool
       -> WriterAgent answer with assumptions and caveats
```

This makes the chat interface a visible part of the Agent, while the deeper Agent behavior remains planning, tool use, evidence updates, and traceable synthesis.

## 7. FinanceLensAgent Design

FinanceLensAgent converts brand evidence into analysis variables. It should be honest and educational, not pretend to be a professional valuation model.

### 7.1 Finance Tasks

1. Unit economics:
   - estimated GMV per store
   - revenue per store
   - store-level margin
   - franchise service margin
   - product/equipment sales margin

2. Expansion model:
   - store count growth
   - franchise openings and closures
   - overseas vs domestic expansion
   - same-store growth where available

3. DCF-style assumptions:
   - revenue growth
   - operating margin
   - tax rate
   - reinvestment/capital expenditure proxy
   - discount rate
   - terminal growth

4. Sensitivity analysis:
   - growth rate vs margin
   - store count vs GMV per store
   - discount rate vs terminal growth

### 7.2 Finance Outputs

Each finance answer must include:

1. assumption table,
2. linked evidence IDs,
3. calculation formula,
4. sensitivity result,
5. caveat that outputs are educational analysis, not investment advice.

## 8. Data Model Additions

### 8.1 AgentRun

Fields:

- `run_id`
- `session_id`
- `user_query`
- `intent`
- `started_at`
- `completed_at`
- `status`
- `agents_invoked`
- `tool_calls`
- `answer`
- `supporting_evidence_ids`
- `error_message`

### 8.2 TraceEvent

Fields:

- `event_id`
- `run_id`
- `timestamp`
- `agent_name`
- `event_type`
- `summary`
- `input_preview`
- `output_preview`
- `tool_name`
- `tool_status`
- `latency_ms`

### 8.3 TodoItem

Fields:

- `todo_id`
- `run_id`
- `title`
- `intent`
- `query`
- `status`
- `assigned_agent`
- `supporting_source_urls`
- `result_summary`

### 8.4 FinanceAssumption

Fields:

- `assumption_id`
- `brand_id`
- `metric_name`
- `metric_value`
- `unit`
- `period`
- `formula`
- `source_evidence_ids`
- `confidence`
- `notes`

### 8.5 FinanceScenario

Fields:

- `scenario_id`
- `brand_id`
- `scenario_name`
- `revenue_growth`
- `operating_margin`
- `discount_rate`
- `terminal_growth`
- `sensitivity_axis_x`
- `sensitivity_axis_y`
- `result_value`
- `notes`

## 9. Frontend Experience

### 9.1 Default View

The default screen should immediately look like an AI research product:

1. Chat input at top-left or left rail.
2. Recent research questions.
3. Current answer with citations.
4. Agent run timeline in the center.
5. Evidence and finance tabs on the right.

### 9.2 Trace Timeline

Show user-facing summaries, not hidden chain of thought:

- "TriageAgent classified the query as finance_analysis_needed."
- "EvidenceSearchTool found 6 local evidence rows."
- "PlannerAgent created 4 research tasks."
- "FirecrawlSearchTool returned 5 source candidates."
- "VerifierAgent rejected 2 weak rows and approved 4 evidence rows."
- "FinanceLensAgent created 7 assumptions and 2 sensitivity tables."

### 9.3 Finance Lens Tab

Display:

1. operating metrics table,
2. assumption cards,
3. sensitivity matrix,
4. source evidence IDs,
5. caveats.

### 9.4 Evidence DB Tab

Display:

1. searchable evidence table,
2. source URL,
3. confidence,
4. review status,
5. freshness/staleness label,
6. whether the evidence was manually seeded or agent-extracted.

## 10. Error Handling And Safety

### 10.1 Tool Failures

- Failed tool calls return `ToolResponse(success=False, error=...)`.
- Search failure falls back to local evidence.
- Source parsing failure creates a trace event and does not block the whole run.

### 10.2 LLM Failures

- Invalid JSON is retried once with a repair prompt.
- If repair fails, fall back to deterministic extraction for demo data.
- Never write unsourced claims into the final answer.

### 10.3 Evidence Quality

- New evidence must include source URL, source title, date if available, extracted claim, and confidence.
- Weak or promotional sources are marked `needs_review`.
- Conflicting evidence is surfaced rather than silently merged.

### 10.4 Finance Safety

- Do not output buy/sell/hold recommendations.
- Use "DCF-style assumption analysis" instead of claiming full formal valuation.
- Always show assumptions and evidence.
- Always include uncertainty.

## 11. Testing And Verification

### 11.1 Runtime Tests

- Tool registry can register and call tools.
- ToolResponse serializes success and failure.
- SessionStore persists an AgentRun.
- TraceLogger records ordered events.

### 11.2 Agent Tests

- TriageAgent routes local evidence questions correctly.
- PlannerAgent creates 3-5 tasks.
- EvidenceExtractorAgent returns schema-valid rows.
- VerifierAgent rejects missing-source rows.
- FinanceLensAgent generates assumptions with evidence IDs.
- WriterAgent refuses unsupported claims.

### 11.3 UI Tests

- Chat view renders.
- Todo board renders current run.
- Tool call timeline renders non-empty events.
- Evidence tab links to source URLs.
- Finance tab shows assumptions and sensitivity output.
- Desktop and mobile layouts do not overlap text.

### 11.4 Portfolio Verification

- README explains the Agent architecture.
- Project can run without DeepSeek key using fallback mode.
- With DeepSeek key, the LLM path is available.
- Demo script has 3 questions:
  - local evidence Q&A,
  - new research escalation,
  - finance analysis.
- README matches real implemented behavior.

## 12. Implementation Boundaries

v2 should be one implementation plan, but it must be split into clear milestones:

1. Agent runtime and data model.
2. Local Evidence Q&A and chat entry.
3. DeepSeek provider and fallback mode.
4. Research workflow with Firecrawl tool adapter.
5. FinanceLensAgent and model outputs.
6. Frontend Agent Console.
7. Documentation, screenshots, tests.

Do not start with UI polish. The first milestone must make the Agent loop and trace data real.

## 13. Success Criteria

The project is successful when:

1. The default page clearly looks like an Agent research console.
2. A user can ask questions through chat.
3. The system can answer from local evidence with evidence IDs.
4. The system can trigger a research workflow when evidence is insufficient.
5. The workflow records todo items, tool calls, and trace events.
6. FinanceLensAgent produces assumption tables linked to evidence.
7. The final report and answers include citations.
8. Tests prove the runtime, tools, agents, and UI are not fake placeholders.
9. The codebase can honestly demonstrate multi-agent research, tool calling, memory/trace, evidence extraction, and finance analysis.

