"""
Scenarios package containing the 20 benchmark Kubernetes incident definitions.
"""

from backend.scenarios.registry import ScenarioRegistry, GLOBAL_SCENARIO_REGISTRY
from backend.scenarios.definitions import get_all_scenarios, build_scenario_cluster_state
from backend.scenarios.graphs import ScenarioDecisionGraph

__all__ = [
    "ScenarioRegistry",
    "GLOBAL_SCENARIO_REGISTRY",
    "get_all_scenarios",
    "build_scenario_cluster_state",
    "ScenarioDecisionGraph",
]
