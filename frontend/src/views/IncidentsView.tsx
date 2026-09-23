import React, { useState } from "react";
import { ScenarioMetadata } from "../types";
import { AlertTriangle, ShieldCheck, CheckCircle2 } from "lucide-react";

interface IncidentsViewProps {
  scenarios: ScenarioMetadata[];
}

export const IncidentsView: React.FC<IncidentsViewProps> = ({ scenarios }) => {
  const [selectedScenario, setSelectedScenario] = useState<ScenarioMetadata | null>(scenarios[0] || null);

  const difficultyColor = (diff: string) => {
    switch (diff) {
      case "EASY": return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      case "MEDIUM": return "bg-sky-500/20 text-sky-400 border-sky-500/30";
      case "HARD": return "bg-amber-500/20 text-amber-400 border-amber-500/30";
      case "VERY_HARD": return "bg-orange-500/20 text-orange-400 border-orange-500/30";
      case "EXTREME": return "bg-rose-500/20 text-rose-400 border-rose-500/30";
      default: return "bg-slate-700 text-slate-300";
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-surface-border bg-surface p-5">
        <h2 className="text-base font-bold text-white">20-Incident Monotonic Difficulty Ladder</h2>
        <p className="mt-1 text-xs text-slate-400">
          Standardized benchmark scenarios spanning crash loops, admission webhooks, cascading OOM, and multi-tenant quota deadlocks.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* List of Scenarios */}
        <div className="rounded-xl border border-surface-border bg-surface p-4 max-h-[680px] overflow-y-auto space-y-2">
          {scenarios.map((sc) => (
            <button
              key={sc.scenario_id}
              onClick={() => setSelectedScenario(sc)}
              className={`w-full text-left rounded-lg p-3 border transition-all ${
                selectedScenario?.scenario_id === sc.scenario_id
                  ? "bg-primary/10 border-primary/40 text-slate-100"
                  : "bg-background border-surface-border/60 text-slate-400 hover:border-slate-600 hover:text-slate-200"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-primary">{sc.scenario_id}</span>
                <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold border ${difficultyColor(sc.difficulty)}`}>
                  {sc.difficulty}
                </span>
              </div>
              <p className="mt-1 text-xs font-medium text-slate-200 truncate">{sc.name}</p>
            </button>
          ))}
        </div>

        {/* Selected Scenario Details */}
        <div className="rounded-xl border border-surface-border bg-surface p-6 lg:col-span-2">
          {selectedScenario ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-surface-border pb-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-sm font-bold text-primary">{selectedScenario.scenario_id}</span>
                    <span className={`rounded px-2 py-0.5 text-xs font-bold border ${difficultyColor(selectedScenario.difficulty)}`}>
                      {selectedScenario.difficulty}
                    </span>
                  </div>
                  <h3 className="mt-1 text-lg font-bold text-white">{selectedScenario.name}</h3>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Incident Description</h4>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-300 font-mono bg-background p-4 rounded-lg border border-surface-border">
                  {selectedScenario.description}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Verified Root Cause</h4>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-300 font-mono bg-background p-4 rounded-lg border border-surface-border">
                  {selectedScenario.root_cause}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Safe Correct Resolution Path</h4>
                <p className="mt-1.5 text-xs leading-relaxed text-slate-300 font-mono bg-background p-4 rounded-lg border border-surface-border">
                  {selectedScenario.safe_resolution_description}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex h-full items-center justify-center text-slate-500">
              Select a scenario to inspect ground-truth specification
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
