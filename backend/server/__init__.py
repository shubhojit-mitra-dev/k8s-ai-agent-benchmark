"""Benchmark server package initialization."""

from backend.server.app import app
from backend.server.sse import GLOBAL_EVENT_BROADCASTER

broadcaster = GLOBAL_EVENT_BROADCASTER

__all__ = ["app", "broadcaster", "GLOBAL_EVENT_BROADCASTER"]
