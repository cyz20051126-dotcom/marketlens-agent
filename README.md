# MarketLens Agent

MarketLens Agent 是一个面向中国新茶饮 / 连锁咖啡品牌的轻量多智能体投研控制台。它把本地证据库问答、Agentic RAG、真实网页搜索、可追踪工具调用、会话记录和金融分析视角整合到一个可演示的作品里。

![MarketLens Agent 桌面演示截图](screenshots/marketlens-agent-desktop.png)

## What The Agent Demonstrates

- AI Research Chat over a local evidence database
- Triage / Planner / Search / Extractor / Verifier / FinanceLens / Writer 七个专业 Agent 协作
- **真 LLM 驱动**：Triage / Planner / Extractor / Writer 全部调 DeepSeek（不是规则快速路径）
- **真网页搜索**：Search Agent 调 DuckDuckGo HTML 接口抓真实结果（不是 mock artifact）
- ToolResponse / ToolRegistry / SessionStore / TraceLogger / TodoBoard 等自研轻量 runtime（不依赖 LangChain）
- 每个回答保留 evidence IDs、tool calls、trace timeline 和 todo board
- FinanceLens 将门店数、同店销售、利润率等公开经营指标转为 DCF-style 敏感性假设
- React Agent Console 展示对话、证据、工具调用、运行轨迹和金融假设

## 为什么适合实习投递

这个项目不是普通行业简报页面，而是一个可解释的 AI Agent / AI 工作流作品。它能对应 AI Agent、AI 运营、商业分析、品牌运营和投研助理类 JD 中常见的能力要求。

| JD 信号 | MarketLens Agent 对应能力 |
| --- | --- |
| Agent planning / tool calling | Triage 后由 Planner 拆任务，并调用 EvidenceSearchTool、WebSearchTool、FinanceModelTool。 |
| LLM 集成 / prompt engineering | Triage / Planner / Extractor / Writer 全部走 DeepSeek，prompt + JSON 解析 + 失败降级规则。 |
| RAG / 知识库问答 | `data/evidence.csv` 是本地 Evidence DB，回答必须引用 evidence IDs。 |
| 真实搜索 / Agentic RAG | 证据不足时自动触发 DuckDuckGo 搜索 → 抽取 → 校验 → 入库。 |
| Memory / observability | SessionStore 保存每次 AgentRun，TraceLogger 记录每个 agent/tool 事件。 |
| 结构化输出 | 所有 evidence、tool calls、finance assumptions、scenarios 都是可序列化 schema。 |
| 金融 / 商业分析 | FinanceLens 用门店数、利润率、增长等指标做 DCF-style 敏感性框架。 |
| 前端作品展示 | React 控制台把 chat、todo、trace、tool calls、Finance Lens 放在第一屏。 |

## 架构

```text
用户研究问题
  -> TriageAgent (LLM) 判断意图 + 改写查询
  -> EvidenceSearchTool 查询本地 Evidence DB (严格匹配)
  -> [证据 < 2 条] PlannerAgent (LLM) 拆研究任务
      -> SearchAgent 调 WebSearchTool (DuckDuckGo HTML)
      -> EvidenceExtractorAgent (LLM) 从片段抽取结构化 claims
      -> VerifierAgent (规则) 校验 URL / 重复 / 来源类型 / 置信度
      -> EvidenceStoreTool 写入 work/extracted_evidence.csv
  -> [金融类问题] FinanceLensAgent 生成经营假设和敏感性场景
  -> WriterAgent (LLM) 只引用 reviewed evidence 输出中文回答
  -> AgentRun 保存为 JSON session
  -> FastAPI / React Agent Console 展示结果
```

**设计原则**：
- 不用 LangChain，自研 runtime（面试能讲清每一行代码）
- 纯 LLM 驱动（Triage/Planner/Extractor/Writer 全调 DeepSeek，解析失败才降级到规则）
- Verifier 纯规则不调 LLM（URL/重复/来源/置信度都是是/否判断）
- Research isolation：Extractor 返回结构化 JSON，原始 HTML 不进 Writer 上下文
- 触发搜索条件：本地证据 < 2 条才搜（不靠关键词触发）

## 技术栈

| 层 | 选型 | 理由 |
| --- | --- | --- |
| LLM | DeepSeek (OpenAI-compatible API) | 便宜、中文好、urllib 直调无 SDK 依赖 |
| 搜索 | DuckDuckGo HTML 接口 | 免费、无 key、够演示用（替代昂贵的 Firecrawl） |
| 后端 | FastAPI + uvicorn | 轻量、自带 schema、端口 8765 |
| 前端 | React + Vite + TypeScript | 端口 5173，proxy 到后端 |
| 测试 | pytest | 98 tests passing |
| Runtime | 自研（BaseAgent / ToolRegistry / SessionStore / TraceLogger / TodoBoard） | 不依赖 LangChain，面试可讲清每行 |

## 本地运行

### 1. 环境变量

复制 `.env.example` 为 `.env`，填入你的 DeepSeek API key：

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY=sk-...
```

没有 key 也能跑——LLM client 会降级到 FallbackLLMClient（基于上下文的规则回答），但 Triage/Planner/Extractor/Writer 不会真调 LLM。

### 2. Python 后端

```bash
# 在项目根目录
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -e ".[dev]"

# 启动 API（端口 8765）
python -m uvicorn marketlens.api:app --host 127.0.0.1 --port 8765
```

### 3. 前端

```bash
cd web
npm install
npm run dev -- --port 5173
```

### 4. 打开

```
http://127.0.0.1:5173
```

可以直接提问：

- 瑞幸价格战对利润率有什么影响？
- 帮我用 DCF 分析瑞幸价格战对估值的影响
- 霸王茶姬扩张是不是过快？

## Demo 脚本

不用起前端也能感受效果：

```bash
# 1. 验证 DeepSeek key 能用（5 秒）
python scripts/smoke_test_deepseek.py

# 2. 跑两个示例问题的真 LLM 端到端演示
python scripts/demo_real_llm.py
```

## 测试

```bash
pytest
```

98 个测试全过，覆盖：
- LLM client 层（DeepSeek mock / Fallback / Mock）
- WebSearchTool（DuckDuckGo 解析 / 网络失败降级）
- 四个 agent 的 LLM 路径 + 规则降级
- Orchestrator 全链路（本地证据路径 / 研究路径 / 金融路径）
- 端到端 E2E（agent 顺序 / 金融假设 / 中文引用 / 真延迟 / 降级搜索）

## 输出文件

- `data/evidence.csv`：公开来源证据表（28 条 reviewed，种子数据，不动）
- `data/finance_metrics.csv`：FinanceLens 使用的经营指标 seed metrics（10 条）
- `data/processed/agent_demo.json`：前端 fallback 的 deterministic AgentRun
- `web/src/data/agent_demo.json`：React 控制台内置演示数据
- `work/agent_sessions/`：本地 API 运行后保存的 AgentRun JSON
- `work/extracted_evidence.csv`：搜索抽取的新证据（运行时生成，不污染种子）
- `screenshots/marketlens-agent-desktop.png`：Agent Console 桌面截图

## 来源纪律

本项目只使用公开信息，不声称使用公司内部数据、正式实习经历或投资建议。弱来源不会被隐藏，而是通过 `needs_review` 或置信度体现。WriterAgent 只引用 `reviewed` 且带有效 URL 的证据；FinanceLens 输出是研究训练用的假设框架，不构成投资建议。

## 简历 Bullet

自研 MarketLens Agent 多智能体投研系统，基于 DeepSeek LLM 与 DuckDuckGo HTML 真搜索实现 Triage / Planner / Search / Extractor / Verifier / FinanceLens / Writer 协作，支持证据库问答、自动补证、工具调用轨迹、会话持久化及新茶饮品牌经营指标 / DCF-style 假设分析；自研轻量 Agent runtime（不依赖 LangChain），98 个测试全过。
