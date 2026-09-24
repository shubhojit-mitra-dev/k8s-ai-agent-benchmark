import React, { useState } from "react";
import { Trajectory, PrimaryArm } from "../types";
import { GitCommit, Clock, CheckCircle2, XCircle, ArrowRight, ShieldCheck, ShieldAlert } from "lucide-react";

interface TrajectoriesViewProps {
  trajectories: Trajectory[];
}

export const TrajectoriesView: React.FC<TrajectoriesViewProps> = ({ trajectories }) => {
  const availableArms = Array.from(new Set(trajectories.map((t) => t.arm)));
  const scenarios = Array.from(new Set(trajectories.map((t) => t.scenario_id))).sort();

  const [selectedScenario, setSelectedScenario] = useState<string>(scenarios[0] || "all");
  const [armA, setArmA] = useState<string>(
    availableArms.find((a) => a.includes("SONNET") && !a.includes("JEV")) || availableArms[0] || "OR-SONNET"
  );
  const [armB, setArmB] = useState<string>(
    availableArms.find((a) => a.includes("JEV")) || availableArms[1] || "OR-JEV-SONNET"
  );

  const filteredTrajectories = trajectories.filter((t) =>
    selectedScenario === "all" ? true : t.scenario_id === selectedScenario
  );

  const getTrajectory = (arm: string, scenario: string) => {
    return trajectories.find((t) => t.arm === arm && t.scenario_id === scenario);
  };

  const currentScenarioId = selectedScenario === "all" ? scenarios[0] : selectedScenario;
  const trajA = currentScenarioId ? getTrajectory(armA, currentScenarioId) : null;
  const trajB = currentScenarioId ? getTrajectory(armB, currentScenarioId) : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <span className="rounded-pill bg-primary/10 text-primary text-xs font-mono font-bold px-2.5 py-0.5 border border-primary/20">
              AUDIT TRAIL
            </span>
            <span className="text-xs text-muted font-mono">{trajectories.length} Total Trajectories</span>
          </div>
          <h2 className="mt-2 text-2xl font-serif font-normal text-ink">Side-by-Side Trajectory Comparison</h2>
          <p className="mt-1 text-xs text-body leading-relaxed">
            Examine step-by-step decision reasoning traces, tool executions, and state transitions between architectures.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2 text-xs">
            <label className="text-muted font-medium">Scenario:</label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="rounded-md border border-hairline bg-canvas px-3 py-1.5 font-mono text-xs text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            >
              {scenarios.map((sc) => (
                <option key={sc} value={sc}>{sc}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <label className="text-muted font-medium">Arm Left:</label>
            <select
              value={armA}
              onChange={(e) => setArmA(e.target.value)}
              className="rounded-md border border-hairline bg-canvas px-3 py-1.5 font-mono text-xs text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            >
              {availableArms.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <label className="text-muted font-medium">Arm Right:</label>
            <select
              value={armB}
              onChange={(e) => setArmB(e.target.value)}
              className="rounded-md border border-hairline bg-canvas px-3 py-1.5 font-mono text-xs text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            >
              {availableArms.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Side-by-side Trajectory Panes */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left Pane */}
        <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-hairline">
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span className="font-bold text-ink">{armA}</span>
              <span className="text-muted">({currentScenarioId || "None"})</span>
            </div>
            {trajA && (
              <span className={`flex items-center space-x-1 text-xs font-mono font-medium ${
                trajA.resolved ? "text-success" : "text-muted"
              }`}>
                {trajA.resolved ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Clock className="h-3.5 w-3.5" />}
                <span>{trajA.resolved ? "Resolved" : "Completed / Evaluated"}</span>
              </span>
            )}
          </div>

          {trajA ? (
            <div className="mt-4 space-y-3 max-h-[620px] overflow-y-auto pr-2">
              <div className="grid grid-cols-3 gap-2 text-xs font-mono bg-canvas p-3 rounded-md border border-hairline text-body">
                <div>
                  <span className="text-[10px] text-muted block uppercase">Duration</span>
                  <span className="font-bold text-ink">{(trajA.duration_ms / 1000).toFixed(2)}s</span>
                </div>
                <div>
                  <span className="text-[10px] text-muted block uppercase">Tokens</span>
                  <span className="font-bold text-ink">{trajA.total_tokens.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-[10px] text-muted block uppercase">Cost</span>
                  <span className="font-bold text-ink">${trajA.total_cost_usd.toFixed(4)}</span>
                </div>
              </div>

              {/* Combined chronological event list */}
              <div className="space-y-2.5">
                {trajA.decisions.map((dec, idx) => (
                  <div key={`dec-${idx}`} className="rounded-md bg-canvas p-3.5 border border-hairline text-xs font-mono space-y-1.5 shadow-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-muted text-[11px]">Step {dec.step_index || idx + 1}</span>
                      <span className="text-xs font-bold text-primary px-2 py-0.5 rounded bg-primary/10 border border-primary/20">
                        {dec.engine}
                      </span>
                    </div>
                    <p className="text-body-strong font-sans text-xs">
                      <strong>Decision:</strong> {dec.choice}
                    </p>
                    {dec.raw_reasoning && dec.raw_reasoning !== "{}" && (
                      <div className="rounded bg-surface-soft p-2 text-muted text-[11px] overflow-x-auto whitespace-pre-wrap font-mono">
                        {dec.raw_reasoning}
                      </div>
                    )}
                  </div>
                ))}

                {trajA.tool_events.map((te, idx) => (
                  <div key={`tool-${idx}`} className="rounded-md bg-canvas p-3 border border-hairline text-xs font-mono space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-teal-700">Tool: {te.tool_name}</span>
                      <span className="text-muted text-[11px]">{te.duration_ms}ms</span>
                    </div>
                    {te.output && (
                      <div className="rounded bg-surface-dark p-2 text-on-dark-soft text-[11px] max-h-28 overflow-y-auto whitespace-pre-wrap font-mono">
                        {te.output}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="mt-8 text-center text-xs text-muted">No trajectory recorded for {armA}</p>
          )}
        </div>

        {/* Right Pane */}
        <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-hairline">
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span className="font-bold text-ink">{armB}</span>
              <span className="text-muted">({currentScenarioId || "None"})</span>
            </div>
            {trajB && (
              <span className={`flex items-center space-x-1 text-xs font-mono font-medium ${
                trajB.resolved ? "text-success" : "text-muted"
              }`}>
                {trajB.resolved ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Clock className="h-3.5 w-3.5" />}
                <span>{trajB.resolved ? "Resolved" : "Completed / Evaluated"}</span>
              </span>
            )}
          </div>

          {trajB ? (
            <div className="mt-4 space-y-3 max-h-[620px] overflow-y-auto pr-2">
              <div className="grid grid-cols-3 gap-2 text-xs font-mono bg-canvas p-3 rounded-md border border-hairline text-body">
                <div>
                  <span className="text-[10px] text-muted block uppercase">Duration</span>
                  <span className="font-bold text-ink">{(trajB.duration_ms / 1000).toFixed(2)}s</span>
                </div>
                <div>
                  <span className="text-[10px] text-muted block uppercase">Tokens</span>
                  <span className="font-bold text-ink">{trajB.total_tokens.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-[10px] text-muted block uppercase">Cost</span>
                  <span className="font-bold text-ink">${trajB.total_cost_usd.toFixed(4)}</span>
                </div>
              </div>

              {/* Combined chronological event list */}
              <div className="space-y-2.5">
                {trajB.decisions.map((dec, idx) => (
                  <div key={`dec-${idx}`} className="rounded-md bg-canvas p-3.5 border border-hairline text-xs font-mono space-y-1.5 shadow-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-muted text-[11px]">Step {dec.step_index || idx + 1}</span>
                      <span className="text-xs font-bold text-teal-700 px-2 py-0.5 rounded bg-accent-teal/15 border border-accent-teal/30">
                        {dec.engine}
                      </span>
                    </div>
                    <p className="text-body-strong font-sans text-xs">
                      <strong>Decision:</strong> {dec.choice}
                    </p>
                    {dec.raw_reasoning && dec.raw_reasoning !== "{}" && (
                      <div className="rounded bg-surface-soft p-2 text-muted text-[11px] overflow-x-auto whitespace-pre-wrap font-mono">
                        {dec.raw_reasoning}
                      </div>
                    )}
                  </div>
                ))}

                {trajB.tool_events.map((te, idx) => (
                  <div key={`tool-${idx}`} className="rounded-md bg-canvas p-3 border border-hairline text-xs font-mono space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-teal-700">Tool: {te.tool_name}</span>
                      <span className="text-muted text-[11px]">{te.duration_ms}ms</span>
                    </div>
                    {te.output && (
                      <div className="rounded bg-surface-dark p-2 text-on-dark-soft text-[11px] max-h-28 overflow-y-auto whitespace-pre-wrap font-mono">
                        {te.output}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="mt-8 text-center text-xs text-muted">No trajectory recorded for {armB}</p>
          )}
        </div>
      </div>
    </div>
  );
};
