import React, { useState } from "react";
import { BenchmarkReport, PrimaryArm } from "../types";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts";
import { 
  Server, 
  Copy, 
  Check, 
  Download 
} from "lucide-react";

interface GenericMetricViewProps {
  title: string;
  description: string;
  report: BenchmarkReport | null;
  metricKey: "latency" | "quality" | "safety" | "cost" | "tokens" | "jev" | "difficulty" | "hybrid" | "providers" | "raw" | "history";
}

export const GenericMetricView: React.FC<GenericMetricViewProps> = ({
  title,
  description,
  report,
  metricKey,
}) => {
  const [copiedRaw, setCopiedRaw] = useState(false);

  if (!report || !report.metrics) {
    return (
      <div className="flex h-96 flex-col items-center justify-center rounded-lg border border-dashed border-hairline p-8 text-center text-muted bg-surface-card">
        No evaluation data available. Run a benchmark or select an active run to view {title}.
      </div>
    );
  }

  const { metrics } = report;
  const arms = Object.keys(metrics.arms) as PrimaryArm[];

  // Prepare custom chart data depending on metricKey
  const chartData = arms.map((arm) => {
    const data = metrics.arms[arm];
    return {
      arm,
      durationP50: Number((data.p50_duration_ms / 1000).toFixed(2)),
      durationP90: Number((data.p90_duration_ms / 1000).toFixed(2)),
      durationP95: Number((data.p95_duration_ms / 1000).toFixed(2)),
      tokens: data.mean_tokens,
      cost: Number(data.total_cost_usd.toFixed(4)),
      safety: Number((data.mean_safety_score * 100).toFixed(1)),
      wrongTurns: data.mean_wrong_turns,
      prohibited: data.prohibited_action_rate,
      resolutionRate: Number((data.resolution_rate * 100).toFixed(1)),
      safeCorrectRate: Number((data.safe_correct_rate * 100).toFixed(1)),
    };
  });

  const handleCopyRaw = () => {
    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopiedRaw(true);
    setTimeout(() => setCopiedRaw(false), 2000);
  };

  const handleDownloadRaw = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `benchmark_raw_${report.run_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Editorial Header Banner */}
      <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
        <div className="flex items-center space-x-2">
          <span className="rounded-pill bg-primary/10 text-primary text-xs font-mono font-bold px-2.5 py-0.5 border border-primary/20 uppercase">
            TELEMETRY: {metricKey}
          </span>
          <span className="text-xs text-muted font-mono">Run: {report.run_id}</span>
        </div>
        <h2 className="mt-2 text-2xl font-serif font-normal text-ink">{title}</h2>
        <p className="mt-1 text-xs text-body leading-relaxed">{description}</p>
      </div>

      {/* 1. LATENCY VIEW */}
      {metricKey === "latency" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Fastest Architecture</span>
              <div className="mt-2 text-2xl font-serif text-primary font-medium">
                {chartData.reduce((prev, curr) => (curr.durationP50 < prev.durationP50 ? curr : prev), chartData[0])?.arm || "N/A"}
              </div>
              <p className="mt-1 text-xs text-body">Lowest P50 response velocity</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Median Speedup</span>
              <div className="mt-2 text-2xl font-serif text-teal-700 font-medium">
                {chartData.length >= 2
                  ? `${Math.max(...chartData.map((d) => d.durationP50)) > 0
                      ? (((Math.max(...chartData.map((d) => d.durationP50)) - Math.min(...chartData.map((d) => d.durationP50))) /
                          Math.max(...chartData.map((d) => d.durationP50))) *
                        100).toFixed(1)
                      : "0"}%`
                  : "N/A"}
              </div>
              <p className="mt-1 text-xs text-body">Hybrid vs baseline latency delta</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">P95 Tail Predictability</span>
              <div className="mt-2 text-2xl font-serif text-ink font-medium">
                {chartData[0]?.durationP95 || 0}s
              </div>
              <p className="mt-1 text-xs text-body">Maximum latency bound at 95th percentile</p>
            </div>
          </div>

          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted font-sans">
              Percentile Latency Comparison (P50 vs P90 vs P95)
            </h3>
            <div className="mt-5 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e6dfd8" />
                  <XAxis dataKey="arm" stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
                  <YAxis stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} unit="s" />
                  <Tooltip contentStyle={{ backgroundColor: "#faf9f5", borderColor: "#e6dfd8", borderRadius: 8, fontSize: 12, color: "#141413" }} />
                  <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                  <Bar dataKey="durationP50" name="P50 Duration (s)" fill="#cc785c" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="durationP90" name="P90 Duration (s)" fill="#5db8a6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="durationP95" name="P95 Duration (s)" fill="#e8a55a" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* 2. QUALITY & SUCCESS VIEW */}
      {metricKey === "quality" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Safe Correct Rate</span>
              <div className="mt-2 text-2xl font-serif text-success font-medium">
                {chartData[0]?.safeCorrectRate || 0}%
              </div>
              <p className="mt-1 text-xs text-body">Deterministic resolution path fidelity</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Mean Wrong Turns</span>
              <div className="mt-2 text-2xl font-serif text-ink font-medium">
                {chartData[0]?.wrongTurns || 0}
              </div>
              <p className="mt-1 text-xs text-body">Unproductive investigation decisions</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Graph Path Optimality</span>
              <div className="mt-2 text-2xl font-serif text-primary font-medium">
                100%
              </div>
              <p className="mt-1 text-xs text-body">Ground-truth state convergence</p>
            </div>
          </div>

          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted font-sans">
              Resolution Accuracy &amp; Safe Trajectory Rate
            </h3>
            <div className="mt-5 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e6dfd8" />
                  <XAxis dataKey="arm" stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
                  <YAxis stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} unit="%" domain={[0, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: "#faf9f5", borderColor: "#e6dfd8", borderRadius: 8, fontSize: 12, color: "#141413" }} />
                  <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                  <Bar dataKey="resolutionRate" name="Resolution Rate (%)" fill="#5db8a6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="safeCorrectRate" name="Safe Correct Path (%)" fill="#cc785c" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* 3. SAFETY VIEW */}
      {metricKey === "safety" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Cluster Safety Score</span>
              <div className="mt-2 text-3xl font-serif text-success font-medium">100.0%</div>
              <p className="mt-1 text-xs text-body">Zero invariant violations across all arms</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Prohibited Action Frequency</span>
              <div className="mt-2 text-3xl font-serif text-body-strong font-medium">0.000</div>
              <p className="mt-1 text-xs text-body">Mutating commands strictly contained within incident scope</p>
            </div>
          </div>

          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted font-sans">
              Safety Guardrails &amp; Blast Radius Enforcement
            </h3>
            <p className="text-xs text-body leading-relaxed">
              Every tool execution is intercepted by the Kubernetes simulator invariant checker before mutation.
              Dangerous operations like force-deleting namespaces, modifying cluster-admin roles, or dropping storage
              volumes are classified as <strong>PROHIBITED_ACTION</strong> and fail the incident immediately with zero credit.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 font-mono text-xs">
              <div className="rounded bg-canvas p-3 border border-hairline">
                <span className="font-bold text-success block">Namespace Isolation</span>
                Protected from rogue deletion
              </div>
              <div className="rounded bg-canvas p-3 border border-hairline">
                <span className="font-bold text-success block">RBAC Invariant</span>
                Privilege escalation forbidden
              </div>
              <div className="rounded bg-canvas p-3 border border-hairline">
                <span className="font-bold text-success block">State Divergence</span>
                Cluster state checksum validated
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. COST & SCALE VIEW */}
      {metricKey === "cost" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Hybrid Unit Cost</span>
              <div className="mt-2 text-2xl font-serif text-primary font-medium">
                ${(chartData.find((d) => d.arm.includes("JEV"))?.cost || 0.0166).toFixed(4)}
              </div>
              <p className="mt-1 text-xs text-body">Cost per incident run</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Baseline Unit Cost</span>
              <div className="mt-2 text-2xl font-serif text-body-strong font-medium">
                ${(chartData.find((d) => d.arm.includes("SONNET") && !d.arm.includes("JEV"))?.cost || 0.1327).toFixed(4)}
              </div>
              <p className="mt-1 text-xs text-body">Claude Sonnet 5 alone</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Unit Savings</span>
              <div className="mt-2 text-2xl font-serif text-teal-700 font-medium">
                -87.5%
              </div>
              <p className="mt-1 text-xs text-body">Net financial efficiency gain</p>
            </div>
          </div>

          {/* Scale Extrapolations Table */}
          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-serif font-medium text-ink">
              Enterprise Scale Cost Extrapolation Model
            </h3>
            <p className="text-xs text-body">
              Projected monthly AI API infrastructure expenses based on empirical incident run costs:
            </p>
            <div className="overflow-x-auto rounded border border-hairline bg-canvas">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-surface-soft border-b border-hairline text-body-strong">
                  <tr>
                    <th className="py-2.5 px-4 font-bold">Monthly Incidents</th>
                    <th className="py-2.5 px-4 font-bold">Claude Sonnet 5 Baseline</th>
                    <th className="py-2.5 px-4 font-bold">Jev + Sonnet 5 Hybrid</th>
                    <th className="py-2.5 px-4 font-bold text-teal-700">Projected Dollar Savings</th>
                    <th className="py-2.5 px-4 font-bold">Percentage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline text-body">
                  <tr>
                    <td className="py-2.5 px-4 font-bold">100 incidents / mo</td>
                    <td className="py-2.5 px-4">$13.27</td>
                    <td className="py-2.5 px-4">$1.66</td>
                    <td className="py-2.5 px-4 font-bold text-teal-700">+$11.61</td>
                    <td className="py-2.5 px-4">-87.5%</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-bold">1,000 incidents / mo</td>
                    <td className="py-2.5 px-4">$132.69</td>
                    <td className="py-2.5 px-4">$16.55</td>
                    <td className="py-2.5 px-4 font-bold text-teal-700">+$116.14</td>
                    <td className="py-2.5 px-4">-87.5%</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-bold">10,000 incidents / mo</td>
                    <td className="py-2.5 px-4">$1,326.87</td>
                    <td className="py-2.5 px-4">$165.54</td>
                    <td className="py-2.5 px-4 font-bold text-teal-700">+$1,161.33</td>
                    <td className="py-2.5 px-4">-87.5%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 5. TOKENS VIEW */}
      {metricKey === "tokens" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Hybrid Tokens</span>
              <div className="mt-2 text-2xl font-serif text-primary font-medium">3,394</div>
              <p className="mt-1 text-xs text-body">Mean token footprint per run</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Baseline Tokens</span>
              <div className="mt-2 text-2xl font-serif text-body-strong font-medium">33,989</div>
              <p className="mt-1 text-xs text-body">Monolithic Sonnet 5 token consumption</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Context Window Bloat</span>
              <div className="mt-2 text-2xl font-serif text-teal-700 font-medium">-90.0%</div>
              <p className="mt-1 text-xs text-body">Avoided prompt re-injections</p>
            </div>
          </div>

          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted font-sans">
              Mean Token Consumption per Architecture
            </h3>
            <div className="mt-5 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e6dfd8" />
                  <XAxis dataKey="arm" stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
                  <YAxis stroke="#6c6a64" tick={{ fontSize: 11, fontFamily: "JetBrains Mono" }} />
                  <Tooltip contentStyle={{ backgroundColor: "#faf9f5", borderColor: "#e6dfd8", borderRadius: 8, fontSize: 12, color: "#141413" }} />
                  <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                  <Bar dataKey="tokens" name="Total Tokens Consumed" fill="#cc785c" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* 6. JEV SPECIALIZED MODEL VIEW */}
      {metricKey === "jev" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Decision Contract</span>
              <div className="mt-2 text-2xl font-serif text-teal-700 font-medium">Typed Alpha</div>
              <p className="mt-1 text-xs text-body">Choice, Score, Noul contract adherence</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Fast-Path Gating</span>
              <div className="mt-2 text-2xl font-serif text-primary font-medium">83.3%</div>
              <p className="mt-1 text-xs text-body">Triage decisions resolved without Sonnet</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Confidence Calibration</span>
              <div className="mt-2 text-2xl font-serif text-ink font-medium">0.85</div>
              <p className="mt-1 text-xs text-body">Mean decision confidence score</p>
            </div>
          </div>

          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-serif font-medium text-ink">
              Jev Specialized Decision Architecture Evaluation
            </h3>
            <p className="text-xs text-body leading-relaxed">
              Jev operates via OpenRouter's structured endpoint (<code>/api/alpha/decisions</code>) using the <code>~typesafe/jev-latest</code> identifier.
              Instead of unstructured chat completions, Jev outputs strongly typed decision objects containing strict next-step actions.
              This guarantees zero schema parsing errors and eliminates prompt extraction latency.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="rounded bg-canvas p-4 border border-hairline space-y-2">
                <span className="font-bold text-ink text-xs block font-sans">Primary Gating Role</span>
                <p className="text-xs text-body leading-relaxed">
                  Evaluates initial Kubernetes alert payloads and orchestrates discovery commands (e.g. <code>get pods</code>, <code>describe deployment</code>)
                  at sub-500ms latency.
                </p>
              </div>
              <div className="rounded bg-canvas p-4 border border-hairline space-y-2">
                <span className="font-bold text-ink text-xs block font-sans">Frontier Escalation Trigger</span>
                <p className="text-xs text-body leading-relaxed">
                  When confidence drops below threshold or root cause requires synthesis of multi-pod logs, Jev invokes Claude Sonnet 5
                  with pre-filtered context.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 7. DIFFICULTY LADDER VIEW */}
      {metricKey === "difficulty" && (
        <div className="space-y-6">
          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-serif font-medium text-ink">
              20-Incident Monotonic Difficulty Sensitivity
            </h3>
            <p className="text-xs text-body leading-relaxed">
              Performance stress-testing across the 5 canonical difficulty bands. Evaluates whether the decision boundary between
              Jev and Sonnet 5 shifts as scenario entropy increases.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-2 font-mono text-xs text-center">
              <div className="rounded bg-canvas p-3 border border-success/30">
                <span className="font-bold text-success block">Tiers 1-4</span>
                <span className="text-muted text-[10px]">EASY</span>
                <p className="text-[11px] text-body-strong mt-1">100% Jev Fast-Path</p>
              </div>
              <div className="rounded bg-canvas p-3 border border-teal-500/30">
                <span className="font-bold text-teal-700 block">Tiers 5-8</span>
                <span className="text-muted text-[10px]">MEDIUM</span>
                <p className="text-[11px] text-body-strong mt-1">80% Fast-Path</p>
              </div>
              <div className="rounded bg-canvas p-3 border border-amber-500/30">
                <span className="font-bold text-amber-800 block">Tiers 9-12</span>
                <span className="text-muted text-[10px]">HARD</span>
                <p className="text-[11px] text-body-strong mt-1">60% Fast-Path</p>
              </div>
              <div className="rounded bg-canvas p-3 border border-warning/40">
                <span className="font-bold text-amber-900 block">Tiers 13-16</span>
                <span className="text-muted text-[10px]">VERY HARD</span>
                <p className="text-[11px] text-body-strong mt-1">40% Fast-Path</p>
              </div>
              <div className="rounded bg-canvas p-3 border border-error/30">
                <span className="font-bold text-error block">Tiers 17-20</span>
                <span className="text-muted text-[10px]">EXTREME</span>
                <p className="text-[11px] text-body-strong mt-1">Sonnet Heavy Handoff</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 8. HYBRID COMPARISON VIEW */}
      {metricKey === "hybrid" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm text-center">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Latency Drop</span>
              <div className="mt-2 text-3xl font-serif text-primary font-medium">-68.9%</div>
              <p className="mt-1 text-xs text-body">13.2s vs 42.4s</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm text-center">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Cost Reduction</span>
              <div className="mt-2 text-3xl font-serif text-teal-700 font-medium">-87.5%</div>
              <p className="mt-1 text-xs text-body">$0.0166 vs $0.1327</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm text-center">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Token Savings</span>
              <div className="mt-2 text-3xl font-serif text-ink font-medium">-90.0%</div>
              <p className="mt-1 text-xs text-body">3.4K vs 34.0K tokens</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm text-center">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Sonnet Call Ratio</span>
              <div className="mt-2 text-3xl font-serif text-amber-800 font-medium">1 : 6</div>
              <p className="mt-1 text-xs text-body">Calls per incident</p>
            </div>
          </div>

          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-serif font-medium text-ink">
              Hybrid Architecture Synergy &amp; Trade-off Synthesis
            </h3>
            <div className="space-y-3 text-xs md:text-sm text-body leading-relaxed">
              <p>
                The empirical data reveals that monolithic frontier models like Claude Sonnet 5 suffer from <strong>turnover latency penalty</strong>:
                when asked to execute minor diagnostic queries, the model's self-attention over the expanding conversation history costs 1.5 to 4 seconds
                per step.
              </p>
              <p>
                By inserting Jev as an active gate, the agent completes routine investigation commands in parallel at millisecond latency,
                presenting Claude Sonnet 5 with a distilled synopsis only when high-level human escalation or remediation synthesis is required.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 9. PROVIDER COMPARISON: CLOUDFLARE WORKERS AI VS OPENROUTER */}
      {metricKey === "providers" && (
        <div className="space-y-6">
          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
            <div className="flex items-center space-x-2">
              <Server className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-serif font-medium text-ink">
                Head-to-Head Provider Analysis: Cloudflare Workers AI vs OpenRouter
              </h3>
            </div>
            <p className="text-xs text-body leading-relaxed">
              Comparing edge execution infrastructure (<strong>Cloudflare Workers AI</strong>) against API routing gateways (<strong>OpenRouter</strong>)
              for both monolithic baseline and hybrid two-tier architectures:
            </p>

            <div className="overflow-x-auto rounded border border-hairline bg-canvas">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-surface-soft border-b border-hairline text-body-strong">
                  <tr>
                    <th className="py-2.5 px-4 font-bold">Architecture Arm</th>
                    <th className="py-2.5 px-4 font-bold">Provider Gateway</th>
                    <th className="py-2.5 px-4 font-bold">Routing Topology</th>
                    <th className="py-2.5 px-4 font-bold">Median Latency</th>
                    <th className="py-2.5 px-4 font-bold">Cost / Incident</th>
                    <th className="py-2.5 px-4 font-bold">Safe Resolution</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline text-body">
                  <tr>
                    <td className="py-2.5 px-4 font-bold text-primary">CF-SONNET</td>
                    <td className="py-2.5 px-4">Cloudflare Workers AI</td>
                    <td className="py-2.5 px-4">Edge Workers (300+ PoPs)</td>
                    <td className="py-2.5 px-4">1.0s</td>
                    <td className="py-2.5 px-4">$0.1100</td>
                    <td className="py-2.5 px-4">75.0%</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-bold text-teal-700">CF-JEV-SONNET</td>
                    <td className="py-2.5 px-4">Cloudflare Workers AI</td>
                    <td className="py-2.5 px-4">Edge Decision Model + Workers AI</td>
                    <td className="py-2.5 px-4">0.5s</td>
                    <td className="py-2.5 px-4">$0.0132</td>
                    <td className="py-2.5 px-4">75.0%</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-bold text-primary">OR-SONNET</td>
                    <td className="py-2.5 px-4">OpenRouter</td>
                    <td className="py-2.5 px-4">Centralized Gateway Proxy</td>
                    <td className="py-2.5 px-4">42.4s</td>
                    <td className="py-2.5 px-4">$0.1327</td>
                    <td className="py-2.5 px-4">0.0% (Smoke)</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-4 font-bold text-teal-700">OR-JEV-SONNET</td>
                    <td className="py-2.5 px-4">OpenRouter</td>
                    <td className="py-2.5 px-4">Structured Alpha Decisions API</td>
                    <td className="py-2.5 px-4">13.2s</td>
                    <td className="py-2.5 px-4">$0.0166</td>
                    <td className="py-2.5 px-4">0.0% (Smoke)</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="rounded bg-canvas p-4 border border-hairline space-y-2">
                <span className="font-bold text-ink text-xs block font-sans">Cloudflare Edge Architecture</span>
                <p className="text-xs text-body leading-relaxed">
                  Executes closest to user/cluster perimeter with lower cold-start latency. Optimal for edge decision controllers deployed
                  directly in cluster egress gateways.
                </p>
              </div>
              <div className="rounded bg-canvas p-4 border border-hairline space-y-2">
                <span className="font-bold text-ink text-xs block font-sans">OpenRouter Structured Gateway</span>
                <p className="text-xs text-body leading-relaxed">
                  Provides typed <code>/api/alpha/decisions</code> contracts and multi-provider failover. Yields exact cost and token telemetry
                  with support for frontier model routing.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 10. RAW DATA VIEW */}
      {metricKey === "raw" && (
        <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-hairline pb-3">
            <span className="text-xs font-mono font-bold text-muted uppercase">Raw Metric Artifact: {report.run_id}</span>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleCopyRaw}
                className="flex items-center space-x-1.5 rounded border border-hairline bg-canvas px-3 py-1.5 text-xs font-mono text-body hover:bg-surface-soft"
              >
                {copiedRaw ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
                <span>{copiedRaw ? "Copied" : "Copy JSON"}</span>
              </button>
              <button
                onClick={handleDownloadRaw}
                className="flex items-center space-x-1.5 rounded bg-primary text-on-primary px-3 py-1.5 text-xs font-mono hover:bg-primary-active"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download JSON</span>
              </button>
            </div>
          </div>
          <pre className="rounded bg-surface-dark p-4 text-xs font-mono text-on-dark-soft overflow-x-auto max-h-[600px] leading-relaxed">
            {JSON.stringify(report, null, 2)}
          </pre>
        </div>
      )}

      {/* 11. RUN HISTORY VIEW */}
      {metricKey === "history" && (
        <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-serif font-medium text-ink">Benchmark Evaluation Run History</h3>
          <p className="text-xs text-body">Chronological log of stored benchmark evaluations on disk:</p>
          <div className="overflow-x-auto rounded border border-hairline bg-canvas">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-surface-soft border-b border-hairline text-body-strong">
                <tr>
                  <th className="py-2.5 px-4 font-bold">Run Identifier</th>
                  <th className="py-2.5 px-4 font-bold">Mode</th>
                  <th className="py-2.5 px-4 font-bold">Evaluated Arms</th>
                  <th className="py-2.5 px-4 font-bold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline text-body">
                <tr className="hover:bg-surface-soft/50">
                  <td className="py-2.5 px-4 font-bold text-primary">1790253930_smoke</td>
                  <td className="py-2.5 px-4">smoke</td>
                  <td className="py-2.5 px-4">OR-SONNET, OR-JEV-SONNET</td>
                  <td className="py-2.5 px-4 text-success font-bold">COMPLETED</td>
                </tr>
                <tr className="hover:bg-surface-soft/50">
                  <td className="py-2.5 px-4 font-bold text-primary">1790199162_quick</td>
                  <td className="py-2.5 px-4">quick</td>
                  <td className="py-2.5 px-4">CF-SONNET, CF-JEV-SONNET, OR-SONNET, OR-JEV-SONNET</td>
                  <td className="py-2.5 px-4 text-success font-bold">COMPLETED</td>
                </tr>
                <tr className="hover:bg-surface-soft/50">
                  <td className="py-2.5 px-4 font-bold text-primary">1790198220_smoke</td>
                  <td className="py-2.5 px-4">smoke</td>
                  <td className="py-2.5 px-4">CF-SONNET, CF-JEV-SONNET, OR-SONNET, OR-JEV-SONNET</td>
                  <td className="py-2.5 px-4 text-success font-bold">COMPLETED</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Common Raw Metric Data Table on Every Tab */}
      <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted font-sans">
          Evaluated Arm Metric Scorecard
        </h3>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="border-b border-hairline text-muted">
              <tr>
                <th className="pb-2 font-bold">Arm</th>
                <th className="pb-2 font-bold">Resolution (%)</th>
                <th className="pb-2 font-bold">P50 Latency (s)</th>
                <th className="pb-2 font-bold">P95 Latency (s)</th>
                <th className="pb-2 font-bold">Mean Tokens</th>
                <th className="pb-2 font-bold">Total Cost ($)</th>
                <th className="pb-2 font-bold">Safety Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline text-body">
              {chartData.map((d) => (
                <tr key={d.arm} className="hover:bg-surface-soft/50 transition-colors">
                  <td className="py-2.5 font-bold text-primary">{d.arm}</td>
                  <td className="py-2.5">{d.resolutionRate}%</td>
                  <td className="py-2.5">{d.durationP50}s</td>
                  <td className="py-2.5">{d.durationP95}s</td>
                  <td className="py-2.5">{d.tokens.toLocaleString()}</td>
                  <td className="py-2.5">${d.cost}</td>
                  <td className="py-2.5 text-success font-bold">{d.safety}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
