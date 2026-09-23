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

interface NavbarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  status: "idle" | "running" | "connected";
}

const TABS: { id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "overview", label: "Overview", icon: BarChart3 },
  { id: "live", label: "Live Run", icon: Terminal },
  { id: "architecture", label: "Architecture", icon: Layers },
  { id: "incidents", label: "Incidents (20)", icon: AlertTriangle },
  { id: "trajectories", label: "Trajectories", icon: GitCommit },
  { id: "latency", label: "Latency", icon: Clock },
  { id: "quality", label: "Quality & Success", icon: CheckCircle2 },
  { id: "safety", label: "Safety", icon: ShieldAlert },
  { id: "cost", label: "Cost & Scale", icon: DollarSign },
  { id: "tokens", label: "Tokens", icon: Cpu },
  { id: "jev", label: "Jev Analysis", icon: Zap },
  { id: "difficulty", label: "Difficulty Ladder", icon: TrendingUp },
  { id: "hybrid", label: "Hybrid Comparison", icon: Network },
  { id: "providers", label: "Provider Comparison", icon: Database },
  { id: "raw", label: "Raw Data", icon: Database },
  { id: "history", label: "Run History", icon: History },
  { id: "reports", label: "Scientific Report", icon: FileText },
];

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange, status }) => {
  return (
    <header className="sticky top-0 z-50 border-b border-surface-border bg-background/95 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center font-bold text-primary font-mono">
            K8S
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold tracking-tight text-white">Kubernetes AI Agent Benchmark</span>
              <span className="rounded bg-primary/20 px-2 py-0.5 text-xs font-mono font-medium text-primary border border-primary/30">
                v1.0.0-research
              </span>
            </div>
            <p className="text-xs text-slate-400">Jev + Sonnet 5 vs Sonnet 5 Alone Evaluation Platform</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className={`inline-block h-2.5 w-2.5 rounded-full ${
              status === "running" ? "bg-amber-400 animate-pulse" :
              status === "connected" ? "bg-emerald-400" : "bg-slate-500"
            }`} />
            <span className="text-slate-300 capitalize">{status}</span>
          </div>
        </div>
      </div>

      <nav className="flex overflow-x-auto border-t border-surface-border/50 px-4 py-1.5 scrollbar-thin">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center space-x-2 whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
                isActive
                  ? "bg-primary/10 text-primary border border-primary/30"
                  : "text-slate-400 hover:bg-surface-raised hover:text-slate-200"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
};
