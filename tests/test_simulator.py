"""Test suite for deterministic Kubernetes simulator state machine and action validation."""

from backend.scenarios.registry import GLOBAL_SCENARIO_REGISTRY
from backend.models.schema import ActionRisk


def test_cluster_initialization():
    sim = GLOBAL_SCENARIO_REGISTRY.create_simulator("K8S-001")
    assert sim.scenario_id == "K8S-001"
    resolved = sim.evaluate_resolution_state()
    assert not resolved
    assert sim.initial_state_hash is not None


def test_prohibited_action_detection():
    sim = GLOBAL_SCENARIO_REGISTRY.create_simulator("K8S-001")
    # drain_node is high-risk/critical in KubernetesSimulator
    success, reason, risk = sim.execute_action("drain_node", {"node_name": "node-1"})
    assert risk == ActionRisk.CRITICAL


def test_safe_mutation_execution():
    sim = GLOBAL_SCENARIO_REGISTRY.create_simulator("K8S-001")
    success, reason, risk = sim.execute_action("restart_deployment", {"deployment_name": "payments-api", "namespace": "payments"})
    assert risk in [ActionRisk.LOW, ActionRisk.MEDIUM]
    assert success
