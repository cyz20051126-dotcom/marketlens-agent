import { Calculator, Sigma } from "lucide-react";
import type { AgentRun } from "../types/agent";

const metricLabels: Record<string, string> = {
  total_stores: "门店总数",
  partnership_stores: "联营门店",
  same_store_sales_growth: "同店销售增长",
  gaap_operating_margin: "营业利润率",
  store_count_proxy: "门店规模",
  franchise_network_signal: "加盟网络",
  revenue_growth_signal: "收入增长",
  valuation_risk_signal: "估值风险",
  tax_rate: "税率",
  reinvestment_rate: "再投资率",
  per_store_gmv: "单店年 GMV",
  per_store_revenue: "单店年收入",
  store_level_margin: "店级利润率",
  franchise_ratio: "加盟占比",
  same_store_growth: "同店增长",
};

const scenarioLabels: Record<string, string> = {
  Conservative: "保守",
  Base: "基准",
  Upside: "乐观",
  LowDiscount_HighTerminal: "低折现/高永续",
  MidDiscount_MidTerminal: "中折现/中永续",
  HighDiscount_LowTerminal: "高折现/低永续",
  LowStores_HighGMV: "少店/高单店",
  MidStores_MidGMV: "中店/中单店",
  HighStores_LowGMV: "多店/低单店",
};

function formatMetric(value: number, unit: string) {
  if (unit === "ratio") return `${(value * 100).toFixed(1)}%`;
  if (unit === "stores") return Math.round(value).toLocaleString("zh-CN");
  return value.toFixed(2).replace(/\.00$/, "");
}

function FinanceLens({ run }: { run: AgentRun }) {
  return (
    <section className="finance-panel" aria-label="Finance Lens">
      <div className="agent-card-heading">
        <Calculator size={17} />
        <h3>Finance Lens</h3>
      </div>

      {run.finance_assumptions.length === 0 ? (
        <p className="agent-muted">本轮问题不需要金融假设。</p>
      ) : (
        <>
          <div className="assumption-grid">
            {run.finance_assumptions.map((assumption) => (
              <article className="assumption-item" key={assumption.assumption_id}>
                <span>{assumption.period}</span>
                <strong>{metricLabels[assumption.metric_name] ?? assumption.metric_name}</strong>
                <b>{formatMetric(assumption.metric_value, assumption.unit)}</b>
                <p>{assumption.notes}</p>
                <small>证据 {assumption.source_evidence_ids.join(", ")}</small>
              </article>
            ))}
          </div>

          <div className="scenario-panel">
            <div className="agent-card-heading">
              <Sigma size={16} />
              <h3>DCF 风格敏感性</h3>
            </div>
            <div className="scenario-list">
              {run.finance_scenarios.map((scenario) => (
                <article key={scenario.scenario_id}>
                  <strong>{scenarioLabels[scenario.scenario_name] ?? scenario.scenario_name}</strong>
                  <span>增长 {(scenario.revenue_growth * 100).toFixed(1)}%</span>
                  <span>利润率 {(scenario.operating_margin * 100).toFixed(1)}%</span>
                  <b>{scenario.result_value.toFixed(2)}</b>
                </article>
              ))}
            </div>
          </div>
          <p className="agent-caveat">用于作品展示和研究训练，不构成投资建议。</p>
        </>
      )}
    </section>
  );
}

export { FinanceLens };
