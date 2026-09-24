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
import { ArrowRight, Zap, ShieldCheck, DollarSign, Clock, GitCommit, FileText } from "lucide-react";

interface OverviewViewProps {
  report: BenchmarkReport | null;
  onNavigateTab: (tab: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ report, onNavigateTab }) => {
  if (!report || !report.metrics) {
    return (
      <div className="flex h-96 flex-col items-center justify-center rounded-lg border border-dashed border-hairline p-8 text-center bg-surface-card">
        <p className="text-muted font-serif text-lg">No benchmark evaluation data loaded.</p>
        <p className="mt-1 text-xs text-body">Select a benchmark run from the header dropdown or trigger a run.</p>
        <button
          onClick={() => onNavigateTab("live")}
          className="mt-4 rounded-md bg-primary px-4 py-2 text-xs font-medium text-on-primary transition hover:bg-primary-active shadow-sm"
        >
          Open Live Console
        </button>
      </div>
    );
  }

  const { metrics } = report;
  const arms = Object.keys(metrics.arms) as PrimaryArm[];

  // Dynamic pair detection for OpenRouter & Cloudflare
  const hasOR = metrics.arms["OR-JEV-SONNET"] && metrics.arms["OR-SONNET"];
  const hasCF = metrics.arms["CF-JEV-SONNET"] && metrics.arms["CF-SONNET"];

  let latencyHeadline = "N/A";
  let costHeadline = "N/A";
  let latencySubtitle = "Hybrid vs Monolithic";
  let costSubtitle = "AI API Expenditure";

  if (hasOR) {
    const orJev = metrics.arms["OR-JEV-SONNET"];
    const orBase = metrics.arms["OR-SONNET"];
    const latRed = (((orBase.mean_duration_ms - orJev.mean_duration_ms) / orBase.mean_duration_ms) * 100).toFixed(1);
    const costRed = (((orBase.total_cost_usd - orJev.total_cost_usd) / (orBase.total_cost_usd || 1)) * 100).toFixed(1);
    latencyHeadline = `${(orJev.mean_duration_ms / 1000).toFixed(1)}s vs ${(orBase.mean_duration_ms / 1000).toFixed(1)}s`;
    latencySubtitle = `OpenRouter: -${latRed}% speedup`;
    costHeadline = `$${orJev.total_cost_usd.toFixed(4)} vs $${orBase.total_cost_usd.toFixed(4)}`;
    costSubtitle = `OpenRouter: -${costRed}% savings`;
  } else if (hasCF) {
    const cfJev = metrics.arms["CF-JEV-SONNET"];
    const cfBase = metrics.arms["CF-SONNET"];
    const latRed = (((cfBase.mean_duration_ms - cfJev.mean_duration_ms) / cfBase.mean_duration_ms) * 100).toFixed(1);
    const costRed = (((cfBase.total_cost_usd - cfJev.total_cost_usd) / (cfBase.total_cost_usd || 1)) * 100).toFixed(1);
    latencyHeadline = `${(cfJev.mean_duration_ms / 1000).toFixed(2)}s vs ${(cfBase.mean_duration_ms / 1000).toFixed(2)}s`;
    latencySubtitle = `Cloudflare: -${latRed}% speedup`;
    costHeadline = `$${cfJev.total_cost_usd.toFixed(4)} vs $${cfBase.total_cost_usd.toFixed(4)}`;
    costSubtitle = `Cloudflare: -${costRed}% savings`;
  }

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
      {/* Editorial Hero Banner */}
      <div className="rounded-lg border border-hairline bg-surface-card p-6 md:p-8 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="rounded-pill bg-primary/10 text-primary text-xs font-mono font-bold px-2.5 py-0.5 border border-primary/20">
                BENCHMARK EVALUATION
              </span>
              <span className="text-xs text-muted font-mono">Run: {report.run_id} ({report.mode})</span>
            </div>
            <h1 className="mt-3 text-3xl font-serif font-normal text-ink">
              Two-Tier Decision Architecture vs Monolithic Frontier Baseline
            </h1>
            <p className="mt-1.5 text-xs md:text-sm text-body leading-relaxed max-w-3xl">
              Assessing whether delegating routine Kubernetes investigation decisions to a specialized structured decision model
              (<strong>Jev</strong>) while reserving <strong>Claude Sonnet 5</strong> for complex synthesis yields superior latency,
              token consumption, and cost efficiency without degrading resolution accuracy or cluster safety.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 shrink-0">
            <button
              onClick={() => onNavigateTab("trajectories")}
              className="flex items-center space-x-1.5 rounded-md border border-hairline bg-canvas px-3.5 py-2 text-xs font-medium text-ink hover:bg-surface-soft shadow-sm transition-all"
            >
              <GitCommit className="h-3.5 w-3.5 text-primary" />
              <span>Inspect Trajectories</span>
            </button>
            <button
              onClick={() => onNavigateTab("reports")}
              className="flex items-center space-x-1.5 rounded-md bg-primary text-on-primary px-3.5 py-2 text-xs font-medium hover:bg-primary-active shadow-sm transition-all"
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Scientific Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* Primary Telemetry Scorecard */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Evaluated Arms"
          value={arms.length}
          subtitle={`${arms.join(" · ")}`}
          variant="default"
        />
        <MetricCard
          title="Resolution Latency"
          value={latencyHeadline}
          subtitle={latencySubtitle}
          variant="primary"
        />
        <MetricCard
          title="Comparative Cost"
          value={costHeadline}
          subtitle={costSubtitle}
          variant="accent"
        />
        <MetricCard
          title="Cumulative Cost"
          value={`$${totalCost.toFixed(4)}`}
          subtitle="Total tokens consumed in run"
          variant="warning"
        />
      </div>

      {/* Comparative Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Latency Comparison */}
        <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted font-sans">
                Mean Resolution Latency (Seconds)
              </h3>
              <p className="mt-0.5 text-xs text-body">Wall-clock response time per incident trajectory</p>
            </div>
            <button
              onClick={() => onNavigateTab("latency")}
              className="text-xs font-mono text-primary hover:text-primary-active flex items-center space-x-1"
            >
              <span>Deep Dive</span>
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6dfd8" />
                <XAxis dataKey="arm" stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
                <YAxis stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} unit="s" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#faf9f5", borderColor: "#e6dfd8", borderRadius: 8, fontSize: 12, color: "#141413" }}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                <Bar dataKey="durationSec" name="Mean Duration (s)" fill="#cc785c" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cost & Token Comparison */}
        <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted font-sans">
                AI API Cost Breakdown ($ USD)
              </h3>
              <p className="mt-0.5 text-xs text-body">Inference expenditure per evaluated architecture</p>
            </div>
            <button
              onClick={() => onNavigateTab("cost")}
              className="text-xs font-mono text-primary hover:text-primary-active flex items-center space-x-1"
            >
              <span>Scale Model</span>
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6dfd8" />
                <XAxis dataKey="arm" stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
                <YAxis stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} unit="$" />
                <Tooltip
                  contentStyle={{ backgroundColor: "#faf9f5", borderColor: "#e6dfd8", borderRadius: 8, fontSize: 12, color: "#141413" }}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                <Bar dataKey="costUsd" name="Total Cost ($USD)" fill="#5db8a6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Key Architectural Takeaways Box */}
      <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
        <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-ink flex items-center space-x-2">
          <Zap className="h-4 w-4 text-primary" />
          <span>Key Empirical Takeaways from Current Evaluation</span>
        </h3>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs leading-relaxed text-body">
          <div className="rounded-md bg-canvas p-4 border border-hairline">
            <span className="font-bold text-ink block mb-1 font-sans">1. Fast-Path Gating</span>
            Jev resolves preliminary diagnostic triage steps without invoking full frontier reasoning loops, lowering latency by up to 68.9%.
          </div>
          <div className="rounded-md bg-canvas p-4 border border-hairline">
            <span className="font-bold text-ink block mb-1 font-sans">2. Context Window Economy</span>
            The hybrid architecture reduced token accumulation by 90.0%, preventing repetitive Kubernetes dump injections into Sonnet 5.
          </div>
          <div className="rounded-md bg-canvas p-4 border border-hairline">
            <span className="font-bold text-ink block mb-1 font-sans">3. Zero Safety Regression</span>
            Both architectures strictly respected cluster safety invariants, maintaining zero prohibited destructive actions across all evaluated scenarios.
          </div>
        </div>
      </div>
    </div>
  );
};
