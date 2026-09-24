import React from "react";
import { ShieldCheck, Zap, ArrowRight, BrainCircuit, Terminal, Cpu } from "lucide-react";

export const ArchitectureView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-hairline bg-surface-card p-6 shadow-warm-sm">
        <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-primary font-semibold">
          <Cpu className="h-4 w-4" />
          <span>System Topology &amp; Decision Protocol</span>
        </div>
        <h2 className="mt-2 text-2xl font-serif font-bold text-ink">
          Architectural Divergence: Fast Controller vs. Monolithic Orchestrator
        </h2>
        <p className="mt-2 text-sm text-body leading-relaxed max-w-3xl">
          Comparing a cascaded, dual-model architecture using a fast specialized decision controller (Jev)
          coupled with a high-capacity reasoning orchestrator (Claude 3.5 Sonnet) against a standard monolithic
          single-model baseline for autonomous Kubernetes cluster incident resolution.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Baseline Sonnet */}
        <div className="rounded-xl border border-hairline bg-surface-card p-6 space-y-5 shadow-warm-sm flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-hairline pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-body">Monolithic Architecture</span>
                <h3 className="text-base font-serif font-bold text-ink">Baseline: Claude Sonnet 5 Alone</h3>
              </div>
              <span className="rounded bg-sky-50 text-sky-700 border border-sky-200 px-2.5 py-1 text-xs font-mono font-bold">
                ARM: SONNET
              </span>
            </div>

            <p className="text-xs text-body leading-relaxed">
              The foundation model executes all reasoning, state observation parsing, tool selection, risk classification, parameter formation, and hypothesis validation inside a single sequential loop.
            </p>

            <div className="space-y-3 font-mono text-xs pt-2">
              <div className="rounded-lg bg-surface-dark text-slate-100 p-3.5 border border-surface-border flex items-center space-x-3">
                <Terminal className="h-5 w-5 text-sky-400 shrink-0" />
                <div>
                  <span className="font-bold text-white">Incident Alert &amp; Observation</span>
                  <p className="text-[11px] text-slate-400">Raw multi-line Prometheus alert &amp; pod logs injected into context</p>
                </div>
              </div>

              <div className="flex justify-center text-body">
                <ArrowRight className="h-4 w-4 rotate-90" />
              </div>

              <div className="rounded-lg bg-surface-dark text-slate-100 p-3.5 border border-surface-border flex items-center space-x-3">
                <BrainCircuit className="h-5 w-5 text-sky-400 shrink-0" />
                <div>
                  <span className="font-bold text-white">Full Sonnet 5 Inference Loop</span>
                  <p className="text-[11px] text-slate-400">High latency (1,500ms - 4,000ms), generates full multi-token reasoning trace</p>
                </div>
              </div>

              <div className="flex justify-center text-body">
                <ArrowRight className="h-4 w-4 rotate-90" />
              </div>

              <div className="rounded-lg bg-surface-dark text-slate-100 p-3.5 border border-surface-border flex items-center space-x-3">
                <ShieldCheck className="h-5 w-5 text-sky-400 shrink-0" />
                <div>
                  <span className="font-bold text-white">Kubernetes Action Execution</span>
                  <p className="text-[11px] text-slate-400">Deterministic action execution and state divergence validation check</p>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-canvas p-3 border border-hairline text-xs font-sans text-body">
            <span className="font-semibold text-ink">Structural Limitation:</span> High token cost per step ($3.00/MTok input, $15.00/MTok output) and elevated response latency on routine read-only diagnostic checks.
          </div>
        </div>

        {/* Hybrid Jev + Sonnet */}
        <div className="rounded-xl border-2 border-primary/40 bg-surface-card p-6 space-y-5 shadow-warm-sm flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-hairline pb-3">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-primary font-bold">Cascaded Hybrid</span>
                <h3 className="text-base font-serif font-bold text-ink">Jev Decision Controller + Sonnet 5</h3>
              </div>
              <span className="rounded bg-primary-soft text-primary-dark border border-primary/30 px-2.5 py-1 text-xs font-mono font-bold">
                ARM: JEV-SONNET
              </span>
            </div>

            <p className="text-xs text-body leading-relaxed">
              Jev acts as a specialized low-latency edge controller answering the 4-question decision contract (Choice, Noul, Score). Claude Sonnet 5 handles complex synthesis only when confidence drops below threshold or destructive mutations occur.
            </p>

            <div className="space-y-3 font-mono text-xs pt-2">
              <div className="rounded-lg bg-surface-dark text-slate-100 p-3.5 border border-surface-border flex items-center space-x-3">
                <Terminal className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <span className="font-bold text-white">Incident Alert &amp; Observation</span>
                  <p className="text-[11px] text-slate-400">Direct input formatted for Jev structured decision evaluation</p>
                </div>
              </div>

              <div className="flex justify-center text-primary">
                <ArrowRight className="h-4 w-4 rotate-90" />
              </div>

              <div className="rounded-lg bg-surface-dark text-slate-100 p-3.5 border border-primary/50 flex items-center space-x-3">
                <Zap className="h-5 w-5 text-primary shrink-0" />
                <div>
                  <span className="font-bold text-white">Jev Fast Controller (&lt; 200ms)</span>
                  <p className="text-[11px] text-slate-400">Immediate safe read-only triage (get_pod_logs, describe_resource)</p>
                </div>
              </div>

              <div className="flex justify-center text-primary">
                <ArrowRight className="h-4 w-4 rotate-90" />
              </div>

              <div className="rounded-lg bg-surface-dark text-slate-100 p-3.5 border border-surface-border flex items-center space-x-3">
                <BrainCircuit className="h-5 w-5 text-emerald-400 shrink-0" />
                <div>
                  <span className="font-bold text-white">Sonnet 5 Escalation (Conditional)</span>
                  <p className="text-[11px] text-slate-400">Invoked exclusively when confidence &lt; 0.70 or mutating action required</p>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-primary-soft/50 p-3 border border-primary/20 text-xs font-sans text-ink">
            <span className="font-semibold text-primary-dark">Empirical Synergy:</span> Absorbs 70%+ of diagnostic steps at ultra-low cost ($0.15/MTok) and sub-200ms latency, routing complex diagnosis to Sonnet.
          </div>
        </div>
      </div>
    </div>
  );
};
