import React, { useState } from "react";
import { startBenchmarkRun } from "../api/client";
import { Play, Pause, RefreshCw, Terminal, CheckCircle2 } from "lucide-react";

interface LiveRunnerViewProps {
  events: any[];
  onClearEvents: () => void;
  onRefreshRun: () => void;
}

export const LiveRunnerView: React.FC<LiveRunnerViewProps> = ({
  events,
  onClearEvents,
  onRefreshRun,
}) => {
  const [mode, setMode] = useState<string>("smoke");
  const [forceMock, setForceMock] = useState<boolean>(true);
  const [parallel, setParallel] = useState<boolean>(false);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);

  const handleStart = async () => {
    try {
      setIsRunning(true);
      onClearEvents();
      const res = await startBenchmarkRun({ mode, forceMock, parallel });
      setCurrentRunId(res.run_id);
    } catch (err: any) {
      alert(`Error starting benchmark: ${err.message}`);
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-surface-border bg-surface p-5">
        <div>
          <h2 className="text-base font-bold text-white">Live Benchmark Execution Controller</h2>
          <p className="text-xs text-slate-400">Launch and stream autonomous incident response scenarios in real-time</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2">
            <label className="text-xs font-mono text-slate-400">Mode:</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              disabled={isRunning}
              className="rounded-lg border border-surface-border bg-background px-3 py-1.5 text-xs font-mono text-slate-200 focus:border-primary focus:outline-none"
            >
              <option value="smoke">Smoke (2 incidents)</option>
              <option value="quick">Quick (5 incidents)</option>
              <option value="ladder">Ladder (10 incidents)</option>
              <option value="full">Full (20 incidents)</option>
            </select>
          </div>

          <label className="flex items-center space-x-2 text-xs font-mono text-slate-300">
            <input
              type="checkbox"
              checked={forceMock}
              onChange={(e) => setForceMock(e.target.checked)}
              disabled={isRunning}
              className="rounded border-surface-border bg-background text-primary focus:ring-0"
            />
            <span>Deterministic Mock</span>
          </label>

          <label className="flex items-center space-x-2 text-xs font-mono text-slate-300">
            <input
              type="checkbox"
              checked={parallel}
              onChange={(e) => setParallel(e.target.checked)}
              disabled={isRunning}
              className="rounded border-surface-border bg-background text-primary focus:ring-0"
            />
            <span>Parallel Arms</span>
          </label>

          <button
            onClick={handleStart}
            disabled={isRunning}
            className={`flex items-center space-x-1.5 rounded-lg px-4 py-1.5 text-xs font-bold transition ${
              isRunning
                ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                : "bg-primary text-slate-900 hover:bg-primary/90"
            }`}
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            <span>{isRunning ? "Running..." : "Start Benchmark"}</span>
          </button>

          <button
            onClick={onRefreshRun}
            className="flex items-center space-x-1.5 rounded-lg border border-surface-border bg-surface-raised px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Reload Latest</span>
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-surface-border bg-surface p-5">
        <div className="flex items-center justify-between pb-3 border-b border-surface-border">
          <div className="flex items-center space-x-2 font-mono text-xs">
            <Terminal className="h-4 w-4 text-primary" />
            <span className="font-semibold text-slate-200">Execution Stream Event Log</span>
            {currentRunId && (
              <span className="rounded bg-surface-raised px-2 py-0.5 text-slate-400">
                Run ID: {currentRunId}
              </span>
            )}
          </div>
          <span className="text-xs text-slate-500 font-mono">{events.length} events logged</span>
        </div>

        <div className="mt-4 h-96 overflow-y-auto rounded-lg bg-background p-4 font-mono text-xs space-y-2 border border-surface-border/50">
          {events.length === 0 ? (
            <div className="flex h-full items-center justify-center text-slate-500">
              Awaiting run initialization. Click "Start Benchmark" to stream live decisions.
            </div>
          ) : (
            events.map((ev, idx) => (
              <div key={idx} className="flex items-start space-x-2">
                <span className="text-slate-500 shrink-0">
                  {new Date(ev.timestamp ? ev.timestamp * 1000 : Date.now()).toLocaleTimeString()}
                </span>
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 ${
                  ev.event === "decision" ? "bg-secondary/20 text-secondary border border-secondary/40" :
                  ev.event === "tool_call" ? "bg-primary/20 text-primary border border-primary/40" :
                  ev.event === "scenario_completed" ? "bg-accent/20 text-accent border border-accent/40" :
                  "bg-slate-800 text-slate-300"
                }`}>
                  {ev.event}
                </span>
                <span className="text-slate-300 break-all">
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
