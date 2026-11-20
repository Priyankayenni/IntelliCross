# IntelliCross backend

Async FastAPI service: traffic simulation → detection → preemption →
live telemetry over WebSocket.

## Quick start (simulation mode — no SUMO, no camera, no hardware needed)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # for just the simulation demo you only need
                                  # fastapi, uvicorn, pydantic, numpy — the
                                  # ultralytics/opencv lines are for vision mode

uvicorn app.main:app --reload --port 8000
```

Then:
- `GET  http://localhost:8000/health` — liveness check
- `GET  http://localhost:8000/status` — one-shot snapshot
- `WS   ws://localhost:8000/ws/telemetry` — live intersection state (what the dashboard consumes)
- `WS   ws://localhost:8000/ws/preemption-events` — fires only when a preemption command is issued

The mock traffic simulator (`app/simulation/traffic_sim.py`) starts
generating traffic and occasional emergency vehicles immediately — you
should see a preemption event within the first minute or two. To force
one faster for a demo/test, bump `emergency_probability` in
`MockTrafficSimulator`.

## Project layout

```
app/
  main.py                     FastAPI app + lifespan-managed background pipeline task
  core/
    pipeline.py                mock/SUMO orchestration loop (tick -> simulate -> preempt -> publish)
    vision_pipeline.py          REAL computer-vision loop (video frames -> detect -> track -> ETA -> preempt)
    event_bus.py                async pub/sub feeding WebSocket clients
  models/
    schemas.py                 all shared Pydantic contracts
  simulation/
    traffic_sim.py             MockTrafficSimulator (works today) + SumoTrafficSimulator (TraCI hook)
  detection/
    detector.py                YOLOv8-nano wrapper + emergency-vehicle heuristic
    tracker.py                  minimal IoU tracker, gives detections stable track_ids across frames
    distance.py                 monocular distance/speed estimation from bounding-box height
  signal_control/
    controller_base.py         SignalController interface + MockSignalController
    gpio_controller.py         RaspberryPiSignalController (real hardware)
    normal_cycle.py             baseline fixed-time cycling
    preemption.py                ETA calc + green-wave decision engine
  api/
    routes.py                  REST + WebSocket routes, including /vision/start and /vision/stop
```

## Vision mode — confirmed working against real video

Unlike the mock/SUMO path (ground-truth vehicle state), the vision path
runs actual YOLOv8n inference on video frames. This was tested against
both a real photo (Ultralytics' bundled `bus.jpg` — correctly detected
at 0.87 confidence) and a synthetic clip simulating an approaching
vehicle, confirming distance shrinks and ETA drops sensibly frame over
frame, and that a real preemption command gets issued at a believable
ETA (not on frame 1, not due to a timing artifact).

**One real bug found and fixed along the way, worth knowing about if
you extend this**: for a pre-recorded video *file*, speed must be
computed using the video's own frame rate (`1 / video_fps`) as `dt`,
not wall-clock time between `detect()` calls — inference speed varies
run to run, so wall-clock dt corrupts the speed estimate. Live sources
(webcam index, RTSP URL) correctly use wall-clock dt instead, since
those frames really do arrive in real time. See
`VisionPipeline.__init__` in `vision_pipeline.py`.

Try it yourself once the server is running:

```bash
curl -X POST http://localhost:8000/vision/start \
  -H "Content-Type: application/json" \
  -d '{"source": "/path/to/video.mp4", "approach": "N"}'

# or a live webcam:
curl -X POST http://localhost:8000/vision/start \
  -H "Content-Type: application/json" \
  -d '{"source": "0", "approach": "N"}'

curl -X POST http://localhost:8000/vision/stop
```

Starting vision mode automatically pauses the mock simulator so they
don't both publish conflicting telemetry; stopping it resumes the mock
simulator. The dashboard doesn't need to know which is active — it
just renders whatever `IntersectionStatus.mode` says (`"simulation"` or
`"vision"`).

**Measured on this machine (CPU, no GPU):** ~7.5 FPS steady-state at
640px with yolov8n — real-time-plausible for a single intersection
camera, consistent with the abstract's "lightweight, real-time"
framing. Your numbers will vary with hardware; this isn't a formal
benchmark, just a sanity check that the "lightweight" claim holds up.

## Swapping in real SUMO

1. Install SUMO (https://sumo.dlr.de/docs/Installing/index.html) and `pip install traci sumolib`.
2. Build or obtain a `.sumocfg` + `.net.xml` for your intersection.
3. In `app/core/pipeline.py`, replace `MockTrafficSimulator(...)` with
   `SumoTrafficSimulator(sumocfg_path="...", gui=True)`.

Nothing else in the codebase needs to change — both simulators satisfy
the same `TrafficSimulator` interface.

## Swapping in real hardware

See `../hardware/README.md`.

## Testing the pipeline logic without any ML/CV dependencies

The preemption engine and simulator have no dependency on
ultralytics/opencv — they operate on structured vehicle state, not
pixels. That means you can exercise the whole decision logic
(`app/core/pipeline.py`, `app/signal_control/preemption.py`) with just
`fastapi`, `uvicorn`, `pydantic`, and `numpy` installed. Vision
dependencies only come into play once you wire a real or SUMO camera
frame into `VehicleDetector`.
