"""
FastAPI REST Routes for the Benchmark Platform.
Exposes scenarios, run triggering, live SSE streams, and report downloads.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.benchmark import BenchmarkEngine
from backend.config import (
    BENCHMARK_VERSION,
    BenchmarkMode,
    BenchmarkSettings,
    OpenRouterRoutingMode,
    ReasoningEffort,
)
from backend.evaluation import aggregate_benchmark_results
from backend.scenarios.registry import GLOBAL_SCENARIO_REGISTRY
from backend.server.sse import GLOBAL_EVENT_BROADCASTER
from backend.storage import GLOBAL_STORAGE_REPOSITORY

router = APIRouter(prefix="/api")


class RunRequest(BaseModel):
    mode: str = "quick"
    arms: Optional[List[str]] = None
    incidents: Optional[List[str]] = None
    difficulty_range: Optional[List[int]] = None
    repetitions: int = 1
    reasoning_effort: str = "high"
    timeout_seconds: float = 120.0
    max_steps: int = 20
    confidence_threshold: float = 0.70
    routing_mode: str = "default"
    seed: int = 42
    force_mock: bool = False


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    settings = BenchmarkSettings()
    return {
        "status": "healthy",
        "benchmark_version": BENCHMARK_VERSION,
        "cloudflare_configured": settings.is_cf_configured(),
        "openrouter_configured": settings.is_or_configured(),
        "total_scenarios": len(GLOBAL_SCENARIO_REGISTRY.list_all()),
    }


@router.get("/scenarios")
async def list_scenarios() -> List[Dict[str, Any]]:
    scenarios = GLOBAL_SCENARIO_REGISTRY.list_all()
    # Exclude hidden ground truth during general inspection
    return [
        {
            "id": s.id,
            "title": s.title,
            "difficulty": s.difficulty,
            "category": s.category,
            "initial_alert": s.initial_alert,
            "initial_state_sha256": s.initial_state_sha256,
        }
        for s in scenarios
    ]


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str) -> Dict[str, Any]:
    scenario = GLOBAL_SCENARIO_REGISTRY.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario.model_dump()


@router.post("/runs")
async def create_run(req: RunRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    settings = BenchmarkSettings(
        reasoning_effort=ReasoningEffort(req.reasoning_effort),
        routing_mode=OpenRouterRoutingMode(req.routing_mode),
    )

    diff_range = (req.difficulty_range[0], req.difficulty_range[1]) if req.difficulty_range else None

    # Asynchronous runner hook broadcasting to SSE
    def run_benchmark_task() -> None:
        async def _run() -> None:
            engine = BenchmarkEngine(
                settings=settings,
                mode=BenchmarkMode(req.mode),
                arms=req.arms,
                incident_ids=req.incidents,
                difficulty_range=diff_range,
                repetitions=req.repetitions,
                max_steps=req.max_steps,
                timeout_seconds=req.timeout_seconds,
                confidence_threshold=req.confidence_threshold,
                seed=req.seed,
                force_mock=req.force_mock,
                event_callback=lambda ev: GLOBAL_EVENT_BROADCASTER.broadcast("active", ev),
            )
            await engine.execute()

        asyncio.run(_run())

    background_tasks.add_task(run_benchmark_task)

    return {
        "status": "initiated",
        "message": f"Benchmark run launched in mode '{req.mode}'",
        "stream_url": "/api/runs/active/events",
    }


@router.get("/runs")
async def list_runs() -> List[Dict[str, Any]]:
    runs = GLOBAL_STORAGE_REPOSITORY.list_runs()
    return [r.model_dump() for r in runs]


@router.get("/runs/{run_id}")
async def get_run_details(run_id: str) -> Dict[str, Any]:
    run = GLOBAL_STORAGE_REPOSITORY.load_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    agg = aggregate_benchmark_results(run.results)
    return {
        "metadata": run.metadata.model_dump(),
        "aggregate_metrics": agg.model_dump(),
        "trajectories_count": len(run.results),
    }


@router.get("/runs/{run_id}/trajectories")
async def get_run_trajectories(run_id: str) -> List[Dict[str, Any]]:
    run = GLOBAL_STORAGE_REPOSITORY.load_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return [r.model_dump() for r in run.results]


@router.get("/runs/{run_id}/report")
async def get_run_report(run_id: str) -> PlainTextResponse:
    run_dir = GLOBAL_STORAGE_REPOSITORY.get_run_dir(run_id)
    report_file = run_dir / "report.md"
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report artifact not found")
    with open(report_file, "r", encoding="utf-8") as f:
        return PlainTextResponse(f.read())


@router.get("/runs/{run_id}/export/{export_format}")
async def export_run(run_id: str, export_format: str) -> Any:
    run_dir = GLOBAL_STORAGE_REPOSITORY.get_run_dir(run_id)
    if export_format == "csv":
        path = run_dir / "results.csv"
        if not path.exists():
            raise HTTPException(status_code=404, detail="CSV export not found")
        return FileResponse(path, filename=f"run_{run_id}_results.csv", media_type="text/csv")
    elif export_format == "json":
        path = run_dir / "results.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="JSON export not found")
        return FileResponse(path, filename=f"run_{run_id}_results.json", media_type="application/json")
    elif export_format in {"md", "markdown"}:
        path = run_dir / "report.md"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Markdown report not found")
        return FileResponse(path, filename=f"run_{run_id}_report.md", media_type="text/markdown")
    raise HTTPException(status_code=400, detail="Invalid export format")


@router.get("/compare")
async def compare_runs(run_a: str = Query(...), run_b: str = Query(...)) -> Dict[str, Any]:
    comp = GLOBAL_STORAGE_REPOSITORY.compare_runs(run_a, run_b)
    if "error" in comp:
        raise HTTPException(status_code=404, detail=comp["error"])
    return comp


@router.get("/runs/{run_id}/events")
async def stream_run_events(run_id: str) -> EventSourceResponse:
    """Streams live execution events via Server-Sent Events (SSE)."""
    return EventSourceResponse(GLOBAL_EVENT_BROADCASTER.event_generator(run_id))
