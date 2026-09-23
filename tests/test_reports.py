"""Test suite for storage persistence, CSV/JSON export, and scientific markdown generation."""

import os
from pathlib import Path
from backend.storage.repository import StorageRepository, BenchmarkRun, RunMetadata
from backend.storage.exporter import ReportExporter
from backend.models.schema import PrimaryArm, Trajectory, EvaluationResult, LatencyResult, CostResult
from backend.evaluation.metrics import aggregate_benchmark_results
from backend.evaluation.hypothesis import HypothesisEvaluator


def test_exporter_and_storage(tmp_path):
    repo = StorageRepository(base_dir=Path(tmp_path))

    traj = Trajectory(
        run_id="run-test",
        incident_id="K8S-001",
        arm=PrimaryArm.CF_SONNET.value,
        difficulty=1,
        latency=LatencyResult(total_latency_ms=2000.0),
        cost=CostResult(total_cost_usd=0.005),
    )

    eval_res = EvaluationResult(
        incident_id="K8S-001",
        arm=PrimaryArm.CF_SONNET.value,
        difficulty=1,
        resolved=True,
        safe=True,
        safe_correct_resolution=True,
        trajectory=traj,
    )

    bench_run = BenchmarkRun(
        metadata=RunMetadata(
            run_id="run-test",
            timestamp="2026-09-24T00:00:00Z",
            mode="test",
            arms=[PrimaryArm.CF_SONNET.value],
            repetitions=1,
            total_incidents=1,
            reasoning_effort="high",
        ),
        results=[eval_res],
    )

    run_dir = repo.save_run(bench_run)
    assert os.path.exists(os.path.join(run_dir, "metadata.json"))

    metrics = aggregate_benchmark_results([eval_res])
    hyp_analysis = HypothesisEvaluator.evaluate_all(metrics, [eval_res])

    # Test exporter
    csv_file = ReportExporter.export_csv(bench_run, run_dir)
    assert os.path.exists(csv_file)

    md_file = ReportExporter.export_markdown_report(bench_run, metrics, hyp_analysis, run_dir)
    assert os.path.exists(md_file)
