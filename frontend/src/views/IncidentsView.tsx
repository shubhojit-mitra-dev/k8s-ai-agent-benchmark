import React, { useState } from "react";
import { ScenarioMetadata } from "../types";
import { AlertTriangle, ShieldAlert, CheckCircle2, Search, Wrench, Layers } from "lucide-react";

interface IncidentsViewProps {
  scenarios: ScenarioMetadata[];
}

export const IncidentsView: React.FC<IncidentsViewProps> = ({ scenarios }) => {
  const [selectedId, setSelectedId] = useState<string>(scenarios[0]?.id || scenarios[0]?.scenario_id || "K8S-001");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("ALL");

  const getDifficultyLabel = (diff: number | string): string => {
    if (typeof diff === "number") {
      if (diff <= 4) return "EASY";
      if (diff <= 8) return "MEDIUM";
      if (diff <= 12) return "HARD";
      if (diff <= 16) return "VERY_HARD";
      return "EXTREME";
    }
    return String(diff);
  };

  const getDifficultyBadge = (diff: number | string) => {
    const label = getDifficultyLabel(diff);
    switch (label) {
      case "EASY":
        return "bg-success/10 text-success border-success/30";
      case "MEDIUM":
        return "bg-accent-teal/15 text-teal-700 border-accent-teal/30";
      case "HARD":
        return "bg-accent-amber/20 text-amber-800 border-accent-amber/40";
      case "VERY_HARD":
        return "bg-warning/20 text-amber-900 border-warning/40";
      case "EXTREME":
        return "bg-error/15 text-error border-error/30";
      default:
        return "bg-surface-soft text-muted border-hairline";
    }
  };

  const filteredScenarios = scenarios.filter((sc) => {
    const id = sc.id || sc.scenario_id || "";
    const title = sc.title || sc.name || "";
    const category = sc.category || "";
    const matchesSearch =
      id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      category.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;
    if (selectedDifficulty === "ALL") return true;
    return getDifficultyLabel(sc.difficulty) === selectedDifficulty;
  });

  const selectedScenario =
    scenarios.find((sc) => (sc.id || sc.scenario_id) === selectedId) || scenarios[0] || null;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-lg border border-hairline bg-surface-card p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="rounded-pill bg-primary/10 text-primary text-xs font-mono font-bold px-2.5 py-0.5 border border-primary/20">
                BENCHMARK SPECIFICATION
              </span>
              <span className="text-xs text-muted font-mono">{scenarios.length} Standardized Incidents</span>
            </div>
            <h2 className="mt-2 text-2xl font-serif font-normal text-ink">
              20-Incident Monotonic Difficulty Ladder
            </h2>
            <p className="mt-1 text-xs text-body leading-relaxed max-w-3xl">
              Deterministic, reproducible Kubernetes failure scenarios spanning crash loops, admission webhook timeouts,
              cascading out-of-memory cascades, split-brain leader elections, and multi-tenant quota deadlocks.
            </p>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-2 shrink-0">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-soft" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search incidents..."
                className="rounded-md border border-hairline bg-canvas pl-9 pr-3 py-1.5 text-xs text-ink placeholder:text-muted-soft focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary w-48"
              />
            </div>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="rounded-md border border-hairline bg-canvas px-3 py-1.5 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            >
              <option value="ALL">All Tiers (1-20)</option>
              <option value="EASY">Easy (1-4)</option>
              <option value="MEDIUM">Medium (5-8)</option>
              <option value="HARD">Hard (9-12)</option>
              <option value="VERY_HARD">Very Hard (13-16)</option>
              <option value="EXTREME">Extreme (17-20)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left: Incident Selector List */}
        <div className="lg:col-span-5 rounded-lg border border-hairline bg-surface-card p-4 max-h-[760px] overflow-y-auto space-y-2">
          {filteredScenarios.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted">No incidents match search criteria.</div>
          ) : (
            filteredScenarios.map((sc) => {
              const id = sc.id || sc.scenario_id || "K8S";
              const title = sc.title || sc.name || "Incident Scenario";
              const isSelected = (selectedScenario?.id || selectedScenario?.scenario_id) === id;
              const diffNum = typeof sc.difficulty === "number" ? sc.difficulty : 1;
              const diffLabel = getDifficultyLabel(sc.difficulty);

              return (
                <button
                  key={id}
                  onClick={() => setSelectedId(id)}
                  className={`w-full text-left rounded-md p-3.5 border transition-all ${
                    isSelected
                      ? "bg-canvas border-primary shadow-sm"
                      : "bg-surface-soft/60 border-hairline-soft hover:bg-canvas hover:border-hairline"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-primary">{id}</span>
                      <span className="text-[10px] font-mono text-muted">Tier {diffNum}</span>
                    </div>
                    <span className={`rounded-pill px-2 py-0.5 text-[10px] font-mono font-bold border ${getDifficultyBadge(sc.difficulty)}`}>
                      {diffLabel}
                    </span>
                  </div>
                  <h4 className="mt-1.5 text-xs font-medium text-ink line-clamp-1">{title}</h4>
                  {sc.category && (
                    <div className="mt-1 text-[11px] text-muted font-sans flex items-center space-x-1">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary/60"></span>
                      <span>{sc.category}</span>
                    </div>
                  )}
                </button>
              );
            })
          )}
        </div>

        {/* Right: Selected Incident Specification Details */}
        <div className="lg:col-span-7 rounded-lg border border-hairline bg-surface-card p-6">
          {selectedScenario ? (
            <div className="space-y-6">
              {/* Incident Header */}
              <div className="border-b border-hairline pb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-sm font-bold text-primary">
                      {selectedScenario.id || selectedScenario.scenario_id}
                    </span>
                    <span
                      className={`rounded-pill px-2.5 py-0.5 text-xs font-mono font-bold border ${getDifficultyBadge(
                        selectedScenario.difficulty
                      )}`}
                    >
                      {getDifficultyLabel(selectedScenario.difficulty)} (Tier {selectedScenario.difficulty})
                    </span>
                    {selectedScenario.category && (
                      <span className="rounded-pill bg-surface-soft px-2.5 py-0.5 text-xs font-mono text-body border border-hairline">
                        {selectedScenario.category}
                      </span>
                    )}
                  </div>
                </div>
                <h3 className="mt-2 text-xl font-serif font-medium text-ink">
                  {selectedScenario.title || selectedScenario.name}
                </h3>
              </div>

              {/* Initial Telemetry Alert */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted font-sans flex items-center space-x-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 text-warning" />
                  <span>Initial Alert &amp; Telemetry Signal</span>
                </h4>
                <div className="mt-2 rounded-md bg-surface-dark p-4 text-xs font-mono text-on-dark border border-surface-dark-soft overflow-x-auto">
                  {selectedScenario.initial_alert ? (
                    typeof selectedScenario.initial_alert === "object" ? (
                      <pre className="text-xs font-mono text-on-dark-soft leading-relaxed whitespace-pre-wrap">
                        {JSON.stringify(selectedScenario.initial_alert, null, 2)}
                      </pre>
                    ) : (
                      <p>{String(selectedScenario.initial_alert)}</p>
                    )
                  ) : (
                    <p className="text-muted-soft">No initial alert payload registered.</p>
                  )}
                </div>
              </div>

              {/* Ground-Truth Verified Root Cause */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted font-sans flex items-center space-x-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                  <span>Verified Ground-Truth Root Cause</span>
                </h4>
                <div className="mt-2 rounded-md bg-canvas p-4 text-xs font-mono leading-relaxed text-body-strong border border-hairline shadow-sm">
                  {selectedScenario.hidden_root_cause || selectedScenario.root_cause || "Unspecified root cause"}
                </div>
              </div>

              {/* Ground Truth Rationale & Safe Resolution Path */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted font-sans flex items-center space-x-1.5">
                  <Layers className="h-3.5 w-3.5 text-primary" />
                  <span>Ground-Truth Diagnostic Rationale</span>
                </h4>
                <div className="mt-2 rounded-md bg-canvas p-4 text-xs leading-relaxed text-body border border-hairline">
                  {selectedScenario.ground_truth_rationale ||
                    selectedScenario.safe_resolution_description ||
                    "Ground truth rationale documented in benchmark specification."}
                </div>
              </div>

              {/* Prohibited / Unsafe Invariant Violations */}
              {selectedScenario.unsafe_actions && selectedScenario.unsafe_actions.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-error font-sans flex items-center space-x-1.5">
                    <ShieldAlert className="h-3.5 w-3.5 text-error" />
                    <span>Safety Invariant: Prohibited Destructive Actions</span>
                  </h4>
                  <div className="mt-2 rounded-md bg-error/5 p-4 border border-error/20">
                    <ul className="space-y-1.5 text-xs font-mono text-error">
                      {selectedScenario.unsafe_actions.map((act, i) => (
                        <li key={i} className="flex items-center space-x-2">
                          <span className="h-1.5 w-1.5 rounded-full bg-error shrink-0"></span>
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Expected Tool Investigation Sequences */}
              {selectedScenario.valid_investigation_paths && selectedScenario.valid_investigation_paths.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted font-sans flex items-center space-x-1.5">
                    <Wrench className="h-3.5 w-3.5 text-muted-soft" />
                    <span>Expected Diagnostic Tool Sequences</span>
                  </h4>
                  <div className="mt-2 space-y-2">
                    {selectedScenario.valid_investigation_paths.map((path, idx) => (
                      <div key={idx} className="flex flex-wrap items-center gap-1.5 text-xs font-mono bg-canvas p-2.5 rounded-md border border-hairline">
                        <span className="text-muted font-bold mr-1">Path {idx + 1}:</span>
                        {path.map((tool, tIdx) => (
                          <React.Fragment key={tIdx}>
                            <span className="rounded bg-surface-soft px-2 py-0.5 text-body-strong font-semibold border border-hairline">
                              {tool}
                            </span>
                            {tIdx < path.length - 1 && <span className="text-muted-soft">&rarr;</span>}
                          </React.Fragment>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex h-96 items-center justify-center text-xs text-muted">
              Select an incident from the monotonic ladder to inspect ground-truth specification.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
