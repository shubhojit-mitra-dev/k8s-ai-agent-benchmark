"""
Storage Repository for Benchmark Runs, Trajectories, and Artifacts.
Provides thread-safe persistence and run comparison capabilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.config import (
    BENCHMARK_VERSION,
    SCENARIO_VERSION,
    PROMPT_VERSION,
    EVALUATION_VERSION,
    BenchmarkSettings,
)
from backend.models.schema import EvaluationResult, Trajectory


class RunMetadata(BaseModel):
    run_id: str
    timestamp: str
    benchmark_version: str = BENCHMARK_VERSION
    scenario_version: str = SCENARIO_VERSION
    prompt_version: str = PROMPT_VERSION
    evaluation_version: str = EVALUATION_VERSION
    mode: str
    arms: List[str]
    repetitions: int
    total_incidents: int
    reasoning_effort: str
    seed: Optional[int] = None
    completed: bool = False
    duration_seconds: float = 0.0


class BenchmarkRun(BaseModel):
    metadata: RunMetadata
    results: List[EvaluationResult] = Field(default_factory=list)


class StorageRepository:
    """Persistent storage engine for benchmark evaluations."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = base_dir or Path("results/runs")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._runs_cache: Dict[str, BenchmarkRun] = {}

    def get_run_dir(self, run_id: str) -> Path:
        run_dir = self.base_dir / f"run_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_run(self, run: BenchmarkRun) -> Path:
        self._runs_cache[run.metadata.run_id] = run
        run_dir = self.get_run_dir(run.metadata.run_id)

        # 1. Save metadata.json
        meta_path = run_dir / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(run.metadata.model_dump_json(indent=2))

        # 2. Save results.json
        res_path = run_dir / "results.json"
        with open(res_path, "w", encoding="utf-8") as f:
            dump_data = [r.model_dump() for r in run.results]
            json.dump(dump_data, f, indent=2)

        # 3. Save trajectories.json
        traj_path = run_dir / "trajectories.json"
        with open(traj_path, "w", encoding="utf-8") as f:
            dump_traj = [r.trajectory.model_dump() for r in run.results]
            json.dump(dump_traj, f, indent=2)

        return run_dir

    def load_run(self, run_id: str) -> Optional[BenchmarkRun]:
        if run_id in self._runs_cache:
            return self._runs_cache[run_id]

        run_dir = self.base_dir / f"run_{run_id}"
        meta_path = run_dir / "metadata.json"
        res_path = run_dir / "results.json"

        if not meta_path.exists():
            return None

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = RunMetadata(**json.load(f))

        results: List[EvaluationResult] = []
        if res_path.exists():
            with open(res_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
                results = [EvaluationResult(**item) for item in raw_list]

        loaded = BenchmarkRun(metadata=meta, results=results)
        self._runs_cache[run_id] = loaded
        return loaded

    def list_runs(self) -> List[RunMetadata]:
        runs: List[RunMetadata] = []
        for run_dir in sorted(self.base_dir.glob("run_*"), reverse=True):
            meta_path = run_dir / "metadata.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        runs.append(RunMetadata(**json.load(f)))
                except Exception:
                    continue
        return runs

    def compare_runs(self, run_id_a: str, run_id_b: str) -> Dict[str, Any]:
        """Compares two benchmark runs side-by-side."""
        run_a = self.load_run(run_id_a)
        run_b = self.load_run(run_id_b)
        if not run_a or not run_b:
            return {"error": "One or both runs not found"}

        return {
            "run_a": {
                "metadata": run_a.metadata.model_dump(),
                "trajectories_count": len(run_a.results),
                "safe_resolution_rate": sum(1 for r in run_a.results if r.safe_correct_resolution) / max(1, len(run_a.results)),
            },
            "run_b": {
                "metadata": run_b.metadata.model_dump(),
                "trajectories_count": len(run_b.results),
                "safe_resolution_rate": sum(1 for r in run_b.results if r.safe_correct_resolution) / max(1, len(run_b.results)),
            },
        }


GLOBAL_STORAGE_REPOSITORY = StorageRepository()
