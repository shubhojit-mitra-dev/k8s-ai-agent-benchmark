import React from "react";
import { Layers, ShieldCheck, Zap, ArrowRight, BrainCircuit, Terminal } from "lucide-react";

export const ArchitectureView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-surface-border bg-surface p-5">
        <h2 className="text-base font-bold text-white">System Architecture &amp; Evaluation Topology</h2>
        <p className="mt-1 text-xs text-slate-400">
          Comparing Fast Decision Controller (Jev) + Reasoning Orchestrator (Sonnet 5) vs Single Foundation Model Baseline.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Baseline Sonnet */}
        <div className="rounded-xl border border-surface-border bg-surface p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Baseline: Claude Sonnet 5 Alone</h3>
            <span className="rounded bg-sky-500/20 text-sky-400 border border-sky-500/30 px-2 py-0.5 text-xs font-mono font-bold">
              ARM: SONNET
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            The foundation model executes all reasoning, tool selection, risk classification, parameter formation, and validation in a single loop.
          </p>

          <div className="space-y-3 font-mono text-xs">
            <div className="rounded-lg bg-background p-3 border border-surface-border flex items-center space-x-3">
              <Terminal className="h-5 w-5 text-sky-400 shrink-0" />
              <div>
                <span className="font-bold text-slate-200">Incident Alert &amp; Observation</span>
                <p className="text-[11px] text-slate-400">Initial telemetry injected into context window</p>
              </div>
            </div>

            <div className="flex justify-center text-slate-500">
              <ArrowRight className="h-4 w-4 rotate-90" />
            </div>

            <div className="rounded-lg bg-background p-3 border border-surface-border flex items-center space-x-3">
              <BrainCircuit className="h-5 w-5 text-sky-400 shrink-0" />
              <div>
                <span className="font-bold text-slate-200">Full Sonnet 5 Inference Loop</span>
                <p className="text-[11px] text-slate-400">High latency (1.5s - 4.0s), full reasoning trace generation</p>
              </div>
            </div>

            <div className="flex justify-center text-slate-500">
              <ArrowRight className="h-4 w-4 rotate-90" />
            </div>

            <div className="rounded-lg bg-background p-3 border border-surface-border flex items-center space-x-3">
              <ShieldCheck className="h-5 w-5 text-sky-400 shrink-0" />
              <div>
                <span className="font-bold text-slate-200">Kubernetes Simulator Execution</span>
                <p className="text-[11px] text-slate-400">Deterministic action execution and state divergence check</p>
              </div>
            </div>
          </div>
        </div>

        {/* Hybrid Jev + Sonnet */}
        <div className="rounded-xl border border-surface-border bg-surface p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Hybrid: Jev + Claude Sonnet 5</h3>
            <span className="rounded bg-accent/20 text-accent border border-accent/30 px-2 py-0.5 text-xs font-mono font-bold">
              ARM: JEV-SONNET
            </span>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            Jev acts as a low-latency specialized decision controller answering the 4-question contract (Choice, Noul, Score). Sonnet 5 handles complex synthesis when uncertainty exceeds threshold.
          </p>

          <div className="space-y-3 font-mono text-xs">
            <div className="rounded-lg bg-background p-3 border border-surface-border flex items-center space-x-3">
              <Terminal className="h-5 w-5 text-accent shrink-0" />
              <div>
                <span className="font-bold text-slate-200">Incident Alert &amp; Observation</span>
                <p className="text-[11px] text-slate-400">Direct input to Jev Decision Controller</p>
              </div>
            </div>

            <div className="flex justify-center text-slate-500">
              <ArrowRight className="h-4 w-4 rotate-90" />
            </div>

            <div className="rounded-lg bg-background p-3 border border-accent/40 flex items-center space-x-3">
              <Zap className="h-5 w-5 text-accent shrink-0" />
              <div>
                <span className="font-bold text-slate-200">Jev Fast Controller (&lt; 200ms)</span>
                <p className="text-[11px] text-slate-400">Confidence scoring &amp; immediate safe read-only triage</p>
              </div>
            </div>

            <div className="flex justify-center text-slate-500">
              <ArrowRight className="h-4 w-4 rotate-90" />
            </div>

            <div className="rounded-lg bg-background p-3 border border-surface-border flex items-center space-x-3">
              <BrainCircuit className="h-5 w-5 text-secondary shrink-0" />
              <div>
                <span className="font-bold text-slate-200">Sonnet 5 Escalation (Conditional)</span>
                <p className="text-[11px] text-slate-400">Escalated only if Jev confidence &lt; threshold or destructive action</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
