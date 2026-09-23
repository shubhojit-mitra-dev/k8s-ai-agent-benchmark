"""Test suite for metrics aggregation, statistical hypothesis tests, and scale projections."""

from backend.evaluation.metrics import aggregate_benchmark_results
from backend.evaluation.hypothesis import HypothesisEvaluator
from backend.models.schema import PrimaryArm, Trajectory, EvaluationResult, LatencyResult, CostResult


def test_metric_aggregation_and_hypothesis():
    trajectories = [
        Trajectory(
            run_id="run-1",
            incident_id="K8S-001",
            arm=PrimaryArm.CF_SONNET.value,
            difficulty=1,
            latency=LatencyResult(total_latency_ms=4000.0),
            cost=CostResult(total_cost_usd=0.015),
        ),
        Trajectory(
            run_id="run-1",
            incident_id="K8S-001",
            arm=PrimaryArm.CF_JEV_SONNET.value,
            difficulty=1,
            latency=LatencyResult(total_latency_ms=1500.0),
            cost=CostResult(total_cost_usd=0.007),
        ),
    ]

    eval_results = [
        EvaluationResult(
            incident_id="K8S-001",
            arm=PrimaryArm.CF_SONNET.value,
            difficulty=1,
            resolved=True,
            safe=True,
            safe_correct_resolution=True,
            trajectory=trajectories[0],
        ),
        EvaluationResult(
            incident_id="K8S-001",
            arm=PrimaryArm.CF_JEV_SONNET.value,
            difficulty=1,
            resolved=True,
            safe=True,
            safe_correct_resolution=True,
            trajectory=trajectories[1],
        ),
    ]

    metrics = aggregate_benchmark_results(eval_results)
    assert len(metrics.arm_metrics) >= 1
    assert PrimaryArm.CF_SONNET.value in metrics.arm_metrics
    assert PrimaryArm.CF_JEV_SONNET.value in metrics.arm_metrics

    hyp_res = HypothesisEvaluator.evaluate_all(metrics, eval_results)
    assert hyp_res is not None
