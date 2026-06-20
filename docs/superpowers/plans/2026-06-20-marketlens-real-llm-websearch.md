# MarketLens Agent v2.1 修复计划：纯 LLM 驱动 + DuckDuckGo 真搜索 + 多智能体链

状态：待用户复核（第二轮）
日期：2026-06-20
前置文档：`docs/superpowers/specs/2026-06-20-marketlens-agent-v2-design.zh-CN.md`

## 0. 假设声明（动手前必须确认）

```
ASSUMPTIONS I'M MAKING:
1. 你有可用的 DeepSeek API key，愿意填到 .env（不进 git）
2. 搜索用 DuckDuckGo HTML 接口，完全免费、无 key、无额度限制
3. 这轮目标是让"简历写的 agent 协作链"能真跑，纯 LLM 驱动（Triage/Planner/Extractor/Writer 全调 DeepSeek）
4. 演示场景是本地跑 uvicorn + vite，不是部署到云
5. 现有 evidence.csv（28 条 reviewed）和 finance_metrics.csv（10 条）不动，作为种子数据
6. 求职投递材料（deliverables/jobs、简历多版本 docx）这轮不动，下轮再拆
7. Verifier 用纯规则不调 LLM（检查 URL/重复/来源类型/置信度），因为这些都是是/否判断，用 LLM 又慢又浪费
→ 如果哪条不对，停下来纠正我。
```

## 1. 这轮范围

### 1.1 M1 必做（让简历能诚实讲）

| # | 修复项 | 现状 | 目标 |
|---|--------|------|------|
| M1-1 | LLM client 真接入 | `llm.py` 写了但 orchestrator/agents 没 import | Triage / Planner / Extractor / Writer 四个 agent 纯 LLM 驱动，有 key 走 DeepSeek，没 key 走增强 fallback |
| M1-2 | DuckDuckGo 真搜索 | `FirecrawlSearchTool` 只写 `prepared` JSON | 改名 `WebSearchTool`，调 DuckDuckGo HTML 接口，返回真实搜索结果，失败时降级到本地 sources.json 模糊匹配 |
| M1-3 | 多智能体链接齐 | Search/Extractor/Verifier/Store 是死代码 | orchestrator 在本地证据不足时走完整链：Planner → SearchAgent → EvidenceExtractorAgent → VerifierAgent → EvidenceStoreTool |
| M1-4 | Writer 用 LLM 综合 | 字符串模板拼接 | Writer 调 LLM 生成带引用的中文研究回答，强制要求输出包含 evidence ID + 不确定性段落 |
| M1-5 | 测试覆盖新链路 | 现有 10 个测试文件 | 新增 LLM mock 测试、DuckDuckGo mock 测试、完整链路集成测试 |

### 1.2 M2 下轮做（这轮不动）

- FinanceLens 补单店经济、税率、再投资率、门店数×单店 GMV 敏感性矩阵（spec §7.1 剩下 3/4）
- 前端从 demo json fallback 改为真 trace 驱动展示
- 把 `deliverables/jobs` 和多版本简历拆成独立子项目
- README / 简历 / 面试讲稿同步更新

### 1.3 这轮不做

- 不接向量数据库（spec §5.2 已排除）
- 不做登录系统
- 不做投资建议输出
- 不重构现有 evidence schema
- 不动前端样式
- 不用 LangChain（自研 runtime 是 deliberate choice，spec §3.2 已论证）

## 2. 关键设计决策

### 2.1 纯 LLM 驱动（用户决策）

**决策**：Triage / Planner / EvidenceExtractor / Writer 四个 agent 全部调 LLM，不用规则路由作为快速路径。

**理由**：DeepSeek 便宜，"纯 LLM 驱动"在简历上比"混合策略"更有说服力。

**代价与应对**：
- Triage 每次问答 +500ms 延迟 → 前端加 loading 状态（M2 处理）
- 测试不能依赖真 LLM → 用 `MockLLMClient`（返回预设内容），所有测试离线跑
- 没 key 时演示会穿帮 → `FallbackLLMClient` 升级为"基于 evidence 的规则化中文模板生成"，保证无 key 也能演示

**Verifier 例外**：Verifier 不调 LLM。它做的事是检查 URL 是不是 http 链接、证据有没有重复、来源类型在不在白名单、置信度够不够——全是是/否判断，if-else 写死，用 LLM 又慢又浪费钱。

### 2.2 DuckDuckGo 搜索接入（替代 Firecrawl）

**问题**：Firecrawl 免费额度 500 credits/月，演示十几轮就用完。用户不想花这个钱。

**决策**：改用 DuckDuckGo HTML 搜索接口（`https://html.duckduckgo.com/html/?q=...`），完全免费、无 key、无额度限制。Python 标准库 `urllib.request` 就能调，不引入新依赖。

**实现**：
- `FirecrawlSearchTool` 改名 `WebSearchTool`，内部调 DuckDuckGo
- 解析返回的 HTML，抽取结果标题、URL、snippet
- 失败时（网络不通/DuckDuckGo 限流）降级到 `data/sources.json` 模糊匹配，trace 标记 `degraded_fallback`

**简历表述调整**：从"接入 Firecrawl"改为"接入 DuckDuckGo 网页搜索"。诚实优先。

**保留 Firecrawl 适配器的选项**：如果以后想加 Firecrawl 作为可选后端，`WebSearchTool` 设计成可扩展接口，但 M1 不做。

### 2.3 什么时候触发搜索（用户反馈后简化）

**决策**：只有当本地证据少于 2 条时才触发 DuckDuckGo 搜索。

**为什么**：
- 你问"瑞幸价格战对利润率影响" → 本地有 4 条瑞幸证据，够答了，不搜
- 你问"霸王茶姬最新上市进展" → 如果本地证据够，直接答；不够才搜
- 这样省搜索调用（省钱），演示更聚焦

**spec §6 的意图**：先查本地，不够再补。这个决策跟 spec 一致，只是把触发条件收紧了。

### 2.4 EvidenceExtractor 用 LLM 抽证据

**问题**：DuckDuckGo 返回的是网页标题 + URL + snippet，不是结构化证据。需要 LLM 把 snippet 抽成 `{claim, excerpt, source_type, confidence}`。

**决策**：Extractor 用 LLM，prompt 要求返回 JSON 数组。LLM 返回非法 JSON 时重试一次（repair prompt），再失败则降级为"直接用 snippet 作为 claim + excerpt，confidence=0.5, review_status=needs_review"。

### 2.5 对照 agent-skills 编排模式（新增）

参考：[addyosmani/agent-skills `references/orchestration-patterns.md`](https://github.com/addyosmani/agent-skills/blob/main/references/orchestration-patterns.md)

用 agent-skills 的 4 个反模式对照我们的 orchestrator 设计，结论：**3 个符合，1 个边界案例需要加固**。

| 反模式 | 我们的情况 | 结论 |
|--------|-----------|------|
| A. 路由 Persona（LLM 只做路由无领域价值） | TriageAgent 如果只返回 intent 就是路由 persona | ⚠ **加固**：Triage 必须同时返回 intent + query 改写，让它有领域输出 |
| B. Persona 调用 Persona | agent 之间不互相调用，全是 orchestrator（Python 代码）调度 | ✓ 符合 |
| C. 改写型顺序编排器（LLM 编排器每步改写摘要） | orchestrator 是 Python 代码，传原始 dataclass，不做 LLM 改写 | ✓ 符合（关键区别：代码编排 ≠ LLM 编排） |
| D. 深层 Persona 树 | 编排深度 = 1（orchestrator → agents，无中间层） | ✓ 符合 |

**额外吸收的洞察（模式 5：research isolation）**：搜索链中间产物（原始 HTML / 长 snippet）不应进 Writer 上下文。Extractor 只返回结构化 JSON，Verifier 只返回 review_status + 通过的证据行。Writer 只接收已通过 Verifier 的结构化证据，不接收搜索原始结果。

**为什么不直接用 agent-skills 的 skill 文件**：那 24 个 skill 面向"人用 AI 写代码"（spec/plan/build/test/review/ship），场景不同。我们是"系统自动研究"，orchestrator 是必要的。但编排原则（深度 ≤1、agent 不互调、research isolation）我们遵守。

## 3. 任务拆解（M1）

每个任务都有验收标准，不达标不算完。

### Task 1：增强 LLM client 层
**文件**：`src/marketlens/agent/llm.py`（改）、`tests/test_agent_llm.py`（新）

改动：
- `DeepSeekLLMClient` 加 `temperature` 和 `max_tokens` 参数
- 新增 `LLMClient` Protocol，让所有 client 实现统一接口
- `FallbackLLMClient.complete()` 升级：接受 `context` 参数（evidence 列表 + query），基于 evidence 生成结构化中文回答，而不是原样返回
- 新增 `MockLLMClient`（测试用，返回预设内容）

验收：
- `test_deepseek_client_calls_api_when_key_present`（mock urllib）通过
- `test_fallback_client_generates_structured_answer_from_evidence` 通过
- `test_mock_client_returns_preset_content` 通过
- 现有 10 个测试文件全绿

### Task 2：DuckDuckGo 真接 HTML 搜索
**文件**：`src/marketlens/agent/tools.py`（改）、`tests/test_agent_tools.py`（改）

改动：
- `FirecrawlSearchTool` 改名 `WebSearchTool`
- `run()` 调 `GET https://html.duckduckgo.com/html/?q={query}`，解析 HTML 抽取标题/URL/snippet
- 失败时降级到 `data/sources.json` 模糊匹配，trace 标记 `degraded_fallback`
- `.env.example` 删掉 `FIRECRAWL_*`，不需要搜索 key

验收：
- `test_web_search_returns_real_results_when_mocked` 通过（mock urllib 返回 DuckDuckGo HTML）
- `test_web_search_falls_back_to_sources_json_on_failure` 通过
- `test_web_search_marks_degraded_status_in_trace` 通过
- 现有测试全绿

### Task 3：四个 agent 纯 LLM 驱动
**文件**：`src/marketlens/agent/agents.py`（改）、`tests/test_agent_agents.py`（改）

改动：
- `TriageAgent.__init__(self, llm_client)`：必须接 LLM，prompt 让 LLM 同时返回 intent + query 改写（避免成为纯路由 persona，见 §2.5）
- `PlannerAgent.__init__(self, llm_client)`：必须接 LLM，prompt 让 LLM 拆任务
- `EvidenceExtractorAgent.__init__(self, llm_client)`：必须接 LLM，prompt 要求返回 JSON 数组；**只返回结构化 JSON，原始 snippet/markdown 不进返回值**（research isolation，见 §2.5）
- `WriterAgent.__init__(self, llm_client)`：必须接 LLM，prompt 强制要求 evidence ID 引用 + 不确定性段落；输入只接收已通过 Verifier 的结构化证据，不接收搜索原始结果
- `VerifierAgent` 不变（纯规则）
- `FinanceLensAgent` 不变（这轮不动）

验收：
- `test_triage_calls_llm_and_returns_intent_plus_rewritten_query` 通过（mock LLM 验证被调用、返回 intent + query 改写都被使用）
- `test_planner_calls_llm_to_generate_tasks` 通过
- `test_extractor_returns_only_structured_json_no_raw_snippet` 通过
- `test_writer_generates_chinese_answer_with_evidence_ids` 通过
- `test_writer_includes_uncertainty_paragraph` 通过
- 现有测试全绿

### Task 4：orchestrator 接齐多智能体链
**文件**：`src/marketlens/agent/orchestrator.py`（改）、`tests/test_agent_orchestrator.py`（改）

改动：
- `__init__` 接受 `llm_client` 参数，构造时注入给需要的 agent
- `answer()` 主流程改为：
  ```
  Triage(LLM) → EvidenceSearch
    if 证据 < 2:
      Planner(LLM) → SearchAgent(DuckDuckGo) → Extractor(LLM) → Verifier(规则) → EvidenceStore
      合并新证据到 evidence 列表
    if finance_analysis:
      FinanceLens
  Writer(LLM) → 输出
  ```
- 每一步都记 trace，latency_ms 用真实计时
- todo board 在每个 agent 完成时更新对应 item 状态

验收：
- `test_orchestrator_local_evidence_path_skips_search` 通过（本地证据充足时不调搜索）
- `test_orchestrator_research_path_invokes_full_chain` 通过（mock LLM + mock 搜索，验证 Search/Extractor/Verifier 都被调用）
- `test_orchestrator_trace_records_real_latency` 通过（latency_ms > 0）
- `test_orchestrator_todo_items_reflect_real_status` 通过（不再是全部 "Planned for research escalation"）
- 现有测试全绿

### Task 5：端到端集成测试 + smoke test
**文件**：`tests/test_agent_e2e.py`（新）

改动：
- 用 `MockLLMClient` + mock DuckDuckGo 跑完整链路
- 验证 `AgentRun` 的 `agents_invoked` 包含所有预期 agent
- 验证 `answer` 是中文、包含 evidence ID、包含"不确定性"或"局限"字样
- 验证 `trace_events` 顺序合理（Triage 在前，Writer 在后）
- 验证 `tool_calls` 包含真实 latency

验收：
- `test_e2e_research_question_runs_full_agent_chain` 通过
- `test_e2e_finance_question_includes_finance_assumptions` 通过
- `test_e2e_answer_is_chinese_with_evidence_citations` 通过
- 手动 smoke test：填真 key，跑 `uvicorn marketlens.api:app`，curl 三个示例问题，回答是真 LLM 生成的中文

## 4. 风险与降级

| 风险 | 概率 | 降级方案 |
|------|------|----------|
| DeepSeek key 失效或额度不足 | 中 | FallbackLLMClient 接管，演示前用 `MARKETLENS_AGENT_MODE=fallback` 强制走 fallback |
| DuckDuckGo 网络不通或限流 | 中 | 降级到 sources.json 模糊匹配，trace 标记 degraded |
| LLM 返回非法 JSON | 高 | Extractor 用 repair prompt 重试一次，再失败用 snippet 直填 |
| LLM 调用延迟 > 30s | 中 | DeepSeek client 已有 30s timeout，超时走 fallback |
| 测试在 CI 跑不了（没 key） | 高 | 所有 LLM 测试用 MockLLMClient，不依赖真 key |
| DuckDuckGo HTML 结构变化 | 低 | 解析失败时降级到 sources.json，不阻塞 run |

## 5. 不动的文件

- `data/evidence.csv` / `data/finance_metrics.csv`（种子数据）
- `data/sources.json`（作为 DuckDuckGo 降级数据源）
- `src/marketlens/schemas.py` / `load.py` / `score.py` / `synthesize.py` / `export.py`
- `web/` 整个前端（M2 再改）
- `deliverables/` 求职材料（下轮拆）
- `docs/application_materials/` 简历材料（M2 同步）

## 6. 完成标准

这轮做完后，以下三件事必须成立：

1. **简历能诚实讲**：把"Planner/Search/Extractor/Verifier/FinanceLens/Writer 协作"这句话对着代码指，每个 agent 都能指到被调用的地方。Triage/Planner/Extractor/Writer 都调 LLM。
2. **演示不穿帮**：填真 key 跑 `uvicorn`，问"霸王茶姬最新扩张动态"，能看到 DuckDuckGo 真搜、Extractor 真抽证据、Verifier 真打分、Writer 真生成中文回答。问"瑞幸价格战对利润率影响"，能看到本地证据充足时跳过搜索。
3. **测试覆盖新链路**：`pytest -q` 全绿，新增的集成测试证明多智能体链不是死代码。

## 7. FAQ（回应你的疑问）

**Q: 为什么不用 LangChain？**
A: spec §3.2 明确写了"不直接套 SDK，自研小型 runtime"。你现在的 `BaseAgent`/`ToolResponse`/`SessionStore`/`TraceLogger` 本质就是手搓版 LangChain 核心。面试时能讲清每行代码，比"我用了 LangChain"有说服力。保持现状。

**Q: Verifier 为什么不用 LLM？**
A: Verifier 干的事是检查证据质量——URL 是不是真的 http 链接、跟现有证据有没有重复、来源类型在不在白名单、置信度够不够。这些都是"是/否"判断，if-else 写死就行。用 LLM 做这些 = 每次花一次 API 调用 + 等 1-2 秒，就为了判断"这个 URL 合不合法"——又慢又浪费钱。

**Q: 什么时候触发搜索？**
A: 只有本地证据少于 2 条时才搜。"瑞幸价格战"本地有 4 条，直接答，不搜；"古茗单店模型"本地 0 条单店数据，才搜。这样省搜索调用，演示更聚焦。

## 8. 下一步

确认这份计划后，我按 Task 1 → 5 顺序执行，每个 Task 完成后跑测试，全绿才进下一个。中途遇到计划没覆盖的情况会停下来问你，不擅自扩 scope。
