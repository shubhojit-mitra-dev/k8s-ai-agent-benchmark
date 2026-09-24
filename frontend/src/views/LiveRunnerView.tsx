import React, { useState, useEffect } from "react";
import { startBenchmarkRun } from "../api/client";
import { Play, RefreshCw, Terminal, Activity, ShieldAlert, Cpu } from "lucide-react";

interface LiveRunnerViewProps {
  events: any[];
  onClearEvents: () => void;
  onRefreshRun: () => void;
  status: "idle" | "running" | "connected";
}

export const LiveRunnerView: React.FC<LiveRunnerViewProps> = ({
  events,
  onClearEvents,
  onRefreshRun,
  status,
}) => {
  const [mode, setMode] = useState<string>("smoke");
  const [forceMock, setForceMock] = useState<boolean>(true);
  const [parallel, setParallel] = useState<boolean>(false);
  const [localRunning, setLocalRunning] = useState<boolean>(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);

  const isRunning = localRunning || status === "running";

  useEffect(() => {
    if (status !== "running") {
      setLocalRunning(false);
    }
  }, [status]);

  const handleStart = async () => {
    try {
      setLocalRunning(true);
      onClearEvents();
      const res = await startBenchmarkRun({ mode, forceMock, parallel });
      setCurrentRunId(res.run_id);
    } catch (err: any) {
      alert(`Error starting benchmark: ${err.message}`);
      setLocalRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-hairline bg-surface-card p-6 shadow-warm-sm flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-primary font-semibold">
            <Activity className="h-4 w-4" />
            <span>Interactive Experiment Controller</span>
          </div>
          <h2 className="mt-1 text-2xl font-serif font-bold text-ink">Live Benchmark Execution Stream</h2>
          <p className="mt-1 text-xs text-body">
            Execute real-time autonomous incident response evaluation across all comparative arms.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2">
            <label className="text-xs font-mono font-medium text-body">Mode:</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              disabled={isRunning}
              className="rounded-lg border border-hairline bg-canvas px-3 py-1.5 text-xs font-mono text-ink focus:border-primary focus:outline-none"
            >
              <option value="smoke">Smoke (2 incidents)</option>
              <option value="quick">Quick (5 incidents)</option>
              <option value="ladder">Ladder (10 incidents)</option>
              <option value="full">Full (20 incidents)</option>
            </select>
          </div>

          <label className="flex items-center space-x-2 text-xs font-mono text-body cursor-pointer select-none">
            <input
              type="checkbox"
              checked={forceMock}
              onChange={(e) => setForceMock(e.target.checked)}
              disabled={isRunning}
              className="rounded border-hairline text-primary focus:ring-0"
            />
            <span>Deterministic Sandbox</span>
          </label>

          <label className="flex items-center space-x-2 text-xs font-mono text-body cursor-pointer select-none">
            <input
              type="checkbox"
              checked={parallel}
              onChange={(e) => setParallel(e.target.checked)}
              disabled={isRunning}
              className="rounded border-hairline text-primary focus:ring-0"
            />
            <span>Parallel Arms</span>
          </label>

          <button
            onClick={handleStart}
            disabled={isRunning}
            className={`flex items-center space-x-1.5 rounded-lg px-4 py-2 text-xs font-bold transition shadow-warm-sm ${
              isRunning
                ? "bg-stone-300 text-stone-500 cursor-not-allowed"
                : "bg-primary text-white hover:bg-primary-dark"
            }`}
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            <span>{isRunning ? "Executing..." : "Start Benchmark"}</span>
          </button>

          <button
            onClick={onRefreshRun}
            className="flex items-center space-x-1.5 rounded-lg border border-hairline bg-surface px-3 py-2 text-xs font-medium text-ink hover:bg-surface-raised transition"
          >
            <RefreshCw className="h-3.5 w-3.5 text-body" />
            <span>Reload Latest</span>
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-hairline bg-surface-card p-6 shadow-warm-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-hairline">
          <div className="flex items-center space-x-2 font-mono text-xs">
            <Terminal className="h-4 w-4 text-primary" />
            <span className="font-semibold text-ink">Live Decision Stream &amp; Execution Telemetry</span>
            {currentRunId && (
              <span className="rounded bg-canvas border border-hairline px-2 py-0.5 text-body font-mono">
                Run ID: {currentRunId}
              </span>
            )}
          </div>
          <span className="text-xs text-body font-mono">{events.length} events logged</span>
        </div>

        <div className="h-96 overflow-y-auto rounded-lg bg-surface-dark p-4 font-mono text-xs space-y-2.5 border border-surface-border">
          {events.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-slate-400 space-y-2">
              <Cpu className="h-6 w-6 text-slate-500" />
              <p>Awaiting run initialization. Click "Start Benchmark" to stream live decisions.</p>
            </div>
          ) : (
            events.map((ev, idx) => (
              <div key={idx} className="flex items-start space-x-2.5 text-slate-200">
                <span className="text-slate-500 shrink-0 select-none">
                  {new Date(ev.timestamp ? ev.timestamp * 1000 : Date.now()).toLocaleTimeString()}
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider shrink-0 ${
                  ev.event === "decision" ? "bg-amber-500/20 text-amber-300 border border-amber-500/40" :
                  ev.event === "tool_call" ? "bg-primary-soft text-primary border border-primary/40" :
                  ev.event === "scenario_completed" ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40" :
                  "bg-slate-800 text-slate-300 border border-slate-700"
                }`}>
                  {ev.event}
                </span>
                <span className="break-all font-mono text-[11px] leading-relaxed">
                  {typeof ev.data === "string" ? ev.data : JSON.stringify(ev.data)}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
