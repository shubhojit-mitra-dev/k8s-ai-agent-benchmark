import React from "react";
import { 
  BarChart3, 
  Terminal, 
  Layers, 
  AlertTriangle, 
  GitCommit, 
  Clock, 
  CheckCircle2, 
  ShieldAlert, 
  DollarSign, 
  Cpu, 
  Zap, 
  TrendingUp, 
  Network, 
  Database, 
  History, 
  FileText 
} from "lucide-react";

export type TabId = 
  | "overview"
  | "live"
  | "architecture"
  | "incidents"
  | "trajectories"
  | "latency"
  | "quality"
  | "safety"
  | "cost"
  | "tokens"
  | "jev"
  | "difficulty"
  | "hybrid"
  | "providers"
  | "raw"
  | "history"
  | "reports";

import { RunInfo } from "../types";

interface NavbarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  status: "idle" | "running" | "connected";
  runIds?: string[];
  runInfos?: RunInfo[];
  selectedRunId?: string;
  onSelectRun?: (runId: string) => void;
}

const TABS: { id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "overview", label: "Overview", icon: BarChart3 },
  { id: "incidents", label: "Incidents (20)", icon: AlertTriangle },
  { id: "trajectories", label: "Trajectories", icon: GitCommit },
  { id: "reports", label: "Scientific Report", icon: FileText },
  { id: "latency", label: "Latency", icon: Clock },
  { id: "quality", label: "Quality & Success", icon: CheckCircle2 },
  { id: "safety", label: "Safety", icon: ShieldAlert },
  { id: "cost", label: "Cost & Scale", icon: DollarSign },
  { id: "tokens", label: "Tokens", icon: Cpu },
  { id: "jev", label: "Jev Analysis", icon: Zap },
  { id: "difficulty", label: "Difficulty Ladder", icon: TrendingUp },
  { id: "hybrid", label: "Hybrid Comparison", icon: Network },
  { id: "providers", label: "Provider Comparison", icon: Database },
  { id: "architecture", label: "Architecture", icon: Layers },
  { id: "live", label: "Live Console", icon: Terminal },
  { id: "raw", label: "Raw Data", icon: Database },
  { id: "history", label: "Run History", icon: History },
];

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  status,
  runIds = [],
  runInfos = [],
  selectedRunId = "",
  onSelectRun,
}) => {
  const displayRuns = runInfos.length > 0 
    ? runInfos.map(r => ({ id: r.run_id, label: `Run ${r.run_id} (${r.mode || "live"}, ${r.total_incidents || 2} incidents)` }))
    : runIds.map(id => ({ 
        id, 
        label: id.includes("1790253930")
          ? `Run ${id} (Live OpenRouter Sonnet 5 + Jev)`
          : id.includes("1790199162")
          ? `Run ${id} (4-Arm Cloudflare + OpenRouter)`
          : `Run ${id}` 
      }));

  return (
    <header className="sticky top-0 z-50 border-b border-hairline bg-canvas/95 backdrop-blur-md">
      {/* Top Brand & Run Selector Bar */}
      <div className="flex h-16 items-center justify-between px-6 border-b border-hairline-soft">
        <div className="flex items-center space-x-3">
          {/* Anthropic Radial Spike Glyph */}
          <div className="h-8 w-8 rounded-lg bg-surface-dark flex items-center justify-center text-on-dark shrink-0 shadow-sm">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M12 2L13.8 8.8L20.5 7L15.7 12L20.5 17L13.8 15.2L12 22L10.2 15.2L3.5 17L8.3 12L3.5 7L10.2 8.8Z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="font-serif text-lg font-medium tracking-tight text-ink">
                Kubernetes AI Agent Benchmark
              </span>
              <span className="rounded-pill bg-surface-card px-2.5 py-0.5 text-xs font-mono font-medium text-body-strong border border-hairline">
                v1.0.0-research
              </span>
            </div>
            <p className="text-xs text-muted font-sans">
              Autonomous Incident Response: Jev + Claude Sonnet 5 vs Claude Sonnet 5 Alone
            </p>
          </div>
        </div>

        {/* Right side: Run Selector & System Status */}
        <div className="flex items-center space-x-4">
          {displayRuns.length > 0 && (
            <div className="flex items-center space-x-2 text-xs">
              <label htmlFor="run-select" className="text-muted font-medium">
                Active Run:
              </label>
              <select
                id="run-select"
                value={selectedRunId}
                onChange={(e) => onSelectRun && onSelectRun(e.target.value)}
                className="rounded-md border border-hairline bg-surface-card px-3 py-1.5 font-mono text-xs text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              >
                {displayRuns.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex items-center space-x-2 text-xs font-mono bg-surface-card px-3 py-1.5 rounded-md border border-hairline">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                status === "running"
                  ? "bg-warning animate-pulse"
                  : status === "connected"
                  ? "bg-success"
                  : "bg-muted-soft"
              }`}
            />
            <span className="text-body-strong capitalize">{status}</span>
          </div>
        </div>
      </div>

      {/* Sub-nav: Editorial Category Tabs */}
      <nav className="flex overflow-x-auto px-6 py-2 scrollbar-none space-x-1.5 bg-canvas">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center space-x-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                isActive
                  ? "bg-surface-card text-ink font-semibold border border-hairline shadow-sm"
                  : "text-muted hover:bg-surface-soft hover:text-ink border border-transparent"
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${isActive ? "text-primary" : "text-muted-soft"}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
};
