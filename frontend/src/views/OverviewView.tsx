import React from "react";
import { BenchmarkReport, PrimaryArm } from "../types";
import { MetricCard } from "../components/MetricCard";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend 
} from "recharts";

interface OverviewViewProps {
  report: BenchmarkReport | null;
  onNavigateTab: (tab: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ report, onNavigateTab }) => {
  if (!report || !report.metrics) {
    return (
      <div className="flex h-96 flex-col items-center justify-center rounded-xl border border-dashed border-surface-border p-8 text-center">
        <p className="text-slate-400">No benchmark run data loaded.</p>
        <p className="mt-1 text-xs text-slate-500">Run a benchmark from the Live Run tab or load an existing run.</p>
        <button
          onClick={() => onNavigateTab("live")}
          className="mt-4 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-slate-900 transition hover:bg-primary/90"
        >
          Go to Live Runner
        </button>
      </div>
    );
  }

  const { metrics, hypothesis_results } = report;
  const arms = Object.keys(metrics.arms) as PrimaryArm[];

  const chartData = arms.map((arm) => {
    const data = metrics.arms[arm];
    return {
      arm,
      resolutionRate: Number((data.resolution_rate * 100).toFixed(1)),
      safeCorrectRate: Number((data.safe_correct_rate * 100).toFixed(1)),
      durationSec: Number((data.mean_duration_ms / 1000).toFixed(2)),
      costUsd: Number(data.total_cost_usd.toFixed(4)),
      wrongTurns: Number(data.mean_wrong_turns.toFixed(2)),
    };
  });

  const totalCost = Object.values(metrics.arms).reduce((acc, curr) => acc + curr.total_cost_usd, 0);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-primary/30 bg-primary/5 p-6 backdrop-blur">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">Central Research Hypothesis Evaluation</h2>
            <p className="mt-1 text-sm text-slate-300">
              Assessing whether Jev + Sonnet 5 improves latency, safety, and efficiency over Sonnet 5 alone.
            </p>
          </div>
          <span className="rounded-lg border border-primary/40 bg-primary/20 px-3 py-1 font-mono text-xs font-semibold text-primary">
            Run: {report.run_id} ({report.mode})
          </span>
        </div>

        {report.neutral_summary && (
          <div className="mt-4 rounded-lg bg-surface/80 p-4 border border-surface-border text-xs leading-relaxed text-slate-300 font-mono">
            {report.neutral_summary}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Scenarios Tested"
          value={metrics.total_runs}
          subtitle="Across 4 primary arms"
          variant="primary"
        />
        <MetricCard
          title="CF Hybrid vs Baseline Latency"
          value={
            metrics.arms["CF-JEV-SONNET"] && metrics.arms["CF-SONNET"]
              ? `${(metrics.arms["CF-JEV-SONNET"].mean_duration_ms / 1000).toFixed(1)}s vs ${(metrics.arms["CF-SONNET"].mean_duration_ms / 1000).toFixed(1)}s`
              : "N/A"
          }
          subtitle="Mean resolution time"
          variant="accent"
        />
        <MetricCard
          title="CF Hybrid Safe Correct"
          value={
            metrics.arms["CF-JEV-SONNET"]
              ? `${(metrics.arms["CF-JEV-SONNET"].safe_correct_rate * 100).toFixed(1)}%`
              : "N/A"
          }
          subtitle={
            metrics.arms["CF-SONNET"]
              ? `Baseline: ${(metrics.arms["CF-SONNET"].safe_correct_rate * 100).toFixed(1)}%`
              : undefined
          }
          variant="default"
        />
        <MetricCard
          title="Total Evaluation Cost"
          value={`$${totalCost.toFixed(4)}`}
          subtitle="All arms combined"
          variant="warning"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-surface-border bg-surface p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Resolution &amp; Safety Rates (%)
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">Comparing pure resolution vs safe &amp; correct paths</p>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="arm" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#111827", borderColor: "#374151", borderRadius: 8, fontSize: 12 }}
                />
                <Legend />
                <Bar dataKey="resolutionRate" name="Resolution Rate (%)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="safeCorrectRate" name="Safe & Correct Rate (%)" fill="#34d399" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-surface-border bg-surface p-5">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Mean Duration (Seconds)
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">Wall-clock resolution latency per arm</p>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="arm" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} unit="s" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#111827", borderColor: "#374151", borderRadius: 8, fontSize: 12 }}
                />
                <Legend />
                <Bar dataKey="durationSec" name="Mean Duration (s)" fill="#818cf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
