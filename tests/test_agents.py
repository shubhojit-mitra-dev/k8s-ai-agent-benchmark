"""Test suite for agent orchestration and resolution loop."""

import asyncio
from backend.agents import create_agent_for_arm
from backend.scenarios.registry import GLOBAL_SCENARIO_REGISTRY
from backend.models.schema import PrimaryArm
from backend.config import BenchmarkSettings


def test_baseline_sonnet_run():
    scenario = GLOBAL_SCENARIO_REGISTRY.get("K8S-001")
    assert scenario is not None
    sim = GLOBAL_SCENARIO_REGISTRY.create_simulator("K8S-001")
    settings = BenchmarkSettings()
    agent = create_agent_for_arm(
        run_id="test-run-1",
        arm=PrimaryArm.CF_SONNET.value,
        incident_id="K8S-001",
        difficulty=scenario.difficulty,
        simulator=sim,
        settings=settings,
        force_mock=True,
    )
    traj = asyncio.run(agent.run(initial_alert=scenario.initial_alert))

    assert traj.arm == PrimaryArm.CF_SONNET.value
    assert traj.incident_id == "K8S-001"
    assert traj.tool_calls > 0
    assert traj.latency.total_latency_ms > 0


def test_hybrid_jev_sonnet_run():
    scenario = GLOBAL_SCENARIO_REGISTRY.get("K8S-001")
    assert scenario is not None
    sim = GLOBAL_SCENARIO_REGISTRY.create_simulator("K8S-001")
    settings = BenchmarkSettings()
    agent = create_agent_for_arm(
        run_id="test-run-2",
        arm=PrimaryArm.CF_JEV_SONNET.value,
        incident_id="K8S-001",
        difficulty=scenario.difficulty,
        simulator=sim,
        settings=settings,
        force_mock=True,
    )
    traj = asyncio.run(agent.run(initial_alert=scenario.initial_alert))

    assert traj.arm == PrimaryArm.CF_JEV_SONNET.value
    assert traj.incident_id == "K8S-001"
    assert traj.tool_calls > 0
    assert traj.latency.total_latency_ms > 0
