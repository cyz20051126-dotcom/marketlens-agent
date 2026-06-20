export type ToolCallRecord = {
  tool_name: string;
  input_summary: string;
  output_summary: string;
  status: string;
  latency_ms: number;
};

export type TraceEvent = {
  event_id: string;
  run_id: string;
  timestamp: string;
  agent_name: string;
  event_type: string;
  summary: string;
  input_preview: string;
  output_preview: string;
  tool_name: string;
  tool_status: string;
  latency_ms: number;
};

export type TodoItem = {
  todo_id: string;
  run_id: string;
  title: string;
  intent: string;
  query: string;
  status: string;
  assigned_agent: string;
  supporting_source_urls: string[];
  result_summary: string;
};

export type FinanceAssumption = {
  assumption_id: string;
  brand_id: string;
  metric_name: string;
  metric_value: number;
  unit: string;
  period: string;
  formula: string;
  source_evidence_ids: string[];
  confidence: number;
  notes: string;
};

export type FinanceScenario = {
  scenario_id: string;
  brand_id: string;
  scenario_name: string;
  revenue_growth: number;
  operating_margin: number;
  discount_rate: number;
  terminal_growth: number;
  sensitivity_axis_x: string;
  sensitivity_axis_y: string;
  result_value: number;
  notes: string;
};

export type AgentRun = {
  run_id: string;
  session_id: string;
  user_query: string;
  intent: string;
  started_at: string;
  completed_at: string;
  status: string;
  agents_invoked: string[];
  tool_calls: ToolCallRecord[];
  trace_events: TraceEvent[];
  todo_items: TodoItem[];
  answer: string;
  supporting_evidence_ids: string[];
  finance_assumptions: FinanceAssumption[];
  finance_scenarios: FinanceScenario[];
  error_message: string;
  llm_provider: string;
  llm_used: boolean;
  fallback_reason: string;
};
