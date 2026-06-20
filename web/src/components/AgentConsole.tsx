import { Bot, Play, RotateCcw, Sparkles } from "lucide-react";
import { useState } from "react";
import demoRun from "../data/agent_demo.json";
import type { AgentRun } from "../types/agent";
import { AgentTrace } from "./AgentTrace";
import { FinanceLens } from "./FinanceLens";

const starterQuestions = [
  "瑞幸价格战对利润率有什么影响？",
  "帮我用 DCF 分析瑞幸价格战对估值的影响",
  "霸王茶姬扩张是不是过快？",
];

const intentLabels: Record<string, string> = {
  finance_analysis_needed: "金融分析",
  new_research_needed: "补充研究",
  report_generation_needed: "报告生成",
  local_evidence_qa: "证据问答",
};

function AgentConsole() {
  const [query, setQuery] = useState(starterQuestions[1]);
  const [run, setRun] = useState<AgentRun>(demoRun as AgentRun);
  const [isLoading, setIsLoading] = useState(false);
  const [notice, setNotice] = useState("内置演示数据保留真实 Agent trace。配置 DeepSeek key 后点击运行可实时调用 LLM；搜索失败会自动降级。");

  async function submit(nextQuery = query) {
    const trimmed = nextQuery.trim();
    if (!trimmed || isLoading) return;
    setQuery(trimmed);
    setIsLoading(true);
    setNotice("Agent 正在运行...");
    try {
      const response = await fetch("/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setRun((await response.json()) as AgentRun);
      setNotice("已连接本地 Agent API。");
    } catch {
      setRun(demoRun as AgentRun);
      setNotice("未检测到 API 服务，已展示内置演示运行。");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="agent-console" id="agent" aria-label="MarketLens Agent 控制台">
      <div className="agent-command-panel">
        <p className="eyebrow">
          <Sparkles size={15} />
          多智能体研究控制台
        </p>
        <h1>
          <span>MarketLens</span>
          <span>Agent</span>
        </h1>
        <p className="hero-subtitle">
          对话入口会先判断问题类型，再调用证据库、DuckDuckGo 真搜索、Finance Lens
          和 Writer，最后留下可复盘的工具调用与轨迹。Triage/Planner/Extractor/Writer 全部走 DeepSeek LLM。
        </p>

        <div className="agent-input-shell">
          <Bot size={19} />
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            rows={3}
            aria-label="输入研究问题"
          />
          <button onClick={() => submit()} disabled={isLoading}>
            {isLoading ? <RotateCcw size={17} /> : <Play size={17} />}
            {isLoading ? "运行中" : "运行"}
          </button>
        </div>

        <div className="starter-row" aria-label="示例问题">
          {starterQuestions.map((question) => (
            <button key={question} onClick={() => submit(question)}>
              {question}
            </button>
          ))}
        </div>

        <article className="agent-answer">
          <div className="answer-meta">
            <span>{intentLabels[run.intent] ?? run.intent}</span>
            <small>{run.run_id}</small>
          </div>
          <p>{run.answer}</p>
          <div className="evidence-chip-row">
            {run.supporting_evidence_ids.map((id) => (
              <span className="evidence-chip is-live" key={id}>
                {id}
              </span>
            ))}
          </div>
        </article>

        <div className="agent-notice">{notice}</div>
      </div>

      <AgentTrace run={run} />
      <FinanceLens run={run} />
    </section>
  );
}

export { AgentConsole };
