import React from "react";
import { BenchmarkReport } from "../types";
import { FileText, Download, Award, ShieldAlert, Cpu, BarChart2 } from "lucide-react";

interface ScientificReportViewProps {
  report: BenchmarkReport | null;
}

export const ScientificReportView: React.FC<ScientificReportViewProps> = ({ report }) => {
  if (!report || !report.metrics) {
    return (
      <div className="flex h-96 flex-col items-center justify-center rounded-xl border border-dashed border-surface-border p-8 text-center text-slate-500">
        No evaluation report available. Execute a benchmark run to view scientific synthesis.
      </div>
    );
  }

  const { metrics, hypothesis_results, neutral_summary } = report;

  const downloadReport = () => {
    const blob = new Blob([neutral_summary || JSON.stringify(report, null, 2)], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `benchmark_scientific_report_${report.run_id}.md`;
    a.click();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between rounded-xl border border-surface-border bg-surface p-5">
        <div>
          <h2 className="text-base font-bold text-white">Empirical Evaluation &amp; Statistical Report</h2>
          <p className="text-xs text-slate-400">Formal paper-ready breakdown with blinded scoring and statistical confidence</p>
        </div>

        <button
          onClick={downloadReport}
          className="flex items-center space-x-2 rounded-lg bg-surface-raised border border-surface-border px-3 py-1.5 text-xs font-mono font-medium text-slate-200 hover:bg-slate-700"
        >
          <Download className="h-3.5 w-3.5" />
          <span>Export Markdown</span>
        </button>
      </div>

      {/* Synthesis Box */}
      <div className="rounded-xl border border-primary/30 bg-surface p-6 space-y-4">
        <h3 className="text-sm font-bold text-primary uppercase tracking-wider font-mono">
          Executive Research Summary
        </h3>
        <div className="rounded-lg bg-background p-4 text-xs font-mono leading-relaxed text-slate-300 border border-surface-border whitespace-pre-wrap">
          {neutral_summary}
        </div>
      </div>

      {/* Detailed Metrics Table */}
      <div className="rounded-xl border border-surface-border bg-surface p-5">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Comparative Empirical Metrics
        </h3>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="border-b border-surface-border text-slate-400">
              <tr>
                <th className="pb-2">Evaluation Arm</th>
                <th className="pb-2">Sample Size</th>
                <th className="pb-2">Resolution Rate</th>
                <th className="pb-2">Safe &amp; Correct</th>
                <th className="pb-2">P50 Latency</th>
                <th className="pb-2">P95 Latency</th>
                <th className="pb-2">Mean Cost</th>
                <th className="pb-2">Prohibited Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border/50 text-slate-300">
              {Object.entries(metrics.arms).map(([arm, m]) => (
                <tr key={arm} className="hover:bg-surface-raised/40">
                  <td className="py-2.5 font-bold text-primary">{arm}</td>
                  <td className="py-2.5">{m.sample_size}</td>
                  <td className="py-2.5">{(m.resolution_rate * 100).toFixed(1)}%</td>
                  <td className="py-2.5">{(m.safe_correct_rate * 100).toFixed(1)}%</td>
                  <td className="py-2.5">{(m.p50_duration_ms / 1000).toFixed(2)}s</td>
                  <td className="py-2.5">{(m.p95_duration_ms / 1000).toFixed(2)}s</td>
                  <td className="py-2.5">${m.mean_cost_usd.toFixed(4)}</td>
                  <td className="py-2.5 text-danger">{m.prohibited_action_rate.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
