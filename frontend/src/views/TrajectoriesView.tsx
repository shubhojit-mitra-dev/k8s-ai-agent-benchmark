import React, { useState } from "react";
import { Trajectory, PrimaryArm } from "../types";
import { GitCommit, Clock, CheckCircle2, XCircle, ArrowRight, ShieldCheck, ShieldAlert } from "lucide-react";

interface TrajectoriesViewProps {
  trajectories: Trajectory[];
}

export const TrajectoriesView: React.FC<TrajectoriesViewProps> = ({ trajectories }) => {
  const [selectedScenario, setSelectedScenario] = useState<string>("all");
  const [armA, setArmA] = useState<PrimaryArm>("CF-SONNET");
  const [armB, setArmB] = useState<PrimaryArm>("CF-JEV-SONNET");

  const scenarios = Array.from(new Set(trajectories.map((t) => t.scenario_id))).sort();

  const filteredTrajectories = trajectories.filter((t) =>
    selectedScenario === "all" ? true : t.scenario_id === selectedScenario
  );

  const getTrajectory = (arm: PrimaryArm, scenario: string) => {
    return trajectories.find((t) => t.arm === arm && t.scenario_id === scenario);
  };

  const currentScenarioId = selectedScenario === "all" ? scenarios[0] : selectedScenario;
  const trajA = currentScenarioId ? getTrajectory(armA, currentScenarioId) : null;
  const trajB = currentScenarioId ? getTrajectory(armB, currentScenarioId) : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-surface-border bg-surface p-5">
        <div>
          <h2 className="text-base font-bold text-white">Side-by-Side Trajectory Comparison</h2>
          <p className="text-xs text-slate-400">Step-by-step diff of decision paths and tool executions</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2">
            <label className="text-xs font-mono text-slate-400">Scenario:</label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="rounded-lg border border-surface-border bg-background px-3 py-1.5 text-xs font-mono text-slate-200"
            >
              {scenarios.map((sc) => (
                <option key={sc} value={sc}>{sc}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-xs font-mono text-slate-400">Arm Left:</label>
            <select
              value={armA}
              onChange={(e) => setArmA(e.target.value as PrimaryArm)}
              className="rounded-lg border border-surface-border bg-background px-3 py-1.5 text-xs font-mono text-slate-200"
            >
              <option value="CF-SONNET">CF-SONNET</option>
              <option value="CF-JEV-SONNET">CF-JEV-SONNET</option>
              <option value="OR-SONNET">OR-SONNET</option>
              <option value="OR-JEV-SONNET">OR-JEV-SONNET</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-xs font-mono text-slate-400">Arm Right:</label>
            <select
              value={armB}
              onChange={(e) => setArmB(e.target.value as PrimaryArm)}
              className="rounded-lg border border-surface-border bg-background px-3 py-1.5 text-xs font-mono text-slate-200"
            >
              <option value="CF-SONNET">CF-SONNET</option>
              <option value="CF-JEV-SONNET">CF-JEV-SONNET</option>
              <option value="OR-SONNET">OR-SONNET</option>
              <option value="OR-JEV-SONNET">OR-JEV-SONNET</option>
            </select>
          </div>
        </div>
      </div>

      {/* Side-by-side Trajectory Panes */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left Pane */}
        <div className="rounded-xl border border-surface-border bg-surface p-5">
          <div className="flex items-center justify-between pb-3 border-b border-surface-border">
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span className="font-bold text-slate-200">{armA}</span>
              <span className="text-slate-400">({currentScenarioId || "None"})</span>
            </div>
            {trajA && (
              <span className={`flex items-center space-x-1 text-xs font-mono ${
                trajA.resolved ? "text-emerald-400" : "text-rose-400"
              }`}>
                {trajA.resolved ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
                <span>{trajA.resolved ? "Resolved" : "Failed"}</span>
              </span>
            )}
          </div>

          {trajA ? (
            <div className="mt-4 space-y-3 max-h-[600px] overflow-y-auto pr-2">
              <div className="flex items-center justify-between text-xs font-mono text-slate-400 pb-2 border-b border-surface-border/50">
                <span>Duration: {(trajA.duration_ms / 1000).toFixed(2)}s</span>
                <span>Tokens: {trajA.total_tokens}</span>
                <span>Cost: ${trajA.total_cost_usd.toFixed(4)}</span>
              </div>

              {trajA.tool_events.map((te, idx) => (
                <div key={idx} className="rounded-lg bg-background p-3 border border-surface-border text-xs font-mono space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-primary">#{idx + 1} {te.tool_name}</span>
                    <span className="text-slate-500">{te.duration_ms}ms</span>
                  </div>
                  <div className="text-slate-400 text-[11px] truncate">
                    args: {JSON.stringify(te.arguments)}
                  </div>
                  <div className="rounded bg-surface-raised p-2 text-slate-300 text-[11px] max-h-24 overflow-y-auto whitespace-pre-wrap">
                    {te.output || "No output"}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-6 text-center text-xs text-slate-500">No trajectory recorded for {armA}</p>
          )}
        </div>

        {/* Right Pane */}
        <div className="rounded-xl border border-surface-border bg-surface p-5">
          <div className="flex items-center justify-between pb-3 border-b border-surface-border">
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span className="font-bold text-slate-200">{armB}</span>
              <span className="text-slate-400">({currentScenarioId || "None"})</span>
            </div>
            {trajB && (
              <span className={`flex items-center space-x-1 text-xs font-mono ${
                trajB.resolved ? "text-emerald-400" : "text-rose-400"
              }`}>
                {trajB.resolved ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
                <span>{trajB.resolved ? "Resolved" : "Failed"}</span>
              </span>
            )}
          </div>

          {trajB ? (
            <div className="mt-4 space-y-3 max-h-[600px] overflow-y-auto pr-2">
              <div className="flex items-center justify-between text-xs font-mono text-slate-400 pb-2 border-b border-surface-border/50">
                <span>Duration: {(trajB.duration_ms / 1000).toFixed(2)}s</span>
                <span>Tokens: {trajB.total_tokens}</span>
                <span>Cost: ${trajB.total_cost_usd.toFixed(4)}</span>
              </div>

              {trajB.tool_events.map((te, idx) => (
                <div key={idx} className="rounded-lg bg-background p-3 border border-surface-border text-xs font-mono space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-accent">#{idx + 1} {te.tool_name}</span>
                    <span className="text-slate-500">{te.duration_ms}ms</span>
                  </div>
                  <div className="text-slate-400 text-[11px] truncate">
                    args: {JSON.stringify(te.arguments)}
                  </div>
                  <div className="rounded bg-surface-raised p-2 text-slate-300 text-[11px] max-h-24 overflow-y-auto whitespace-pre-wrap">
                    {te.output || "No output"}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-6 text-center text-xs text-slate-500">No trajectory recorded for {armB}</p>
          )}
        </div>
      </div>
    </div>
  );
};
