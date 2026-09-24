"""
Server-Sent Events (SSE) Progress Broadcaster.
Streams live benchmark trajectory events to frontend clients.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional


class EventBroadcaster:
    """Manages active run event queues and broadcasts SSE events to subscribers."""

    def __init__(self) -> None:
        self._queues: Dict[str, List[asyncio.Queue]] = {}

    def register(self, run_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.setdefault(run_id, []).append(q)
        return q

    def unregister(self, run_id: str, q: asyncio.Queue) -> None:
        if run_id in self._queues and q in self._queues[run_id]:
            self._queues[run_id].remove(q)
            if not self._queues[run_id]:
                del self._queues[run_id]

    def broadcast(self, run_id: str, event_data: Dict[str, Any]) -> None:
        targets = set()
        if run_id in self._queues:
            targets.update(self._queues[run_id])
        if "active" in self._queues:
            targets.update(self._queues["active"])
        if "global" in self._queues:
            targets.update(self._queues["global"])
        for q in targets:
            q.put_nowait(event_data)

    async def event_generator(self, run_id: str) -> AsyncGenerator[Dict[str, str], None]:
        q = self.register(run_id)
        try:
            while True:
                # Wait for next event or timeout check
                try:
                    data = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield {
                        "event": data.get("event", "message"),
                        "data": json.dumps(data),
                    }
                    if data.get("event") == "run_completed":
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment
                    yield {"event": "ping", "data": json.dumps({"status": "alive"})}
        finally:
            self.unregister(run_id, q)


GLOBAL_EVENT_BROADCASTER = EventBroadcaster()
