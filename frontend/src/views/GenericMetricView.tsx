import React from "react";
import { BenchmarkReport, PrimaryArm } from "../types";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts";

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
  if (!report || !report.metrics) {
    return (
      <div className="flex h-96 flex-col items-center justify-center rounded-xl border border-dashed border-surface-border p-8 text-center text-slate-500">
        No evaluation data available. Run a benchmark to view {title}.
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
      durationP95: Number((data.p95_duration_ms / 1000).toFixed(2)),
      tokens: data.mean_tokens,
      cost: Number(data.total_cost_usd.toFixed(4)),
      safety: Number((data.mean_safety_score * 100).toFixed(1)),
      wrongTurns: data.mean_wrong_turns,
      prohibited: data.prohibited_action_rate,
      resolutionRate: Number((data.resolution_rate * 100).toFixed(1)),
    };
  });

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-surface-border bg-surface p-5">
        <h2 className="text-base font-bold text-white">{title}</h2>
        <p className="mt-1 text-xs text-slate-400">{description}</p>
      </div>

      <div className="rounded-xl border border-surface-border bg-surface p-5">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Comparative Chart: {title}
        </h3>
        <div className="mt-4 h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="arm" stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#111827", borderColor: "#374151", borderRadius: 8, fontSize: 12 }}
              />
              <Legend />
              {metricKey === "latency" && (
                <>
                  <Bar dataKey="durationP50" name="P50 Duration (s)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="durationP95" name="P95 Duration (s)" fill="#818cf8" radius={[4, 4, 0, 0]} />
                </>
              )}
              {metricKey === "quality" && (
                <Bar dataKey="resolutionRate" name="Resolution Rate (%)" fill="#34d399" radius={[4, 4, 0, 0]} />
              )}
              {metricKey === "safety" && (
                <>
                  <Bar dataKey="safety" name="Safety Score (%)" fill="#34d399" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="wrongTurns" name="Mean Wrong Turns" fill="#fbbf24" radius={[4, 4, 0, 0]} />
                </>
              )}
              {metricKey === "cost" && (
                <Bar dataKey="cost" name="Total Cost ($USD)" fill="#fbbf24" radius={[4, 4, 0, 0]} />
              )}
              {metricKey === "tokens" && (
                <Bar dataKey="tokens" name="Mean Tokens Consumed" fill="#818cf8" radius={[4, 4, 0, 0]} />
              )}
              {(!["latency", "quality", "safety", "cost", "tokens"].includes(metricKey)) && (
                <Bar dataKey="resolutionRate" name="Metric Indicator" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              )}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-xl border border-surface-border bg-surface p-5">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Raw Metric Data Table
        </h3>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="border-b border-surface-border text-slate-400">
              <tr>
                <th className="pb-2">Arm</th>
                <th className="pb-2">Resolution (%)</th>
                <th className="pb-2">P50 Latency (s)</th>
                <th className="pb-2">P95 Latency (s)</th>
                <th className="pb-2">Mean Tokens</th>
                <th className="pb-2">Total Cost ($)</th>
                <th className="pb-2">Safety Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border/50 text-slate-300">
              {chartData.map((d) => (
                <tr key={d.arm} className="hover:bg-surface-raised/40">
                  <td className="py-2.5 font-bold text-primary">{d.arm}</td>
                  <td className="py-2.5">{d.resolutionRate}%</td>
                  <td className="py-2.5">{d.durationP50}s</td>
                  <td className="py-2.5">{d.durationP95}s</td>
                  <td className="py-2.5">{d.tokens.toLocaleString()}</td>
                  <td className="py-2.5">${d.cost}</td>
                  <td className="py-2.5">{d.safety}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
