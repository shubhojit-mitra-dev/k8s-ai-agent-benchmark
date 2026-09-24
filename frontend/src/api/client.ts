import { BenchmarkReport, ScenarioMetadata, Trajectory, RunInfo } from "../types";

const API_BASE = "";

export async function fetchHealth(): Promise<{ status: string; timestamp: number; scenarios_loaded: number }> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchScenarios(): Promise<ScenarioMetadata[]> {
  const res = await fetch(`${API_BASE}/api/scenarios`);
  if (!res.ok) throw new Error(`Failed to fetch scenarios: ${res.statusText}`);
  const data: ScenarioMetadata[] = await res.json();
  return data.map((sc) => ({
    ...sc,
    scenario_id: sc.scenario_id || sc.id,
    name: sc.name || sc.title,
    description: sc.description || (sc.initial_alert ? JSON.stringify(sc.initial_alert, null, 2) : ""),
    root_cause: sc.root_cause || sc.hidden_root_cause,
    safe_resolution_description: sc.safe_resolution_description || sc.ground_truth_rationale,
  }));
}

export async function fetchRuns(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/runs`);
  if (!res.ok) throw new Error(`Failed to fetch runs: ${res.statusText}`);
  const data = await res.json();
  if (Array.isArray(data) && data.length > 0 && typeof data[0] === "object" && data[0].run_id) {
    return data.map((item: any) => item.run_id);
  }
  return data;
}

export async function fetchRunInfos(): Promise<RunInfo[]> {
  const res = await fetch(`${API_BASE}/api/runs`);
  if (!res.ok) throw new Error(`Failed to fetch runs: ${res.statusText}`);
  const data = await res.json();
  if (Array.isArray(data)) {
    return data;
  }
  return [];
}

export async function fetchRunReport(runId: string): Promise<BenchmarkReport> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/report`);
  if (!res.ok) throw new Error(`Failed to fetch report for run ${runId}: ${res.statusText}`);
  return res.json();
}

export async function fetchRunTrajectories(runId: string): Promise<Trajectory[]> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/trajectories`);
  if (!res.ok) throw new Error(`Failed to fetch trajectories for run ${runId}: ${res.statusText}`);
  return res.json();
}

export async function startBenchmarkRun(params: {
  mode: string;
  forceMock: boolean;
  parallel: boolean;
}): Promise<{ status: string; run_id: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/runs/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mode: params.mode,
      force_mock: params.forceMock,
      parallel: params.parallel,
    }),
  });
  if (!res.ok) throw new Error(`Failed to start benchmark: ${res.statusText}`);
  return res.json();
}

export function subscribeToLiveEvents(onEvent: (event: any) => void, onError?: (err: any) => void): () => void {
  const eventSource = new EventSource(`${API_BASE}/api/events`);
  
  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onEvent(data);
    } catch (err) {
      console.error("Error parsing SSE event data", err);
    }
  };

  eventSource.onerror = (err) => {
    if (onError) onError(err);
  };

  return () => {
    eventSource.close();
  };
}
