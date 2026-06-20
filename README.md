# MarketLens Agent

MarketLens Agent 是一个面向中国新茶饮/连锁咖啡品牌的轻量多智能体研究控制台。它把本地证据库问答、Agentic RAG、Firecrawl-ready 网页研究、可追踪工具调用、会话记录和金融分析视角整合到一个可演示的作品里。

![MarketLens Agent 桌面演示截图](screenshots/marketlens-agent-desktop.png)

## What The Agent Demonstrates

- AI Research Chat over a local evidence database
- Triage、Planner、Evidence Search、FinanceLens、Writer 等专业 Agent 协作
- ToolResponse、ToolRegistry、SessionStore、TraceLogger、TodoBoard 等自研轻量 runtime
- 每个回答保留 evidence IDs、tool calls、trace timeline 和 todo board
- FinanceLens 将门店数、同店销售、利润率等公开经营指标转为 DCF-style 敏感性假设
- React Agent Console 展示对话、证据、工具调用、运行轨迹和金融假设

## 为什么适合实习投递

这个项目不是普通行业简报页面，而是一个可解释的 AI Agent / AI 工作流作品。它能对应 AI Agent、AI 运营、商业分析、品牌运营和投研助理类 JD 中常见的能力要求。

| JD 信号 | MarketLens Agent 对应能力 |
| --- | --- |
| Agent planning / tool calling | Triage 后由 Planner 拆任务，并调用 EvidenceSearchTool、FirecrawlSearchTool、FinanceModelTool。 |
| RAG / 知识库问答 | `data/evidence.csv` 是本地 Evidence DB，回答必须引用 evidence IDs。 |
| Memory / observability | SessionStore 保存每次 AgentRun，TraceLogger 记录每个 agent/tool 事件。 |
| 结构化输出 | 所有 evidence、tool calls、finance assumptions、scenarios 都是可序列化 schema。 |
| 金融/商业分析 | FinanceLens 用门店数、利润率、增长等指标做 DCF-style 敏感性框架。 |
| 前端作品展示 | React 控制台把 chat、todo、trace、tool calls、Finance Lens 放在第一屏。 |

## 架构

```text
用户研究问题
  -> TriageAgent 判断意图
  -> EvidenceSearchTool 查询本地 Evidence DB
  -> PlannerAgent 在证据不足时生成研究任务
  -> FirecrawlSearchTool 准备外部搜索请求 artifact
  -> FinanceLensAgent 生成经营假设和敏感性场景
  -> WriterAgent 只引用 reviewed evidence 输出回答
  -> AgentRun 保存为 JSON session
  -> FastAPI / React Agent Console 展示结果
```

## 本地运行

Python/API：

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python scripts\build_artifacts.py
.\.venv\Scripts\python -m uvicorn marketlens.api:app --host 127.0.0.1 --port 8765
```

前端：

```powershell
cd C:\Users\chenyizhe\Desktop\MarketLens_AI\web
npm install
npm run dev -- --port 5173
```

打开：

```text
http://127.0.0.1:5173
```

可以直接提问：

- 瑞幸价格战对利润率有什么影响？
- 帮我用 DCF 分析瑞幸价格战对估值的影响
- 霸王茶姬扩张是不是过快？

## 输出文件

- `data/evidence.csv`：公开来源证据表。
- `data/finance_metrics.csv`：FinanceLens 使用的经营指标 seed metrics。
- `data/processed/agent_demo.json`：前端 fallback 的 deterministic AgentRun。
- `web/src/data/agent_demo.json`：React 控制台内置演示数据。
- `work/agent_sessions/`：本地 API 运行后保存的 AgentRun JSON。
- `screenshots/marketlens-agent-desktop.png`：Agent Console 桌面截图。

## 来源纪律

本项目只使用公开信息，不声称使用公司内部数据、正式实习经历或投资建议。弱来源不会被隐藏，而是通过 `needs_review` 或置信度体现。WriterAgent 只引用 `reviewed` 且带有效 URL 的证据；FinanceLens 输出是研究训练用的假设框架，不构成投资建议。

## 简历 Bullet

自研 MarketLens Agent 多智能体研究系统，基于 DeepSeek-compatible LLM 接口与 Firecrawl-ready 搜索工具实现 Triage / Planner / Evidence Search / Verifier / FinanceLens / Writer 协作，支持证据库问答、自动补证准备、工具调用轨迹、会话持久化及新茶饮品牌经营指标/DCF-style 假设分析。
