# MarketLens Agent v2 中文设计文档

状态：待用户复核
日期：2026-06-20

## 1. 一句话定位

MarketLens Agent 是一个面向中国新茶饮/连锁咖啡品牌的轻量多智能体研究系统。它结合 Agentic RAG、网页研究、结构化证据库和金融分析视角，目标是成为一个可以用于 AI Agent / AI 工作流 / 商业分析相关实习投递的作品，而不是单纯的行业简报生成器。

面试讲法：

> 我参考 HelloAgents 和 Deep Research Agent 的架构思路，自研了一个轻量多智能体研究框架，并把它应用在新消费品牌研究场景里。系统可以通过对话接收问题，先判断本地证据库是否足够；如果不够，就自动规划搜索任务、调用工具抓取公开资料、抽取结构化证据、复核来源质量；如果问题涉及金融分析，还会把经营证据转成单店模型、加盟模型和 DCF 假设，最后输出带引用的研究回答或报告。

## 2. 为什么 v1 不够

现在的 MarketLens v1 有价值，但更像一个 source-to-brief 工作流：

1. 它有结构化证据表。
2. 它能从已有数据生成简报。
3. 它有比较好看的 dashboard。
4. 但它还没有真正展示 Agent 循环。
5. 它还没有显式展示 planning、tool calls、memory、handoff、run traces。
6. 它还没有基于证据库的 AI 对话入口。
7. 它还没有把商业证据转成金融假设和分析模型。

v2 的目标是让项目真正贴近 AI Agent 实习岗位，而不是把普通报告包装成 Agent。

## 3. 调研结论

### 3.1 岗位 JD 信号

| 来源 | JD 强调什么 | 对项目的启发 |
| --- | --- | --- |
| 乐其集团 AI Agent 岗 | Profile、Planning、Memory、Tool Calling / MCP、RAG、Agent framework、evaluation | 项目必须显式做 Agent runtime，而不是只做 UI。 |
| 百融 AI Agent 运营实习 | 任务拆解、工具调用、响应准确性、多轮对话、结构化输出、AI 产品能力评测 | 要加入 chat、trace log、结构化证据、评测样例。 |
| CUHK 深圳发布的远程 AI Agent 实习 | 可复用 Agent、自动化流程、AI 知识库、prompt/tool workflow、数据库字段/标签/索引设计 | 要加入 Evidence DB、可搜索记忆、可复用研究流程。 |

主要参考链接：

- https://www.wondercv.com/xiaozhao/leqee-2026-spring-ai-agent-10542-243500/
- https://www.shixiseng.com/intern/inn_ebjduo0kjxlu
- https://career.cuhk.edu.cn/job/view/id/467284

### 3.2 Agent 架构参考

| 参考项目/文档 | 有用模式 | 我们怎么吸收 |
| --- | --- | --- |
| HelloAgents Chapter 14 | TODO Planner、Task Summarizer、Report Writer、SearchTool、NoteTool | 我们做 Planner、Searcher、Extractor、Verifier、FinanceLens、Writer。 |
| LangChain Deep Agents | 拆解研究问题、委派 sub-agent、带引用综合输出 | Chat 作为入口，Orchestrator 调度多个专业 Agent。 |
| GPT Researcher | planner + execution agents + publisher | 加入研究计划、搜索执行、来源追踪、最终报告。 |
| OpenAI Agents SDK | Agent definitions、tools、handoffs、guardrails、state、observability、evals | 不直接套 SDK，而是在小型自研 runtime 中复刻核心概念。 |
| LangGraph | durable execution、streaming、human-in-the-loop、persistence | 借鉴状态持久化和 trace 思路，v2 MVP 不强依赖 LangGraph。 |
| IBM Agentic RAG | RAG + Agent 可以从多个来源检索并处理复杂工作流 | 本地 Evidence DB 是第一层来源，网页搜索是升级路径。 |

主要参考链接：

- https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter14/Chapter14-Automated-Deep-Research-Agent.md
- https://docs.langchain.com/oss/python/deepagents/deep-research
- https://github.com/assafelovic/gpt-researcher
- https://developers.openai.com/api/docs/guides/agents
- https://docs.langchain.com/oss/python/langgraph/overview
- https://www.ibm.com/think/topics/agentic-rag

### 3.3 金融分析层的依据

新茶饮/连锁咖啡赛道有足够多公开经营指标，可以支撑金融分析层：

| 品牌/来源 | 可用公开指标 | 金融分析用途 |
| --- | --- | --- |
| 瑞幸咖啡 2025 业绩 | 门店数、收入、同店销售增长、自营店店级经营利润率、联营门店收入 | 收入驱动、店级利润率、经营杠杆、价格战影响。 |
| 蜜雪集团 2025 中报报道 | 全球门店数、加盟开店/闭店、收入、净利润、商品设备销售毛利率、加盟服务毛利率 | 加盟模型、供应链利润、门店扩张空间。 |
| 霸王茶姬 SEC 文件 | 门店数、GMV、DCF 折现率调整、可比公司 P/E 变化 | DCF 假设、单店 GMV、增长预期、估值敏感性。 |
| 古茗 IPO 信息 | GMV、门店数、收入、经调整利润、募集资金用途 | 扩张模型、IT/供应链投入、加盟商支持。 |

主要参考链接：

- https://www.globenewswire.com/news-release/2026/02/26/3245426/0/en/luckin-coffee-announces-fourth-quarter-and-fiscal-year-2025-financial-results.html
- https://stcn.com/article/detail/3281427.html
- https://investor.chagee.com/node/6811/html
- https://m.bjnews.com.cn/detail/1738747334168064.html

## 4. 产品形态

第一屏应该像一个 AI research workstation，而不是 landing page，也不是静态 dashboard。

核心布局：

1. 左侧：AI Research Chat。
2. 中间：Agent Todo Board 和 Trace Timeline。
3. 右侧：Evidence DB、引用来源和 Finance Lens。
4. 底部或二级标签页：生成的报告与导出文件。

用户可以问：

- “霸王茶姬扩张是不是过快？”
- “瑞幸价格战对利润率和估值有什么影响？”
- “蜜雪冰城的加盟模型和古茗有什么区别？”
- “帮我用 DCF 假设框架分析 CHAGEE 的增长风险。”

系统回答时必须包含：

1. 直接回答。
2. evidence ID。
3. 回答来自本地证据库还是新搜索。
4. 如果涉及金融问题，列出金融假设。
5. 不确定性和来源质量提示。

## 5. 功能范围

### 5.1 v2 MVP 包含

1. 自研轻量 Agent Runtime：
   - `BaseAgent`
   - `AgentMessage`
   - `Tool`
   - `ToolRegistry`
   - `ToolResponse`
   - `AgentRun`
   - `SessionStore`
   - `TraceLogger`
   - `TodoBoard`

2. LLM Provider 层：
   - 支持 DeepSeek 的 OpenAI-compatible client。
   - 没有 API key 时使用 deterministic fallback，保证 demo 和测试可运行。
   - 支持结构化 JSON 输出解析。
   - 有 retry 和 validation 边界。

3. Agent 组合：
   - `TriageAgent`：判断是本地证据问答、新研究、金融分析还是报告生成。
   - `PlannerAgent`：把研究问题拆成具体任务。
   - `SearchAgent`：调用 Firecrawl/search，返回候选来源。
   - `EvidenceExtractorAgent`：从来源文本中抽取结构化证据。
   - `VerifierAgent`：检查重复、弱来源、冲突信息、过时信息。
   - `FinanceLensAgent`：把证据映射成经营指标和估值假设。
   - `WriterAgent`：生成带 evidence ID 的回答和报告。

4. 工具：
   - `EvidenceSearchTool`：查询本地 evidence。
   - `FirecrawlSearchTool`：证据不足时搜索网页。
   - `SourceReadTool`：读取缓存或抓取后的来源文本。
   - `EvidenceStoreTool`：追加或合并通过验证的证据。
   - `FinanceModelTool`：计算单店经济和 DCF-style sensitivity。
   - `BriefExportTool`：导出 Markdown/JSON/CSV。

5. 前端：
   - Chat 输入和回答面板。
   - 实时 run timeline。
   - Todo board。
   - Tool call cards。
   - 带来源链接的 evidence table。
   - Finance lens 表格/图表。
   - Final report tab。

6. 作品材料：
   - README 改写为 Agentic Research 定位。
   - 架构图。
   - 面试讲稿。
   - 简历 bullet。
   - Demo script。

### 5.2 v2 MVP 不包含

1. 不做投资建议，不输出买入/卖出/持有。
2. 不伪造私有数据。
3. 不强制上生产级向量数据库。
4. 不做登录系统。
5. 本轮不做 Gmail 自动投递。
6. 不声称这是完整金融估值平台。
7. 不直接复制 HelloAgents 代码，只借鉴思想，自研小型可解释 runtime。

## 6. Agentic RAG 行为

系统不应该每次都直接上网搜索。正确逻辑是：先查本地证据库，再判断是否需要补充研究。

决策流程：

```text
用户问题
  -> TriageAgent
  -> 判断意图：
       local_evidence_qa
       new_research_needed
       finance_analysis_needed
       report_generation_needed
  -> 如果本地证据足够：
       EvidenceSearchTool -> WriterAgent 回答
  -> 如果证据不足或过时：
       PlannerAgent -> SearchAgent -> EvidenceExtractorAgent -> VerifierAgent
       -> EvidenceStoreTool -> WriterAgent 回答
  -> 如果涉及金融分析：
       EvidenceSearchTool + FinanceLensAgent + FinanceModelTool
       -> WriterAgent 输出带假设和 caveat 的回答
```

这样 Chat 是用户能看到的入口，但更深层的 Agent 能力体现在 planning、tool use、evidence update 和 traceable synthesis。

## 7. FinanceLensAgent 设计

FinanceLensAgent 的职责是把品牌证据转成分析变量。它应该诚实、有解释性，而不是假装成专业投行估值模型。

### 7.1 金融任务

1. 单店经济：
   - 估算单店 GMV。
   - 估算单店收入。
   - 店级利润率。
   - 加盟服务毛利率。
   - 商品/设备销售毛利率。

2. 扩张模型：
   - 门店数增长。
   - 加盟开店和闭店。
   - 海外 vs 国内扩张。
   - 可获得时加入同店增长。

3. DCF-style 假设：
   - 收入增长率。
   - 经营利润率。
   - 税率。
   - 再投资/资本开支 proxy。
   - 折现率。
   - 永续增长率。

4. 敏感性分析：
   - 增长率 vs 利润率。
   - 门店数 vs 单店 GMV。
   - 折现率 vs 永续增长率。

### 7.2 金融输出

每个金融回答必须包括：

1. 假设表。
2. 关联 evidence ID。
3. 计算公式。
4. 敏感性结果。
5. 明确 caveat：这是学习/研究用途的分析，不构成投资建议。

## 8. 数据模型新增

### 8.1 AgentRun

字段：

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

字段：

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

字段：

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

字段：

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

字段：

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

## 9. 前端体验

### 9.1 默认视图

默认页面一打开就应该像 AI research product：

1. 左侧或左上方是 Chat input。
2. 有最近研究问题。
3. 当前回答带引用。
4. 中间展示 agent run timeline。
5. 右侧展示 evidence 和 finance tabs。

### 9.2 Trace Timeline

展示面向用户的摘要，不展示隐藏 chain of thought：

- “TriageAgent 将问题分类为 finance_analysis_needed。”
- “EvidenceSearchTool 找到 6 条本地证据。”
- “PlannerAgent 创建 4 个研究任务。”
- “FirecrawlSearchTool 返回 5 个候选来源。”
- “VerifierAgent 拒绝 2 条弱来源证据，批准 4 条证据。”
- “FinanceLensAgent 创建 7 个假设和 2 张敏感性表。”

### 9.3 Finance Lens Tab

展示：

1. 经营指标表。
2. 假设卡片。
3. 敏感性矩阵。
4. 来源 evidence ID。
5. caveats。

### 9.4 Evidence DB Tab

展示：

1. 可搜索 evidence table。
2. source URL。
3. confidence。
4. review status。
5. freshness/staleness label。
6. 证据来自人工种子数据还是 agent 抽取。

## 10. 错误处理和安全边界

### 10.1 工具失败

- 失败的工具调用返回 `ToolResponse(success=False, error=...)`。
- 搜索失败时回退到本地证据。
- 来源解析失败时记录 trace event，但不阻塞整个 run。

### 10.2 LLM 失败

- JSON 格式错误时，用 repair prompt 重试一次。
- repair 失败后，对 demo 数据使用 deterministic fallback。
- 最终回答禁止写入无来源判断。

### 10.3 证据质量

- 新证据必须有 source URL、source title、日期（如果可得）、extracted claim、confidence。
- 弱来源或宣传性来源标记为 `needs_review`。
- 冲突证据要显式展示，而不是静默合并。

### 10.4 金融安全边界

- 不输出买入/卖出/持有建议。
- 使用 “DCF-style assumption analysis”，不声称完整正式估值。
- 必须展示假设和证据。
- 必须展示不确定性。

## 11. 测试与验收

### 11.1 Runtime 测试

- Tool registry 可以注册和调用工具。
- ToolResponse 可以序列化成功和失败。
- SessionStore 可以保存 AgentRun。
- TraceLogger 可以按顺序记录事件。

### 11.2 Agent 测试

- TriageAgent 能正确路由本地证据问题。
- PlannerAgent 创建 3-5 个任务。
- EvidenceExtractorAgent 返回符合 schema 的证据行。
- VerifierAgent 拒绝缺少来源的证据。
- FinanceLensAgent 生成带 evidence ID 的假设。
- WriterAgent 拒绝无证据支撑的结论。

### 11.3 UI 测试

- Chat view 能渲染。
- Todo board 能渲染当前 run。
- Tool call timeline 渲染非空事件。
- Evidence tab 的来源链接可点击。
- Finance tab 显示假设和敏感性输出。
- 桌面和移动端不出现文字重叠。

### 11.4 作品验收

- README 能解释 Agent 架构。
- 没有 DeepSeek key 时也能用 fallback mode 运行。
- 有 DeepSeek key 时可走真实 LLM path。
- Demo script 至少包含 3 个问题：
  - 本地证据问答。
  - 证据不足后自动补证。
  - 金融分析。
- 简历 bullet 必须和真实实现一致。

## 12. 实现边界

v2 可以作为一个整体实现计划，但必须拆成清晰里程碑：

1. Agent runtime 和数据模型。
2. 本地 Evidence Q&A 和 chat 入口。
3. DeepSeek provider 和 fallback mode。
4. Research workflow 与 Firecrawl tool adapter。
5. FinanceLensAgent 和模型输出。
6. 前端 Agent Console。
7. 文档、简历更新、截图和测试。

不要一开始就做 UI 美化。第一阶段必须先把 Agent loop 和 trace data 做真。

## 13. 简历表达

完整版本：

> 自研 MarketLens Agent 多智能体研究系统，参考 HelloAgents / Deep Research 架构实现 Triage、Planner、Search、Evidence Extractor、Verifier、FinanceLens、Writer 等 Agent 协作；接入 DeepSeek 与 Firecrawl，支持本地证据库问答、自动搜索补证、结构化证据抽取、工具调用轨迹、会话记忆与带引用的中文研究报告生成，并将茶饮/咖啡品牌经营数据映射为单店模型、加盟模型和 DCF 假设分析。

短版本：

> 自研 MarketLens Agent 多智能体研究系统，基于 DeepSeek + Firecrawl 实现 Planner/Search/Extractor/Verifier/FinanceLens/Writer 协作，支持证据库问答、自动补证、工具调用轨迹、会话记忆及品牌单店模型/DCF 假设分析。

## 14. 面试讲法

60 秒版本：

> 这个项目最开始只是一个 source-to-brief 工作流，但我后来发现这还不够像真正的 Agent，所以我把它重构成了一个轻量 Agent Runtime。用户可以在 Chat 里提出品牌研究问题，系统会先判断本地证据库是否足够，如果不够就用 Planner 拆任务，再通过 SearchAgent 调 Firecrawl 搜索公开资料，Extractor 抽取结构化证据，Verifier 做来源和冲突检查。涉及金融问题时，FinanceLensAgent 会把门店数、GMV、毛利率、加盟服务收入这些证据转成单店模型和 DCF 假设。前端会展示 todo board、tool calls、trace logs 和 evidence IDs，所以面试官能看到它不是只调 API 写一段总结，而是一个有规划、工具、记忆、证据和可观测性的 Agent 系统。

## 15. 成功标准

项目完成的标准：

1. 默认页面一眼看起来就是 Agent research console。
2. 用户可以通过 chat 提问。
3. 系统可以基于本地 evidence ID 回答。
4. 证据不足时可以触发 research workflow。
5. workflow 会记录 todo items、tool calls 和 trace events。
6. FinanceLensAgent 产出与证据关联的假设表。
7. 最终报告和回答包含 citations。
8. 测试能证明 runtime、tools、agents 和 UI 不是假占位。
9. 简历可以诚实写出 multi-agent research、tool calling、memory/trace、evidence extraction 和 finance analysis。

