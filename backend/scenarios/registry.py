"""
Scenario Registry and Ground Truth Validator.
Validates scenarios, decision graphs, and tools before benchmark execution.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from backend.models.schema import ScenarioMetadata
from backend.scenarios.definitions import get_all_scenarios, build_scenario_cluster_state
from backend.scenarios.graphs import ScenarioDecisionGraph
from backend.simulator.cluster import KubernetesSimulator
from backend.simulator.tools import TOOL_SCHEMAS


class ScenarioRegistry:
    """Central registry and validator for the 20 benchmark scenarios."""

    def __init__(self) -> None:
        self._scenarios: Dict[str, ScenarioMetadata] = {}
        self._graphs: Dict[str, ScenarioDecisionGraph] = {}
        self._load_and_validate_all()

    def _load_and_validate_all(self) -> None:
        raw_scenarios = get_all_scenarios()
        tool_names = {t["function"]["name"] for t in TOOL_SCHEMAS}

        # Validate that exactly 20 scenarios exist and difficulty increases monotonically
        if len(raw_scenarios) != 20:
            raise ValueError(f"Benchmark specification requires exactly 20 scenarios, found {len(raw_scenarios)}")

        for idx, sc in enumerate(raw_scenarios, start=1):
            if sc.difficulty != idx:
                raise ValueError(
                    f"Scenario {sc.id} has difficulty {sc.difficulty}, expected strictly monotonic {idx}"
                )

            # Section 176: Ground truth validation
            if not sc.hidden_root_cause:
                raise ValueError(f"Scenario {sc.id} missing hidden_root_cause")
            if not sc.unsafe_actions:
                raise ValueError(f"Scenario {sc.id} missing unsafe_actions")
            if not sc.correct_resolution_conditions:
                raise ValueError(f"Scenario {sc.id} missing correct_resolution_conditions")

            # Check that referenced tools exist in tool catalog
            for path in sc.valid_investigation_paths:
                for tool in path:
                    if tool not in tool_names and tool not in {"escalate", "handoff_to_frontier", "none_required"}:
                        raise ValueError(f"Scenario {sc.id} references non-existent tool '{tool}'")

            # Precalculate initial state hash
            initial_state = build_scenario_cluster_state(sc.id)
            sc.initial_state_sha256 = initial_state.calculate_sha256()

            self._scenarios[sc.id] = sc

            # Build decision graph for each scenario
            primary = sc.valid_investigation_paths[0] if sc.valid_investigation_paths else []
            alts = sc.valid_investigation_paths[1:] if len(sc.valid_investigation_paths) > 1 else []
            self._graphs[sc.id] = ScenarioDecisionGraph(
                scenario_id=sc.id,
                primary_valid_sequence=primary,
                allowed_alternative_sequences=alts,
                high_information_tools={primary[0]} if primary else set(),
                unsafe_actions=set(sc.unsafe_actions),
                rationale=sc.ground_truth_rationale,
            )

    def get(self, scenario_id: str) -> Optional[ScenarioMetadata]:
        return self._scenarios.get(scenario_id)

    def get_decision_graph(self, scenario_id: str) -> Optional[ScenarioDecisionGraph]:
        return self._graphs.get(scenario_id)

    def list_all(self) -> List[ScenarioMetadata]:
        return list(self._scenarios.values())

    def create_simulator(self, scenario_id: str) -> KubernetesSimulator:
        sc = self.get(scenario_id)
        if not sc:
            raise KeyError(f"Scenario {scenario_id} not registered")
        initial_state = build_scenario_cluster_state(scenario_id)
        return KubernetesSimulator(
            cluster_state=initial_state,
            scenario_id=sc.id,
            hidden_root_cause=sc.hidden_root_cause,
            unsafe_actions=sc.unsafe_actions,
            resolution_conditions=sc.correct_resolution_conditions,
        )


GLOBAL_SCENARIO_REGISTRY = ScenarioRegistry()
