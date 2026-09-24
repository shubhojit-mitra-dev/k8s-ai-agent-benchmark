import React, { useState, useEffect } from "react";
import { Navbar, TabId } from "./components/Navbar";
import { OverviewView } from "./views/OverviewView";
import { LiveRunnerView } from "./views/LiveRunnerView";
import { TrajectoriesView } from "./views/TrajectoriesView";
import { IncidentsView } from "./views/IncidentsView";
import { ArchitectureView } from "./views/ArchitectureView";
import { ScientificReportView } from "./views/ScientificReportView";
import { GenericMetricView } from "./views/GenericMetricView";
import { BenchmarkReport, ScenarioMetadata, Trajectory, RunInfo } from "./types";
import { 
  fetchHealth, 
  fetchScenarios, 
  fetchRuns, 
  fetchRunInfos,
  fetchRunReport, 
  fetchRunTrajectories, 
  subscribeToLiveEvents 
} from "./api/client";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [status, setStatus] = useState<"idle" | "running" | "connected">("idle");
  const [scenarios, setScenarios] = useState<ScenarioMetadata[]>([]);
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [trajectories, setTrajectories] = useState<Trajectory[]>([]);
  const [liveEvents, setLiveEvents] = useState<any[]>([]);
  const [runInfos, setRunInfos] = useState<RunInfo[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>("");

  // Initial data loading
  useEffect(() => {
    fetchHealth()
      .then(() => setStatus("connected"))
      .catch(() => setStatus("idle"));

    fetchScenarios().then(setScenarios).catch(console.error);

    loadRunCatalog();

    // Subscribe to SSE live stream
    const unsubscribe = subscribeToLiveEvents(
      (event) => {
        setLiveEvents((prev) => [event, ...prev.slice(0, 100)]);
        if (event.event === "run_started") setStatus("running");
        if (event.event === "run_completed") {
          setStatus("connected");
          loadRunCatalog();
        }
      },
      () => setStatus("idle")
    );

    return () => unsubscribe();
  }, []);

  const loadRunCatalog = async () => {
    try {
      const runs = await fetchRunInfos();
      setRunInfos(runs);
      if (runs.length > 0) {
        const initialRun = runs[0].run_id;
        setSelectedRunId(initialRun);
        loadRunData(initialRun);
      }
    } catch (err) {
      console.error("Could not load run catalog", err);
      // Fallback
      const runIds = await fetchRuns();
      if (runIds.length > 0) {
        setSelectedRunId(runIds[0]);
        loadRunData(runIds[0]);
      }
    }
  };

  const loadRunData = async (runId: string) => {
    try {
      const [rep, traj] = await Promise.all([
        fetchRunReport(runId),
        fetchRunTrajectories(runId),
      ]);
      setReport(rep);
      setTrajectories(traj);
    } catch (err) {
      console.error(`Could not load run data for ${runId}`, err);
    }
  };

  const handleSelectRun = (runId: string) => {
    setSelectedRunId(runId);
    loadRunData(runId);
  };

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col font-sans selection:bg-primary-soft selection:text-ink">
      <Navbar 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
        status={status}
        runInfos={runInfos}
        selectedRunId={selectedRunId}
        onSelectRun={handleSelectRun}
      />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {activeTab === "overview" && (
          <OverviewView report={report} onNavigateTab={(tab) => setActiveTab(tab as TabId)} />
        )}
        {activeTab === "live" && (
          <LiveRunnerView
            events={liveEvents}
            onClearEvents={() => setLiveEvents([])}
            onRefreshRun={loadRunCatalog}
          />
        )}
        {activeTab === "architecture" && <ArchitectureView />}
        {activeTab === "incidents" && <IncidentsView scenarios={scenarios} />}
        {activeTab === "trajectories" && <TrajectoriesView trajectories={trajectories} />}
        {activeTab === "reports" && <ScientificReportView report={report} />}
        
        {/* Metric Views */}
        {activeTab === "latency" && (
          <GenericMetricView
            title="Latency & Response Time Analysis"
            description="Comparative analysis of time-to-first-action, provider roundtrips, and total incident resolution time."
            report={report}
            metricKey="latency"
          />
        )}
        {activeTab === "quality" && (
          <GenericMetricView
            title="Decision Quality & Resolution Accuracy"
            description="Resolution convergence, post-convergence cluster stability, and optimal vs suboptimal graph path ratio."
            report={report}
            metricKey="quality"
          />
        )}
        {activeTab === "safety" && (
          <GenericMetricView
            title="Safety Invariant Evaluation"
            description="Prohibited action rate, blast radius violations, and unnecessary destructive mutating commands."
            report={report}
            metricKey="safety"
          />
        )}
        {activeTab === "cost" && (
          <GenericMetricView
            title="Cost Analysis & Enterprise Scale Projections"
            description="Unit economics per resolved incident and multi-tenant enterprise cluster cost extrapolations."
            report={report}
            metricKey="cost"
          />
        )}
        {activeTab === "tokens" && (
          <GenericMetricView
            title="Context Window & Token Consumption"
            description="Prompt tokens, completion tokens, and context window efficiency across decision iterations."
            report={report}
            metricKey="tokens"
          />
        )}
        {activeTab === "jev" && (
          <GenericMetricView
            title="Jev Specialized Model Evaluation"
            description="Decision contract validation (Choice, Noul, Score) and calibration against ground truth."
            report={report}
            metricKey="jev"
          />
        )}
        {activeTab === "difficulty" && (
          <GenericMetricView
            title="Difficulty Ladder Sensitivity"
            description="Evaluation performance partitioned across Easy, Medium, Hard, Very Hard, and Extreme incident tiers."
            report={report}
            metricKey="difficulty"
          />
        )}
        {activeTab === "hybrid" && (
          <GenericMetricView
            title="Hybrid Synergy & Hand-off Dynamics"
            description="Deep dive into Jev fast-path gating and escalation triggers to Sonnet 5."
            report={report}
            metricKey="hybrid"
          />
        )}
        {activeTab === "providers" && (
          <GenericMetricView
            title="Provider Performance: Cloudflare vs OpenRouter"
            description="Telemetry benchmarking between Cloudflare Workers AI edge execution and OpenRouter API gateways."
            report={report}
            metricKey="providers"
          />
        )}
        {activeTab === "raw" && (
          <GenericMetricView
            title="Raw Benchmark Data Repository"
            description="Tabular presentation of all recorded trajectories and metric telemetry."
            report={report}
            metricKey="raw"
          />
        )}
        {activeTab === "history" && (
          <GenericMetricView
            title="Historical Run Archive"
            description="Archive of longitudinal benchmark iterations."
            report={report}
            metricKey="history"
          />
        )}
      </main>
    </div>
  );
};
export default App;
