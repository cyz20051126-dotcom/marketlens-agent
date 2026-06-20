import { Activity, CheckCircle2, ListChecks, Wrench } from "lucide-react";
import type { AgentRun } from "../types/agent";

const statusLabels: Record<string, string> = {
  completed: "已完成",
  pending: "待处理",
  prepared: "已准备",
  success: "成功",
  failed: "失败",
};

const taskLabels: Record<string, string> = {
  "Review local evidence": "复核本地证据",
  "Finance assumptions": "生成金融假设",
  "Verify evidence": "校验证据",
  "Draft final answer": "撰写最终回答",
  "Search new sources": "搜索新来源",
  "Structure report": "组织报告结构",
};

const intentLabels: Record<string, string> = {
  finance_analysis_needed: "金融分析",
  new_research_needed: "补充研究",
  report_generation_needed: "报告生成",
  local_evidence_qa: "证据问答",
};

const agentLabels: Record<string, string> = {
  TriageAgent: "意图判断 Agent",
  PlannerAgent: "任务规划 Agent",
  SearchAgent: "搜索 Agent",
  EvidenceExtractorAgent: "证据抽取 Agent",
  VerifierAgent: "证据校验 Agent",
  FinanceLensAgent: "金融分析 Agent",
  WriterAgent: "写作 Agent",
  EvidenceSearchTool: "证据搜索工具",
};

const toolLabels: Record<string, string> = {
  EvidenceSearchTool: "证据搜索工具",
  WebSearchTool: "网页搜索工具",
  FinanceModelTool: "金融模型工具",
  EvidenceStoreTool: "证据入库工具",
};

function displaySummary(summary: string) {
  const classified = summary.match(/^Classified query as (.+)\.$/);
  if (classified) return `判断为${intentLabels[classified[1]] ?? classified[1]}问题。`;
  const found = summary.match(/^Found (\d+) reviewed local evidence rows\.$/);
  if (found) return `找到 ${found[1]} 条已复核本地证据。`;
  const created = summary.match(/^Created (\d+) todo items\.$/);
  if (created) return `生成 ${created[1]} 个研究任务。`;
  const assumptions = summary.match(/^Generated (\d+) finance assumptions\.$/);
  if (assumptions) return `生成 ${assumptions[1]} 个金融假设。`;
  if (summary === "Generated cited answer.") return "生成带证据引用的回答。";
  return summary;
}

function displayOutputSummary(summary: string) {
  const structured = summary.match(/^(\d+) structured items$/);
  if (structured) return `${structured[1]} 个结构化结果`;
  return summary;
}

function AgentTrace({ run }: { run: AgentRun }) {
  return (
    <section className="agent-trace-grid" aria-label="Agent 执行轨迹">
      <div className="agent-card">
        <div className="agent-card-heading">
          <ListChecks size={17} />
          <h3>任务板</h3>
        </div>
        <div className="todo-stack">
          {run.todo_items.length === 0 ? (
            <p className="agent-muted">本地证据足够，本轮未触发补充研究计划。</p>
          ) : (
            run.todo_items.map((item) => (
              <article className="todo-item" key={item.todo_id}>
                <span>{statusLabels[item.status] ?? item.status}</span>
                <strong>{taskLabels[item.title] ?? item.title}</strong>
                <p>{intentLabels[item.intent] ?? item.intent}</p>
              </article>
            ))
          )}
        </div>
      </div>

      <div className="agent-card">
        <div className="agent-card-heading">
          <Activity size={17} />
          <h3>运行轨迹</h3>
        </div>
        <ol className="trace-list">
          {run.trace_events.map((event) => (
            <li key={event.event_id}>
              <CheckCircle2 size={15} />
              <div>
                <strong>{agentLabels[event.agent_name] ?? event.agent_name}</strong>
                <p>{displaySummary(event.summary)}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div className="agent-card">
        <div className="agent-card-heading">
          <Wrench size={17} />
          <h3>工具调用</h3>
        </div>
        <div className="tool-stack">
          {run.tool_calls.map((call) => (
            <article className="tool-item" key={`${call.tool_name}-${call.input_summary}`}>
              <div>
                <strong>{toolLabels[call.tool_name] ?? call.tool_name}</strong>
                <p>{displayOutputSummary(call.output_summary)}</p>
              </div>
              <span>{statusLabels[call.status] ?? call.status}</span>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export { AgentTrace };
