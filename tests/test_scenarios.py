"""Test suite for scenario definitions, causal graphs, and registry validation."""

from backend.scenarios.registry import GLOBAL_SCENARIO_REGISTRY
from backend.scenarios.definitions import get_all_scenarios


def test_scenario_count():
    assert len(get_all_scenarios()) == 20


def test_registry_initialization():
    scenarios = GLOBAL_SCENARIO_REGISTRY.list_all()
    assert len(scenarios) == 20


def test_monotonic_difficulty_ladder():
    scenarios = GLOBAL_SCENARIO_REGISTRY.list_all()
    for idx, sc in enumerate(scenarios, start=1):
        assert sc.id == f"K8S-{idx:03d}"
        assert sc.difficulty == idx


def test_decision_graphs_validity():
    for sc in GLOBAL_SCENARIO_REGISTRY.list_all():
        graph = GLOBAL_SCENARIO_REGISTRY.get_decision_graph(sc.id)
        assert graph is not None
        assert graph.scenario_id == sc.id
        assert len(graph.primary_valid_sequence) > 0
