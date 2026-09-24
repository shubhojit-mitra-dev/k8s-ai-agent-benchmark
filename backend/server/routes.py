"""
FastAPI REST Routes for the Benchmark Platform.
Exposes scenarios, run triggering, live SSE streams, and report downloads.
"""

from __future__ import annotations

import asyncio
import json
import time
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
@router.post("/runs/start")
async def create_run(req: RunRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    settings = BenchmarkSettings(
        reasoning_effort=ReasoningEffort(req.reasoning_effort),
        routing_mode=OpenRouterRoutingMode(req.routing_mode),
    )

    diff_range = (req.difficulty_range[0], req.difficulty_range[1]) if req.difficulty_range else None
    planned_run_id = f"{int(time.time())}_{req.mode}"

    async def _run() -> None:
        try:
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
        except Exception as e:
            GLOBAL_EVENT_BROADCASTER.broadcast("active", {
                "event": "run_error",
                "error": str(e),
                "timestamp": time.time(),
            })

    asyncio.create_task(_run())

    return {
        "status": "initiated",
        "run_id": planned_run_id,
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
    
    frontend_trajectories = []
    for r in run.results:
        t = r.trajectory
        # Transform events into tool_events and decisions
        tool_events = []
        decisions = []
        step_idx = 1
        for ev in t.events:
            actor = getattr(ev, "actor", "")
            if actor == "tool":
                tool_events.append({
                    "step_index": step_idx,
                    "tool_name": getattr(ev, "tool", ""),
                    "arguments": getattr(ev, "tool_args", {}),
                    "risk_level": getattr(ev, "risk_level", "READ_ONLY"),
                    "output": getattr(ev, "tool_output", ""),
                    "duration_ms": getattr(ev, "latency_ms", 0.0),
                    "timestamp": getattr(ev, "monotonic_ms", 0.0),
                })
            else:
                decisions.append({
                    "step_index": step_idx,
                    "engine": "JEV" if actor == "jev" else "SONNET",
                    "choice": getattr(ev, "decision", ""),
                    "noul": "",
                    "score": getattr(ev, "confidence", 0.0) or 0.0,
                    "raw_reasoning": json.dumps(getattr(ev, "payload", {})),
                    "timestamp": getattr(ev, "monotonic_ms", 0.0),
                })
            step_idx += 1

        frontend_trajectories.append({
            "run_id": t.run_id,
            "scenario_id": t.incident_id,
            "arm": t.arm,
            "start_time": 0,
            "end_time": 0,
            "duration_ms": t.latency.total_latency_ms,
            "tool_events": tool_events,
            "decisions": decisions,
            "resolved": r.resolved,
            "total_tokens": t.tokens_input + t.tokens_output,
            "prompt_tokens": t.tokens_input,
            "completion_tokens": t.tokens_output,
            "total_cost_usd": t.cost.total_cost_usd,
            "total_provider_latency_ms": t.latency.model_latency_ms,
            "error_message": None,
        })
    return frontend_trajectories


@router.get("/runs/{run_id}/report")
async def get_run_report(run_id: str) -> Dict[str, Any]:
    run = GLOBAL_STORAGE_REPOSITORY.load_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run_dir = GLOBAL_STORAGE_REPOSITORY.get_run_dir(run_id)
    report_file = run_dir / "report.md"
    neutral_summary = ""
    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            neutral_summary = f.read()

    agg = aggregate_benchmark_results(run.results)
    
    # Format arm metrics for dashboard
    arms_data = {}
    for arm_name, m in agg.arm_metrics.items():
        arms_data[arm_name] = {
            "arm": arm_name,
            "sample_size": len(run.results),
            "resolution_rate": m.safe_resolution_rate,
            "safe_correct_rate": m.safe_resolution_rate,
            "mean_duration_ms": m.latency_total_ms.mean,
            "p50_duration_ms": m.latency_total_ms.p50,
            "p90_duration_ms": m.latency_total_ms.p90,
            "p95_duration_ms": m.latency_total_ms.p95,
            "p99_duration_ms": m.latency_total_ms.p99,
            "mean_tokens": m.total_tokens.mean,
            "mean_cost_usd": m.cost_usd.mean,
            "mean_wrong_turns": 0.0,
            "mean_safety_score": 1.0 - m.unsafe_action_rate,
            "prohibited_action_rate": m.unsafe_action_rate,
            "total_cost_usd": sum(r.trajectory.cost.total_cost_usd for r in run.results if r.arm == arm_name),
        }

    return {
        "timestamp": 0,
        "run_id": run_id,
        "mode": run.metadata.mode,
        "metrics": {
            "total_runs": len(run.results),
            "arms": arms_data,
            "difficulty_breakdown": {},
        },
        "hypothesis_results": {},
        "neutral_summary": neutral_summary,
    }


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


@router.get("/events")
@router.get("/runs/{run_id}/events")
async def stream_run_events(run_id: str = "active") -> EventSourceResponse:
    """Streams live execution events via Server-Sent Events (SSE)."""
    return EventSourceResponse(GLOBAL_EVENT_BROADCASTER.event_generator(run_id))
