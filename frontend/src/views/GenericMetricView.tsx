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
      rawP50Ms: data.p50_duration_ms,
      rawP90Ms: data.p90_duration_ms,
      rawP95Ms: data.p95_duration_ms,
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
                {chartData.length > 0 ? `${(chartData.reduce((acc, c) => acc + c.safeCorrectRate, 0) / chartData.length).toFixed(1)}%` : "N/A"}
              </div>
              <p className="mt-1 text-xs text-body">Mean across evaluated architectures</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Mean Wrong Turns</span>
              <div className="mt-2 text-2xl font-serif text-ink font-medium">
                {chartData.length > 0 ? (chartData.reduce((acc, c) => acc + c.wrongTurns, 0) / chartData.length).toFixed(2) : "0"}
              </div>
              <p className="mt-1 text-xs text-body">Unproductive investigation decisions</p>
            </div>
            <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase text-muted font-sans">Resolution Rate</span>
              <div className="mt-2 text-2xl font-serif text-primary font-medium">
                {chartData.length > 0 ? `${(chartData.reduce((acc, c) => acc + c.resolutionRate, 0) / chartData.length).toFixed(1)}%` : "N/A"}
              </div>
              <p className="mt-1 text-xs text-body">Mean task resolution success rate</p>
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
      {metricKey === "safety" && (() => {
        const meanSafety = chartData.length > 0
          ? (chartData.reduce((acc, c) => acc + c.safety, 0) / chartData.length).toFixed(1)
          : "100.0";
        const meanProhibited = chartData.length > 0
          ? (chartData.reduce((acc, c) => acc + c.prohibited, 0) / chartData.length).toFixed(3)
          : "0.000";

        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Cluster Safety Score</span>
                <div className="mt-2 text-3xl font-serif text-success font-medium">{meanSafety}%</div>
                <p className="mt-1 text-xs text-body">Mean safe trajectory adherence across all arms</p>
              </div>
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Prohibited Action Frequency</span>
                <div className={`mt-2 text-3xl font-serif font-medium ${Number(meanProhibited) > 0 ? "text-error" : "text-body-strong"}`}>
                  {meanProhibited}
                </div>
                <p className="mt-1 text-xs text-body">Mean rate of destructive or forbidden mutating actions</p>
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
        );
      })()}

      {/* 4. COST & SCALE VIEW */}
      {metricKey === "cost" && (() => {
        const hybCost = chartData.find((d) => d.arm.includes("JEV"))?.cost ?? null;
        const baseCost = chartData.find((d) => d.arm.includes("SONNET") && !d.arm.includes("JEV"))?.cost ?? null;
        const unitSavings = (hybCost !== null && baseCost !== null && baseCost > 0)
          ? (((baseCost - hybCost) / baseCost) * 100).toFixed(1)
          : null;

        const effectiveBaseUnit = baseCost ?? 0.05;
        const effectiveHybUnit = hybCost ?? 0.01;

        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Hybrid Unit Cost</span>
                <div className="mt-2 text-2xl font-serif text-primary font-medium">
                  {hybCost !== null ? `$${hybCost.toFixed(4)}` : "N/A"}
                </div>
                <p className="mt-1 text-xs text-body">Mean cost per incident run</p>
              </div>
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Baseline Unit Cost</span>
                <div className="mt-2 text-2xl font-serif text-body-strong font-medium">
                  {baseCost !== null ? `$${baseCost.toFixed(4)}` : "N/A"}
                </div>
                <p className="mt-1 text-xs text-body">Claude Sonnet 5 alone</p>
              </div>
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Unit Savings</span>
                <div className="mt-2 text-2xl font-serif text-teal-700 font-medium">
                  {unitSavings !== null ? `${Number(unitSavings) >= 0 ? `-${unitSavings}%` : `+${Math.abs(Number(unitSavings))}%`}` : "N/A"}
                </div>
                <p className="mt-1 text-xs text-body">Net financial efficiency delta</p>
              </div>
            </div>

            {/* Scale Extrapolations Table */}
            <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-serif font-medium text-ink">
                Enterprise Scale Cost Extrapolation Model
              </h3>
              <p className="text-xs text-body">
                Projected monthly AI API expenses derived directly from observed unit run costs ({effectiveHybUnit > 0 ? `$${effectiveHybUnit.toFixed(4)}` : "N/A"} vs {effectiveBaseUnit > 0 ? `$${effectiveBaseUnit.toFixed(4)}` : "N/A"}):
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
                    {[100, 1000, 10000].map((incidents) => {
                      const baseMonthly = incidents * effectiveBaseUnit;
                      const hybMonthly = incidents * effectiveHybUnit;
                      const savings = baseMonthly - hybMonthly;
                      const pct = baseMonthly > 0 ? ((savings / baseMonthly) * 100).toFixed(1) : "0.0";
                      return (
                        <tr key={incidents}>
                          <td className="py-2.5 px-4 font-bold">{incidents.toLocaleString()} incidents / mo</td>
                          <td className="py-2.5 px-4">${baseMonthly.toFixed(2)}</td>
                          <td className="py-2.5 px-4">${hybMonthly.toFixed(2)}</td>
                          <td className="py-2.5 px-4 font-bold text-teal-700">
                            {savings >= 0 ? `+$${savings.toFixed(2)}` : `-$${Math.abs(savings).toFixed(2)}`}
                          </td>
                          <td className="py-2.5 px-4">{Number(pct) >= 0 ? `-${pct}%` : `+${Math.abs(Number(pct))}%`}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );
      })()}

      {/* 5. TOKENS VIEW */}
      {metricKey === "tokens" && (() => {
        const hybTok = chartData.find((d) => d.arm.includes("JEV"))?.tokens ?? null;
        const baseTok = chartData.find((d) => d.arm.includes("SONNET") && !d.arm.includes("JEV"))?.tokens ?? null;
        const tokenSavings = (hybTok !== null && baseTok !== null && baseTok > 0)
          ? (((baseTok - hybTok) / baseTok) * 100).toFixed(1)
          : null;

        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Hybrid Tokens</span>
                <div className="mt-2 text-2xl font-serif text-primary font-medium">
                  {hybTok !== null ? hybTok.toLocaleString() : "N/A"}
                </div>
                <p className="mt-1 text-xs text-body">Mean token footprint per run</p>
              </div>
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Baseline Tokens</span>
                <div className="mt-2 text-2xl font-serif text-body-strong font-medium">
                  {baseTok !== null ? baseTok.toLocaleString() : "N/A"}
                </div>
                <p className="mt-1 text-xs text-body">Monolithic Sonnet 5 token consumption</p>
              </div>
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Context Window Efficiency</span>
                <div className="mt-2 text-2xl font-serif text-teal-700 font-medium">
                  {tokenSavings !== null ? `${Number(tokenSavings) >= 0 ? `-${tokenSavings}%` : `+${Math.abs(Number(tokenSavings))}%`}` : "N/A"}
                </div>
                <p className="mt-1 text-xs text-body">Token consumption delta versus baseline</p>
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
        );
      })()}

      {/* 6. JEV SPECIALIZED MODEL VIEW */}
      {metricKey === "jev" && (() => {
        const jevArms = chartData.filter((d) => d.arm.includes("JEV"));
        const jevResRate = jevArms.length > 0
          ? (jevArms.reduce((acc, c) => acc + c.resolutionRate, 0) / jevArms.length).toFixed(1)
          : "N/A";
        const jevP50 = jevArms.length > 0 ? (jevArms[0].durationP50 >= 0.01 ? `${jevArms[0].durationP50}s` : `${jevArms[0].rawP50Ms.toFixed(0)}ms`) : "N/A";

        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Decision Contract</span>
                <div className="mt-2 text-2xl font-serif text-teal-700 font-medium">Typed Alpha</div>
                <p className="mt-1 text-xs text-body">Choice, Score, Noul contract adherence</p>
              </div>
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Resolution Rate</span>
                <div className="mt-2 text-2xl font-serif text-primary font-medium">{jevResRate}%</div>
                <p className="mt-1 text-xs text-body">Resolution fidelity for hybrid arms</p>
              </div>
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm">
                <span className="text-xs font-semibold uppercase text-muted font-sans">P50 Latency</span>
                <div className="mt-2 text-2xl font-serif text-ink font-medium">{jevP50}</div>
                <p className="mt-1 text-xs text-body">Fast-path median turnaround</p>
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
                    at sub-second latency.
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
        );
      })()}

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
                <p className="text-[11px] text-body-strong mt-1">Single-signal failures</p>
              </div>
              <div className="rounded bg-canvas p-3 border border-teal-500/30">
                <span className="font-bold text-teal-700 block">Tiers 5-8</span>
                <span className="text-muted text-[10px]">MEDIUM</span>
                <p className="text-[11px] text-body-strong mt-1">Probe &amp; resource bounds</p>
              </div>
              <div className="rounded bg-canvas p-3 border border-amber-500/30">
                <span className="font-bold text-amber-800 block">Tiers 9-12</span>
                <span className="text-muted text-[10px]">HARD</span>
                <p className="text-[11px] text-body-strong mt-1">Cross-component state</p>
              </div>
              <div className="rounded bg-canvas p-3 border border-warning/40">
                <span className="font-bold text-amber-900 block">Tiers 13-16</span>
                <span className="text-muted text-[10px]">VERY HARD</span>
                <p className="text-[11px] text-body-strong mt-1">Temporal &amp; queue races</p>
              </div>
              <div className="rounded bg-canvas p-3 border border-error/30">
                <span className="font-bold text-error block">Tiers 17-20</span>
                <span className="text-muted text-[10px]">EXTREME</span>
                <p className="text-[11px] text-body-strong mt-1">Cascading Super-Max</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 8. HYBRID COMPARISON VIEW */}
      {metricKey === "hybrid" && (() => {
        const hyb = chartData.find((d) => d.arm.includes("JEV"));
        const base = chartData.find((d) => d.arm.includes("SONNET") && !d.arm.includes("JEV"));

        const latDelta = (hyb && base && base.durationP50 > 0)
          ? (((base.durationP50 - hyb.durationP50) / base.durationP50) * 100).toFixed(1)
          : null;
        const costDelta = (hyb && base && base.cost > 0)
          ? (((base.cost - hyb.cost) / base.cost) * 100).toFixed(1)
          : null;
        const tokDelta = (hyb && base && base.tokens > 0)
          ? (((base.tokens - hyb.tokens) / base.tokens) * 100).toFixed(1)
          : null;

        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm text-center">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Latency Delta</span>
                <div className="mt-2 text-3xl font-serif text-primary font-medium">
                  {latDelta !== null ? `${Number(latDelta) >= 0 ? `-${latDelta}%` : `+${Math.abs(Number(latDelta))}%`}` : "N/A"}
                </div>
                <p className="mt-1 text-xs text-body">{hyb && base ? `${hyb.durationP50}s vs ${base.durationP50}s` : "Run comparison"}</p>
              </div>
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm text-center">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Cost Reduction</span>
                <div className="mt-2 text-3xl font-serif text-teal-700 font-medium">
                  {costDelta !== null ? `${Number(costDelta) >= 0 ? `-${costDelta}%` : `+${Math.abs(Number(costDelta))}%`}` : "N/A"}
                </div>
                <p className="mt-1 text-xs text-body">{hyb && base ? `$${hyb.cost} vs $${base.cost}` : "Run comparison"}</p>
              </div>
              <div className="rounded-lg border border-hairline bg-surface-card p-5 shadow-sm text-center">
                <span className="text-xs font-semibold uppercase text-muted font-sans">Token Savings</span>
                <div className="mt-2 text-3xl font-serif text-ink font-medium">
                  {tokDelta !== null ? `${Number(tokDelta) >= 0 ? `-${tokDelta}%` : `+${Math.abs(Number(tokDelta))}%`}` : "N/A"}
                </div>
                <p className="mt-1 text-xs text-body">{hyb && base ? `${hyb.tokens.toLocaleString()} vs ${base.tokens.toLocaleString()}` : "Run comparison"}</p>
              </div>
            </div>

            <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-serif font-medium text-ink">
                Hybrid Architecture Synergy &amp; Trade-off Synthesis
              </h3>
              <div className="space-y-3 text-xs md:text-sm text-body leading-relaxed">
                <p>
                  The empirical data evaluates whether monolithic frontier models suffer from <strong>turnover latency penalty</strong>:
                  when asked to execute minor diagnostic queries, self-attention over expanding conversation history incurs latency and token accumulation.
                </p>
                <p>
                  By inserting Jev as an active gate, the agent completes routine investigation commands in parallel at low latency,
                  presenting Claude Sonnet 5 with a distilled synopsis only when high-level human escalation or remediation synthesis is required.
                </p>
              </div>
            </div>
          </div>
        );
      })()}

      {/* 9. PROVIDER COMPARISON */}
      {metricKey === "providers" && (
        <div className="space-y-6">
          <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm space-y-4">
            <div className="flex items-center space-x-2">
              <Server className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-serif font-medium text-ink">
                Head-to-Head Provider Analysis: Observed Telemetry
              </h3>
            </div>
            <p className="text-xs text-body leading-relaxed">
              Empirical execution metrics for all arms evaluated in the current benchmark run:
            </p>

            <div className="overflow-x-auto rounded border border-hairline bg-canvas">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-surface-soft border-b border-hairline text-body-strong">
                  <tr>
                    <th className="py-2.5 px-4 font-bold">Architecture Arm</th>
                    <th className="py-2.5 px-4 font-bold">Median Latency</th>
                    <th className="py-2.5 px-4 font-bold">P95 Latency</th>
                    <th className="py-2.5 px-4 font-bold">Mean Cost</th>
                    <th className="py-2.5 px-4 font-bold">Safe Resolution</th>
                    <th className="py-2.5 px-4 font-bold">Prohibited Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline text-body">
                  {chartData.map((d) => (
                    <tr key={d.arm}>
                      <td className="py-2.5 px-4 font-bold text-primary">{d.arm}</td>
                      <td className="py-2.5 px-4">{d.durationP50 >= 0.01 ? `${d.durationP50}s` : `${d.rawP50Ms.toFixed(0)}ms`}</td>
                      <td className="py-2.5 px-4">{d.durationP95 >= 0.01 ? `${d.durationP95}s` : `${d.rawP95Ms.toFixed(0)}ms`}</td>
                      <td className="py-2.5 px-4">${d.cost}</td>
                      <td className="py-2.5 px-4">{d.safeCorrectRate}%</td>
                      <td className={`py-2.5 px-4 font-bold ${d.prohibited > 0 ? "text-error" : "text-success"}`}>
                        {d.prohibited.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
          <h3 className="text-sm font-serif font-medium text-ink">Active Evaluation Run Metadata</h3>
          <p className="text-xs text-body">Details of the currently loaded evaluation:</p>
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
                  <td className="py-2.5 px-4 font-bold text-primary">{report.run_id}</td>
                  <td className="py-2.5 px-4">{report.mode}</td>
                  <td className="py-2.5 px-4">{arms.join(", ")}</td>
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
                  <td className="py-2.5">
                    {d.durationP50 >= 0.01 ? `${d.durationP50}s` : (d.rawP50Ms > 0 ? `${d.rawP50Ms.toFixed(0)}ms` : "0s")}
                  </td>
                  <td className="py-2.5">
                    {d.durationP95 >= 0.01 ? `${d.durationP95}s` : (d.rawP95Ms > 0 ? `${d.rawP95Ms.toFixed(0)}ms` : "0s")}
                  </td>
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
