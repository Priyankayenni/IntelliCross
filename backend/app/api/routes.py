from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.event_bus import bus
from app.core.pipeline import TELEMETRY_TOPIC, pipeline
from app.core.vision_pipeline import VisionPipeline

router = APIRouter()

_vision_state = {"pipeline": None, "task": None}


class VisionStartRequest(BaseModel):
    source: str  # video file path, RTSP URL, or webcam index as a string ("0")
    approach: str = "N"


@router.post("/vision/start")
async def start_vision(req: VisionStartRequest):
    """
    Switches the dashboard's telemetry feed from the mock simulator to a
    real computer-vision pipeline running against `source`. Runs until
    the video ends, the stream drops, or /vision/stop is called.
    """
    if _vision_state["task"] is not None and not _vision_state["task"].done():
        raise HTTPException(409, "A vision pipeline is already running. Call /vision/stop first.")

    source: str | int = int(req.source) if req.source.isdigit() else req.source
    try:
        vp = VisionPipeline(source=source, approach=req.approach)
    except RuntimeError as e:
        raise HTTPException(400, str(e))

    pipeline.pause()  # stop the mock simulator from also publishing telemetry
    _vision_state["pipeline"] = vp
    _vision_state["task"] = asyncio.create_task(vp.run_forever())
    return {"status": "started", "source": req.source, "approach": req.approach}


@router.post("/vision/stop")
async def stop_vision():
    vp = _vision_state["pipeline"]
    if vp is None:
        raise HTTPException(400, "No vision pipeline is running.")
    vp.stop()
    pipeline.resume()
    _vision_state["pipeline"] = None
    _vision_state["task"] = None
    return {"status": "stopped"}


@router.get("/status")
async def get_status():
    """One-shot REST snapshot - handy for curl/debugging without opening a socket."""
    return {
        "intersection_id": pipeline.intersection_id,
        "current_phase": pipeline.controller.get_phase(),
        "time_in_phase": round(pipeline.controller.time_in_phase(), 2),
        "is_preemption_holding": pipeline.preemption.is_holding,
    }


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.websocket("/ws/telemetry")
async def telemetry_ws(websocket: WebSocket):
    """
    Live push of IntersectionStatus snapshots to the dashboard. Every
    connected client gets its own queue off the event bus so a slow
    client can't stall the others.
    """
    await websocket.accept()
    queue = bus.subscribe_queue(TELEMETRY_TOPIC)
    try:
        while True:
            status = await queue.get()
            await websocket.send_text(status.model_dump_json())
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe_queue(TELEMETRY_TOPIC, queue)


@router.websocket("/ws/preemption-events")
async def preemption_ws(websocket: WebSocket):
    """Separate low-frequency stream: only fires when a preemption command is issued."""
    await websocket.accept()
    queue = bus.subscribe_queue("preemption")
    try:
        while True:
            command = await queue.get()
            await websocket.send_text(command.model_dump_json())
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe_queue("preemption", queue)
