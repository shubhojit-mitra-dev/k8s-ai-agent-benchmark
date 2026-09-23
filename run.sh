#!/usr/bin/env bash
# Kubernetes AI Agent Benchmark & Evaluation Platform Runner
# Usage:
#   ./run.sh test                 - Run pytest suite
#   ./run.sh benchmark [args]     - Run CLI benchmark (e.g. ./run.sh benchmark --mode smoke --force-mock)
#   ./run.sh server               - Run FastAPI live streaming backend server on port 8000
#   ./run.sh frontend             - Run React Vite dev server on port 3000
#   ./run.sh all                  - Build frontend and launch integrated server

set -euo pipefail

CMD="${1:-all}"

case "$CMD" in
  test)
    echo "Running comprehensive automated test suite..."
    python3 -m pytest tests/ -v
    ;;
  benchmark)
    shift || true
    echo "Launching benchmark execution engine..."
    python3 -m backend.benchmark "$@"
    ;;
  server)
    echo "Starting FastAPI server on http://localhost:8000..."
    exec uvicorn backend.server.app:app --host 0.0.0.0 --port 8000 --reload
    ;;
  frontend)
    echo "Starting Vite frontend server on http://localhost:3000..."
    cd frontend && exec npm run dev
    ;;
  all)
    echo "Building frontend dashboard..."
    (cd frontend && npm run build)
    echo "Starting benchmark platform server on http://localhost:8000..."
    exec uvicorn backend.server.app:app --host 0.0.0.0 --port 8000
    ;;
  *)
    echo "Unknown command: $CMD"
    echo "Available commands: test, benchmark, server, frontend, all"
    exit 1
    ;;
esac
