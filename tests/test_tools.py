"""Test suite for simulator read-only tools and kubectl command simulation."""

from backend.scenarios.registry import GLOBAL_SCENARIO_REGISTRY
from backend.simulator.tools import ToolExecutionEngine, TOOL_SCHEMAS
from backend.models.schema import ActionRisk


def test_tool_registry_schemas():
    assert len(TOOL_SCHEMAS) >= 30


def test_tool_execution_read_only():
    sim = GLOBAL_SCENARIO_REGISTRY.create_simulator("K8S-001")
    output, is_mut, risk, gain = ToolExecutionEngine.execute(sim, "list_pods", {"namespace": "payments"})
    assert risk == ActionRisk.READ_ONLY
    assert not is_mut
    assert len(output) > 0


def test_tool_execution_logs():
    sim = GLOBAL_SCENARIO_REGISTRY.create_simulator("K8S-001")
    output, is_mut, risk, gain = ToolExecutionEngine.execute(sim, "get_pod_logs", {"namespace": "payments", "pod_name": "test"})
    assert risk == ActionRisk.READ_ONLY
    assert len(output) > 0
