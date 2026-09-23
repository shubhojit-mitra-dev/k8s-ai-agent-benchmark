"""
FastAPI Main Application.
Provides CORS, lifecycle validation, static file serving, and route mounting.
"""

from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import BENCHMARK_VERSION
from backend.scenarios.registry import GLOBAL_SCENARIO_REGISTRY
from backend.server.routes import router

app = FastAPI(
    title="Kubernetes AI Agent Benchmark API",
    description="Academic evaluation platform: Jev + Claude Sonnet 5 vs Claude Sonnet 5 Baseline.",
    version=BENCHMARK_VERSION,
)

# Enable CORS for local Vite development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)

# Mount static frontend build if present
dist_path = Path("frontend/dist")
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")


@app.on_event("startup")
async def startup_event() -> None:
    # Fail fast if scenarios or tool catalog are misconfigured
    scenarios = GLOBAL_SCENARIO_REGISTRY.list_all()
    if len(scenarios) != 20:
        raise RuntimeError(f"Startup check failed: expected 20 scenarios, found {len(scenarios)}")
