"""
Kubernetes AI Agent Benchmark Engine & CLI.
Executes primary and secondary experimental arms, blind scoring,
statistical evaluations, and scientific report exports.
"""

from __future__ import annotations

import asyncio
import datetime
import os
import random
import sys
import time
from typing import Any, Callable, Dict, List, Optional
import click
from rich.console import Console
from rich.table import Table

from backend.agents import create_agent_for_arm
from backend.config import (
    BENCHMARK_VERSION,
    BenchmarkMode,
    BenchmarkSettings,
    ReasoningEffort,
)
from backend.evaluation import (
    BlindedEvaluatorContext,
    HypothesisEvaluator,
    TrajectoryEvaluator,
    aggregate_benchmark_results,
)
from backend.models.schema import EvaluationResult, PrimaryArm, ScenarioMetadata, Trajectory
from backend.scenarios.registry import GLOBAL_SCENARIO_REGISTRY
from backend.storage import (
    BenchmarkRun,
    ReportExporter,
    RunMetadata,
    GLOBAL_STORAGE_REPOSITORY,
)

console = Console()


class BenchmarkEngine:
    """Core experimental engine driving autonomous benchmark runs."""

    def __init__(
        self,
        settings: Optional[BenchmarkSettings] = None,
        mode: BenchmarkMode = BenchmarkMode.QUICK,
        arms: Optional[List[str]] = None,
        incident_ids: Optional[List[str]] = None,
        difficulty_range: Optional[tuple[int, int]] = None,
        repetitions: int = 1,
        max_steps: int = 20,
        timeout_seconds: float = 120.0,
        confidence_threshold: float = 0.70,
        seed: Optional[int] = 42,
        force_mock: bool = False,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self.settings = settings or BenchmarkSettings()
        self.mode = mode
        self.repetitions = repetitions
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.confidence_threshold = confidence_threshold
        self.seed = seed
        self.force_mock = force_mock
        self.event_callback = event_callback

        # Select arms
        default_arms = [
            PrimaryArm.CF_SONNET.value,
            PrimaryArm.CF_JEV_SONNET.value,
            PrimaryArm.OR_SONNET.value,
            PrimaryArm.OR_JEV_SONNET.value,
        ]
        self.arms = arms or default_arms

        # Select incidents
        all_scenarios = GLOBAL_SCENARIO_REGISTRY.list_all()
        if incident_ids:
            self.scenarios = [s for s in all_scenarios if s.id in incident_ids]
        elif difficulty_range:
            low, high = difficulty_range
            self.scenarios = [s for s in all_scenarios if low <= s.difficulty <= high]
        elif mode == BenchmarkMode.SMOKE:
            self.scenarios = all_scenarios[:1]
            self.max_steps = 10
            self.repetitions = 1
        elif mode == BenchmarkMode.QUICK:
            # 4 representative scenarios covering different failure domains
            self.scenarios = [s for s in all_scenarios if s.id in {"K8S-001", "K8S-005", "K8S-013", "K8S-020"}]
            self.max_steps = 15
            self.repetitions = 1
        elif mode in {BenchmarkMode.FULL, BenchmarkMode.DEEP}:
            self.scenarios = all_scenarios
            if mode == BenchmarkMode.DEEP:
                self.max_steps = 30
        else:
            self.scenarios = all_scenarios

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if self.event_callback:
            payload = {"event": event_type, "timestamp": time.time(), **data}
            self.event_callback(payload)

    async def execute(self) -> BenchmarkRun:
        run_id = f"{int(time.time())}_{self.mode.value}"
        start_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        start_wall = time.monotonic()

        self._emit_event("run_started", {
            "run_id": run_id,
            "mode": self.mode.value,
            "arms": self.arms,
            "scenarios_count": len(self.scenarios),
            "repetitions": self.repetitions,
        })

        results: List[EvaluationResult] = []
        rng = random.Random(self.seed)

        # Repetition loop
        for rep in range(1, self.repetitions + 1):
            # Section 73: Randomize arm execution order between repetitions
            shuffled_arms = list(self.arms)
            rng.shuffle(shuffled_arms)

            for scenario in self.scenarios:
                self._emit_event("incident_started", {
                    "run_id": run_id,
                    "repetition": rep,
                    "incident_id": scenario.id,
                    "difficulty": scenario.difficulty,
                })

                for arm in shuffled_arms:
                    # Section 173: Blinded evaluation setup
                    blind_ctx = BlindedEvaluatorContext(seed=self.seed)
                    blind_id = blind_ctx.arm_to_blind_map.get(arm, arm)

                    # Initialize deterministic simulator
                    simulator = GLOBAL_SCENARIO_REGISTRY.create_simulator(scenario.id)

                    # Create agent
                    agent = create_agent_for_arm(
                        run_id=run_id,
                        arm=arm,
                        incident_id=scenario.id,
                        difficulty=scenario.difficulty,
                        simulator=simulator,
                        settings=self.settings,
                        confidence_threshold=self.confidence_threshold,
                        force_mock=self.force_mock,
                        max_steps=self.max_steps,
                        timeout_seconds=self.timeout_seconds,
                    )

                    # Run autonomous trajectory
                    trajectory = await agent.run(initial_alert=scenario.initial_alert)

                    # Blind trajectory before evaluation
                    blinded_traj = blind_ctx.blind_trajectory(trajectory)
                    blind_eval = TrajectoryEvaluator.evaluate(blinded_traj)

                    # Unblind strictly post-evaluation
                    blind_eval.arm = arm
                    blind_eval.trajectory.arm = arm

                    results.append(blind_eval)

                    self._emit_event("incident_resolved" if blind_eval.safe_correct_resolution else "incident_failed", {
                        "run_id": run_id,
                        "incident_id": scenario.id,
                        "arm": arm,
                        "safe_correct_resolution": blind_eval.safe_correct_resolution,
                        "latency_ms": blind_eval.trajectory.latency.total_latency_ms,
                        "cost_usd": blind_eval.trajectory.cost.total_cost_usd,
                        "steps": blind_eval.trajectory.total_steps,
                    })

        duration = time.monotonic() - start_wall
        metadata = RunMetadata(
            run_id=run_id,
            timestamp=start_time_iso,
            mode=self.mode.value,
            arms=self.arms,
            repetitions=self.repetitions,
            total_incidents=len(self.scenarios),
            reasoning_effort=self.settings.reasoning_effort.value,
            seed=self.seed,
            completed=True,
            duration_seconds=round(duration, 2),
        )

        run = BenchmarkRun(metadata=metadata, results=results)

        # Persist results and generate export artifacts
        run_dir = GLOBAL_STORAGE_REPOSITORY.save_run(run)
        agg_metrics = aggregate_benchmark_results(results)
        hypothesis_report = HypothesisEvaluator.evaluate_all(agg_metrics, results)

        ReportExporter.export_csv(run, run_dir)
        ReportExporter.export_markdown_report(run, agg_metrics, hypothesis_report, run_dir)

        self._emit_event("run_completed", {
            "run_id": run_id,
            "duration_seconds": duration,
            "total_trajectories": len(results),
            "run_dir": str(run_dir),
        })

        return run


@click.command()
@click.option("--mode", type=click.Choice([m.value for m in BenchmarkMode]), default="quick", help="Benchmark execution mode")
@click.option("--arms", multiple=True, help="Specific arms to execute (e.g. CF-SONNET, CF-JEV-SONNET)")
@click.option("--incidents", multiple=True, help="Specific scenario IDs to evaluate (e.g. K8S-001, K8S-020)")
@click.option("--difficulty", nargs=2, type=int, help="Difficulty range (min max), e.g. 1 10")
@click.option("--repetitions", default=1, type=int, help="Repetitions per incident arm combination")
@click.option("--reasoning-effort", type=click.Choice([r.value for r in ReasoningEffort]), default="high", help="Frontier model reasoning effort")
@click.option("--timeout", default=120.0, type=float, help="Max wall-clock seconds per incident")
@click.option("--max-steps", default=20, type=int, help="Max diagnostic steps per trajectory")
@click.option("--seed", default=42, type=int, help="Random seed for execution order and reproducibility")
@click.option("--force-mock", is_flag=True, help="Force mock providers even if API credentials exist")
def main(
    mode: str,
    arms: tuple[str, ...],
    incidents: tuple[str, ...],
    difficulty: tuple[int, int],
    repetitions: int,
    reasoning_effort: str,
    timeout: float,
    max_steps: int,
    seed: int,
    force_mock: bool,
) -> None:
    """CLI runner for the Kubernetes AI Agent Benchmark."""
    console.print(f"[bold green]Starting Kubernetes AI Agent Benchmark ({BENCHMARK_VERSION})[/bold green]")
    console.print(f"Mode: [cyan]{mode}[/cyan] | Repetitions: [cyan]{repetitions}[/cyan] | Max Steps: [cyan]{max_steps}[/cyan]")

    settings = BenchmarkSettings(
        reasoning_effort=ReasoningEffort(reasoning_effort),
    )

    diff_range = (difficulty[0], difficulty[1]) if difficulty else None
    arms_list = list(arms) if arms else None
    incidents_list = list(incidents) if incidents else None

    engine = BenchmarkEngine(
        settings=settings,
        mode=BenchmarkMode(mode),
        arms=arms_list,
        incident_ids=incidents_list,
        difficulty_range=diff_range,
        repetitions=repetitions,
        max_steps=max_steps,
        timeout_seconds=timeout,
        seed=seed,
        force_mock=force_mock,
    )

    run = asyncio.run(engine.execute())

    # Print summary decision matrix to console
    agg = aggregate_benchmark_results(run.results)
    table = Table(title="Primary Decision Matrix", show_header=True, header_style="bold magenta")
    table.add_column("Arm", style="cyan")
    table.add_column("Safe Res Rate", justify="right")
    table.add_column("Median Latency", justify="right")
    table.add_column("Mean Cost", justify="right")
    table.add_column("Sonnet Calls/Inc", justify="right")
    table.add_column("Unsafe Rate", justify="right")

    for arm_name, m in agg.arm_metrics.items():
        table.add_row(
            arm_name,
            f"{m.safe_resolution_rate:.1%}",
            f"{m.latency_total_ms.p50:.1f} ms",
            f"${m.cost_usd.mean:.4f}",
            f"{m.sonnet_calls_mean:.2f}",
            f"{m.unsafe_action_rate:.1%}",
        )
    console.print(table)
    console.print(f"[bold green]Run completed successfully. Artifacts saved to results/runs/run_{run.metadata.run_id}[/bold green]")


if __name__ == "__main__":
    main()
