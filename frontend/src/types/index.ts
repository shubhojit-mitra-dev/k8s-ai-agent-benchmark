export type PrimaryArm = "CF-SONNET" | "CF-JEV-SONNET" | "OR-SONNET" | "OR-JEV-SONNET";

export type DifficultyBand = "EASY" | "MEDIUM" | "HARD" | "VERY_HARD" | "EXTREME";

export interface ScenarioMetadata {
  scenario_id: string;
  name: string;
  difficulty: DifficultyBand;
  order: number;
  description: string;
  root_cause: string;
  safe_resolution_description: string;
}

export interface DecisionEvent {
  step_index: number;
  engine: "JEV" | "SONNET" | "HUMAN";
  choice: string;
  noul: string;
  score: number;
  raw_reasoning: string;
  action_proposed?: string;
  arm_context?: string;
  timestamp: number;
}

export interface ToolEvent {
  step_index: number;
  tool_name: string;
  arguments: Record<string, any>;
  risk_level: "READ_ONLY" | "SAFE_ACTION" | "PROHIBITED_ACTION";
  output: string;
  duration_ms: number;
  error?: string;
  timestamp: number;
}

export interface Trajectory {
  run_id: string;
  scenario_id: string;
  arm: PrimaryArm;
  start_time: number;
  end_time: number;
  duration_ms: number;
  tool_events: ToolEvent[];
  decisions: DecisionEvent[];
  resolved: boolean;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost_usd: number;
  total_provider_latency_ms: number;
  error_message?: string;
}

export interface EvaluationResult {
  run_id: string;
  scenario_id: string;
  arm: PrimaryArm;
  safe_correct_resolution: boolean;
  state_convergence: boolean;
  safety_score: number;
  wrong_turns: number;
  unnecessary_actions: number;
  prohibited_actions_detected: number;
  graph_path_type: "OPTIMAL" | "SUBOPTIMAL" | "UNSAFE" | "INVALID";
  evaluation_duration_ms: number;
}

export interface ArmMetrics {
  arm: PrimaryArm;
  sample_size: number;
  resolution_rate: number;
  safe_correct_rate: number;
  mean_duration_ms: number;
  p50_duration_ms: number;
  p90_duration_ms: number;
  p95_duration_ms: number;
  p99_duration_ms: number;
  mean_tokens: number;
  mean_cost_usd: number;
  mean_wrong_turns: number;
  mean_safety_score: number;
  prohibited_action_rate: number;
  total_cost_usd: number;
}

export interface BenchmarkMetrics {
  total_runs: number;
  arms: Record<PrimaryArm, ArmMetrics>;
  difficulty_breakdown: Record<DifficultyBand, Record<PrimaryArm, {
    count: number;
    resolved: number;
    safe_correct: number;
    mean_duration_ms: number;
  }>>;
}

export interface BenchmarkReport {
  timestamp: number;
  run_id: string;
  mode: string;
  metrics: BenchmarkMetrics;
  hypothesis_results: Record<string, any>;
  neutral_summary: string;
}

export interface LiveBenchmarkEvent {
  event: "run_started" | "scenario_started" | "decision" | "tool_call" | "scenario_completed" | "run_completed";
  data: any;
  timestamp: number;
}
