"""Test suite for blinded evaluation, graph path checking, and scoring."""

import asyncio
from backend.agents import create_agent_for_arm
from backend.scenarios.registry import GLOBAL_SCENARIO_REGISTRY
from backend.models.schema import PrimaryArm
from backend.config import BenchmarkSettings
from backend.evaluation.blind import BlindedEvaluatorContext
from backend.evaluation.evaluator import TrajectoryEvaluator


def test_blinded_context():
    context = BlindedEvaluatorContext()
    blind_id = context.arm_to_blind_map[PrimaryArm.CF_SONNET.value]
    assert blind_id.startswith("ARM-")
    assert context.unblind_arm_id(blind_id) == PrimaryArm.CF_SONNET.value


def test_trajectory_evaluator():
    scenario = GLOBAL_SCENARIO_REGISTRY.get("K8S-001")
    assert scenario is not None
    sim = GLOBAL_SCENARIO_REGISTRY.create_simulator("K8S-001")
    settings = BenchmarkSettings()
    agent = create_agent_for_arm(
        run_id="test-run-eval",
        arm=PrimaryArm.CF_SONNET.value,
        incident_id="K8S-001",
        difficulty=scenario.difficulty,
        simulator=sim,
        settings=settings,
        force_mock=True,
    )
    traj = asyncio.run(agent.run(initial_alert=scenario.initial_alert))

    eval_result = TrajectoryEvaluator.evaluate(traj)

    assert eval_result.incident_id == "K8S-001"
    assert eval_result.arm == PrimaryArm.CF_SONNET.value
    assert isinstance(eval_result.safe, bool)
