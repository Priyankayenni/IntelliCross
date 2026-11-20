"""
Minimal async pub/sub bus.

The detection loop, the simulator and the preemption engine all run as
independent asyncio tasks. Rather than wiring them directly to the
WebSocket connections (which come and go), everything publishes onto
this bus and the API layer subscribes to broadcast it out.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable

Listener = Callable[[Any], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Listener]] = defaultdict(list)
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe_queue(self, topic: str) -> asyncio.Queue:
        """Get a fresh queue that will receive every future publish on `topic`."""
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues[topic].append(q)
        return q

    def unsubscribe_queue(self, topic: str, q: asyncio.Queue) -> None:
        if q in self._queues[topic]:
            self._queues[topic].remove(q)

    async def publish(self, topic: str, payload: Any) -> None:
        for q in list(self._queues[topic]):
            if q.full():
                # Drop the oldest telemetry frame rather than block the
                # producer - dashboards care about "latest", not "every".
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await q.put(payload)


# One process-wide bus is enough for this service.
bus = EventBus()
