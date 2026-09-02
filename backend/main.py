"""
IntelliCross Inference & Control API
=====================================

FastAPI service providing real-time emergency vehicle detection,
corridor-based alerting, contact logging, and WebSocket live updates.

Endpoints:
  GET  /health                          — health check
  GET  /api/active-emergencies          — list active emergencies (polling fallback)
  GET  /api/hospitals                   — list hospitals (with optional lat/lng filter)
  GET  /api/signals                     — list traffic signals
  GET  /api/corridors                   — list monitoring corridors
  POST /api/detect-image                — detect objects in an uploaded image
  POST /api/detect-stream               — detect objects in a video file
  POST /api/alerts                      — create an internal alert
  POST /api/contact                     — record a contact attempt
  WS   /ws/alerts                       — WebSocket for live alert stream
  WS   /ws/emergency/{vehicle_id}       — WebSocket for per-vehicle updates

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel

LOG = logging.getLogger("intellicross.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="IntelliCross Inference & Control API",
    description="Real-time emergency vehicle detection, corridor alerting, and control room support",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\d+\.\d+\.\d+\.\d+)(:\d+)?",
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ===== CONSTANTS =====

YOLO_CLASSES = [
    "ambulance", "fire_truck", "police", "disaster",
    "car", "bus", "truck", "motorcycle", "auto_rickshaw", "pedestrian", "animal",
]
EMERGENCY_CLASSES = {"ambulance", "fire_truck", "police", "disaster"}
TRAINED_MODEL_PATH = Path("models/emergency_vehicle_web_v1.pt")
CORRIDOR_RADIUS_M = int(os.getenv("CORRIDOR_RADIUS_M", "1000"))
CONFIDENCE_THRESHOLD_LONG = float(os.getenv("CONFIDENCE_THRESHOLD_LONG", "0.35"))
CONFIDENCE_THRESHOLD_SHORT = float(os.getenv("CONFIDENCE_THRESHOLD_SHORT", "0.5"))

# ===== MODEL LOADING =====

_model = None
_model_source = "mock"


def load_model():
    global _model, _model_source
    try:
        from ultralytics import YOLO
    except ImportError:
        LOG.warning("ultralytics not installed — using mock detections")
        _model_source = "mock"
        return

    if TRAINED_MODEL_PATH.exists() and TRAINED_MODEL_PATH.stat().st_size > 100:
        try:
            _model = YOLO(str(TRAINED_MODEL_PATH))
            _model_source = "web_trained_v1"
            LOG.info("Loaded web-trained model from %s", TRAINED_MODEL_PATH)
            return
        except Exception as e:
            LOG.warning("Failed to load web-trained model: %s — falling back", e)

    try:
        _model = YOLO("yolov8n.pt")
        _model_source = "base_model"
        LOG.info("Loaded base pretrained YOLOv8n model")
    except Exception as e:
        LOG.warning("Failed to load base model: %s — using mock detections", e)
        _model_source = "mock"


load_model()

# ===== MOCK DATA =====

MOCK_HOSPITALS = [
    {"id": "aiims", "name": "AIIMS New Delhi", "city": "Ansari Nagar", "lat": 28.5672, "lng": 77.2100,
     "beds_available": 45, "total_beds": 800, "response_time": 3, "phone": "+91 11 2658 8500",
     "email": "emergency@aiims.edu",
     "specializations": ["Trauma Center", "Burn Unit", "Pediatric Care"]},
    {"id": "safdarjung", "name": "Safdarjung Hospital", "city": "Ring Road", "lat": 28.5687, "lng": 77.2067,
     "beds_available": 82, "total_beds": 650, "response_time": 5, "phone": "+91 11 2616 3072",
     "email": "emergency@safdarjung.nic.in",
     "specializations": ["Trauma Center", "Pediatric Care"]},
    {"id": "apollo", "name": "Indraprastha Apollo", "city": "Sarita Vihar", "lat": 28.5407, "lng": 77.2837,
     "beds_available": 120, "total_beds": 710, "response_time": 4, "phone": "+91 11 2692 5858",
     "email": "emergency@apollohospitals.com",
     "specializations": ["Trauma Center", "Burn Unit"]},
    {"id": "max", "name": "Max Super Speciality", "city": "Saket", "lat": 28.5273, "lng": 77.2137,
     "beds_available": 67, "total_beds": 500, "response_time": 6, "phone": "+91 11 2651 5050",
     "email": "emergency@maxhealthcare.in",
     "specializations": ["Burn Unit", "Pediatric Care"]},
]

MOCK_SIGNALS = [
    {"id": "SIG-01", "state": "green", "countdown": 42, "lat": 28.6329, "lng": 77.2195, "preemption": True, "preemption_time": 0},
    {"id": "SIG-02", "state": "green", "countdown": 31, "lat": 28.6208, "lng": 77.2148, "preemption": True, "preemption_time": 35},
    {"id": "SIG-03", "state": "yellow", "countdown": 18, "lat": 28.6062, "lng": 77.2121, "preemption": False, "preemption_time": None},
    {"id": "SIG-04", "state": "red", "countdown": 27, "lat": 28.5901, "lng": 77.2105, "preemption": False, "preemption_time": None},
    {"id": "SIG-05", "state": "green", "countdown": 56, "lat": 28.5754, "lng": 77.2092, "preemption": False, "preemption_time": None},
]

MOCK_CORRIDORS = [
    {"id": "COR-01", "name": "Ring Road Sector 5 Camera", "camera_id": "CAM-014", "signal_id": "SIG-01",
     "lat": 28.6329, "lng": 77.2195, "radius_m": CORRIDOR_RADIUS_M, "vehicle_id": "AMB-2047"},
    {"id": "COR-02", "name": "Moti Nagar Junction Camera", "camera_id": "CAM-022", "signal_id": "SIG-03",
     "lat": 28.6575, "lng": 77.1412, "radius_m": CORRIDOR_RADIUS_M, "vehicle_id": "FTR-0912"},
    {"id": "COR-03", "name": "CP Outer Circle Camera", "camera_id": "CAM-007", "signal_id": "SIG-02",
     "lat": 28.6315, "lng": 77.2167, "radius_m": CORRIDOR_RADIUS_M, "vehicle_id": None},
]

MOCK_VEHICLES = [
    {"id": "AMB-2047", "type": "ambulance", "location": "Ring Road, Sector 5",
     "destination": "AIIMS New Delhi", "destination_hospital_id": "aiims",
     "distance": 3.2, "eta": 4, "speed": 45, "heading": 185, "confidence": 0.98,
     "lat": 28.6329, "lng": 77.2195, "corridor_id": "COR-01", "distance_to_signal": 0.4,
     "locked_route": False, "driver_name": "Rajesh Kumar", "driver_phone": "+91 98100 12345", "severity": 5},
    {"id": "FTR-0912", "type": "fire_truck", "location": "Moti Nagar Junction",
     "destination": "Safdarjung Hospital", "destination_hospital_id": "safdarjung",
     "distance": 5.8, "eta": 9, "speed": 38, "heading": 210, "confidence": 0.72,
     "lat": 28.6575, "lng": 77.1412, "corridor_id": "COR-02", "distance_to_signal": 0.7,
     "locked_route": True, "driver_name": "Sunil Sharma", "driver_phone": "+91 98200 67890", "severity": 4},
    {"id": "POL-7710", "type": "police", "location": "Connaught Place",
     "destination": "Lok Nayak Hospital", "destination_hospital_id": "aiims",
     "distance": 7.1, "eta": 12, "speed": 32, "heading": 175, "confidence": 0.45,
     "lat": 28.6315, "lng": 77.2167, "corridor_id": None, "distance_to_signal": 1.2,
     "locked_route": False, "driver_name": "Anil Verma", "driver_phone": "+91 98300 11111", "severity": 2},
]

# In-memory stores
_alerts: List[dict] = []
_contact_logs: List[dict] = []
_ws_clients: List[WebSocket] = []


# ===== MODELS =====

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    class_name: str
    class_id: int
    confidence: float
    bbox: BoundingBox
    is_emergency: bool


class DetectionResponse(BaseModel):
    detections: List[Detection]
    top_class: Optional[str]
    top_confidence: float
    emergency_detected: bool
    model_source: str
    processing_time_ms: int
    image_width: int
    image_height: int


class HealthResponse(BaseModel):
    status: str
    model_source: str
    model_loaded: bool
    corridor_radius_m: int
    confidence_threshold_long: float
    confidence_threshold_short: float


class AlertCreate(BaseModel):
    vehicle_id: str
    vehicle_type: str
    severity: str = "warning"
    message: str
    location: str
    heading: int = 0
    confidence: float
    nearest_hospital: str
    eta: int


class ContactCreate(BaseModel):
    channel: str  # call, email, sms, whatsapp
    target: str
    target_name: str
    operator_id: str
    vehicle_id: Optional[str] = None


# ===== ENDPOINTS =====

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        model_source=_model_source,
        model_loaded=_model is not None,
        corridor_radius_m=CORRIDOR_RADIUS_M,
        confidence_threshold_long=CONFIDENCE_THRESHOLD_LONG,
        confidence_threshold_short=CONFIDENCE_THRESHOLD_SHORT,
    )


@app.get("/api/active-emergencies")
def active_emergencies():
    return {"vehicles": MOCK_VEHICLES, "count": len(MOCK_VEHICLES)}


@app.get("/api/hospitals")
def get_hospitals(lat: float = 0, lng: float = 0):
    return {"hospitals": MOCK_HOSPITALS}


@app.get("/api/signals")
def get_signals(lat: float = 0, lng: float = 0):
    return {"signals": MOCK_SIGNALS}


@app.get("/api/corridors")
def get_corridors():
    return {"corridors": MOCK_CORRIDORS, "radius_m": CORRIDOR_RADIUS_M}


@app.post("/api/detect-image", response_model=DetectionResponse)
async def detect_image(file: UploadFile = File(...)):
    start = time.time()
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(image)
    h, w = img_array.shape[:2]

    if _model is not None and _model_source != "mock":
        results = _model(img_array, verbose=False)
        detections = _parse_yolo_results(results, w, h)
    else:
        detections = _mock_detections(w, h)

    emergency = [d for d in detections if d.is_emergency]
    top = max(detections, key=lambda d: d.confidence) if detections else None

    elapsed = int((time.time() - start) * 1000)
    return DetectionResponse(
        detections=detections,
        top_class=top.class_name if top else None,
        top_confidence=top.confidence if top else 0,
        emergency_detected=len(emergency) > 0,
        model_source=_model_source,
        processing_time_ms=elapsed,
        image_width=w,
        image_height=h,
    )


@app.post("/api/detect-stream")
async def detect_stream(file: UploadFile = File(...), output_annotated: bool = Form(False)):
    start = time.time()
    video_bytes = await file.read()
    tmp_path = Path("/tmp/intellicross_stream_input.mp4")
    tmp_path.write_bytes(video_bytes)

    cap = cv2.VideoCapture(str(tmp_path))
    if not cap.isOpened():
        return JSONResponse(status_code=400, content={"error": "Cannot open video file"})

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_detections = []
    annotated_frames = []

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if _model is not None and _model_source != "mock":
            results = _model(frame, verbose=False)
            dets = _parse_yolo_results(results, frame.shape[1], frame.shape[0])
        else:
            dets = _mock_detections(frame.shape[1], frame.shape[0])

        if dets:
            frame_detections.append({"frame": frame_idx, "detections": [d.model_dump() for d in dets]})

        if output_annotated:
            annotated_frames.append(_draw_annotations(frame, dets))
        frame_idx += 1

    cap.release()
    tmp_path.unlink(missing_ok=True)

    output_path = None
    if output_annotated and annotated_frames:
        output_path = "/tmp/intellicross_annotated_output.mp4"
        h, w = annotated_frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
        for f in annotated_frames:
            writer.write(f)
        writer.release()

    elapsed = int((time.time() - start) * 1000)
    return {
        "total_frames": total_frames,
        "frames_with_detections": len(frame_detections),
        "frame_detections": frame_detections[:100],
        "model_source": _model_source,
        "processing_time_ms": elapsed,
        "annotated_output": output_path,
    }


@app.post("/api/alerts")
def create_alert(alert: AlertCreate):
    alert_dict = {
        "id": f"al-{int(time.time()*1000)}",
        "timestamp": time.time(),
        "acknowledged": False,
        **alert.model_dump(),
    }
    _alerts.insert(0, alert_dict)
    asyncio.create_task(_broadcast_alert(alert_dict))
    LOG.info("Alert created: %s — %s", alert_dict["id"], alert_dict["message"])
    return {"status": "created", "alert": alert_dict}


@app.post("/api/contact")
def record_contact(contact: ContactCreate):
    log = {
        "id": f"cl-{int(time.time()*1000)}",
        "timestamp": time.time(),
        "status": "sent",
        **contact.model_dump(),
    }
    _contact_logs.insert(0, log)
    LOG.info("Contact logged: %s via %s to %s", log["id"], log["channel"], log["target_name"])
    return {"status": "logged", "contact": log}


@app.get("/api/contact-logs")
def get_contact_logs():
    return {"logs": _contact_logs}


# ===== WEBSOCKET =====

@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await ws.accept()
    _ws_clients.append(ws)
    LOG.info("WebSocket client connected to /ws/alerts (total: %d)", len(_ws_clients))
    try:
        await ws.send_json({"type": "connected", "message": "Alert stream active"})
        while True:
            await asyncio.sleep(15)
            vehicle = random.choice(MOCK_VEHICLES)
            severities = ["critical", "warning", "info"]
            alert = {
                "type": "alert",
                "id": f"al-{int(time.time()*1000)}",
                "vehicle_id": vehicle["id"],
                "vehicle_type": vehicle["type"],
                "severity": random.choice(severities),
                "message": f"{vehicle['type'].title()} {vehicle['id']} corridor update",
                "location": vehicle["location"],
                "heading": vehicle["heading"],
                "confidence": vehicle["confidence"],
                "nearest_hospital": vehicle["destination"],
                "eta": vehicle["eta"],
                "timestamp": time.time(),
                "acknowledged": False,
            }
            await ws.send_json(alert)
    except WebSocketDisconnect:
        _ws_clients.remove(ws)
        LOG.info("WebSocket client disconnected (total: %d)", len(_ws_clients))


@app.websocket("/ws/emergency/{vehicle_id}")
async def ws_emergency(ws: WebSocket, vehicle_id: str):
    await ws.accept()
    LOG.info("WebSocket client connected to /ws/emergency/%s", vehicle_id)
    vehicle = next((v for v in MOCK_VEHICLES if v["id"] == vehicle_id), None)
    if not vehicle:
        await ws.send_json({"type": "error", "message": f"Vehicle {vehicle_id} not found"})
        await ws.close()
        return
    try:
        await ws.send_json({"type": "connected", "vehicle": vehicle})
        while True:
            await asyncio.sleep(5)
            await ws.send_json({
                "type": "update",
                "vehicle_id": vehicle_id,
                "speed": vehicle["speed"] + random.randint(-5, 5),
                "eta": max(1, vehicle["eta"] - 1),
                "distance": max(0.1, vehicle["distance"] - 0.1),
                "timestamp": time.time(),
            })
    except WebSocketDisconnect:
        LOG.info("WebSocket disconnected from /ws/emergency/%s", vehicle_id)


async def _broadcast_alert(alert: dict):
    for client in _ws_clients:
        try:
            await client.send_json({"type": "alert", **alert})
        except Exception:
            pass


# ===== HELPERS =====

def _parse_yolo_results(results, img_w: int, img_h: int) -> List[Detection]:
    detections = []
    for r in results:
        if r.boxes is None:
            continue
        for box, conf, cls in zip(r.boxes.xyxy, r.boxes.conf, r.boxes.cls):
            class_id = int(cls)
            class_name = YOLO_CLASSES[class_id] if class_id < len(YOLO_CLASSES) else "unknown"
            x1, y1, x2, y2 = box.tolist()
            detections.append(Detection(
                class_name=class_name, class_id=class_id,
                confidence=float(conf),
                bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                is_emergency=class_name in EMERGENCY_CLASSES,
            ))
    return detections


def _mock_detections(img_w: int, img_h: int) -> List[Detection]:
    rng = random.Random(int(time.time()) % 10000)
    count = 2 + rng.randint(0, 3)
    sample_classes = [
        ("ambulance", 0, True, 0.94), ("fire_truck", 1, True, 0.88),
        ("police", 2, True, 0.79), ("car", 4, False, 0.71),
        ("bus", 5, False, 0.67), ("motorcycle", 7, False, 0.58),
        ("truck", 6, False, 0.64), ("pedestrian", 9, False, 0.82),
    ]
    chosen = rng.sample(sample_classes, min(count, len(sample_classes)))
    detections = []
    for class_name, class_id, is_em, base_conf in chosen:
        x1 = rng.uniform(0, img_w * 0.5)
        y1 = rng.uniform(0, img_h * 0.5)
        x2 = x1 + rng.uniform(img_w * 0.1, img_w * 0.3)
        y2 = y1 + rng.uniform(img_h * 0.1, img_h * 0.3)
        conf = max(0.4, base_conf + rng.uniform(-0.1, 0.05))
        detections.append(Detection(
            class_name=class_name, class_id=class_id,
            confidence=round(conf, 3),
            bbox=BoundingBox(x1=round(x1, 1), y1=round(y1, 1), x2=round(x2, 1), y2=round(y2, 1)),
            is_emergency=is_em,
        ))
    return detections


def _draw_annotations(frame, detections: List[Detection]) -> np.ndarray:
    annotated = frame.copy()
    colors = {"ambulance": (220, 38, 38), "fire_truck": (234, 88, 12),
              "police": (2, 132, 199), "disaster": (124, 58, 237)}
    for det in detections:
        color = colors.get(det.class_name, (107, 114, 128))
        x1, y1, x2, y2 = int(det.bbox.x1), int(det.bbox.y1), int(det.bbox.x2), int(det.bbox.y2)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"{det.class_name} {det.confidence:.2f}"
        cv2.putText(annotated, label, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return annotated


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
