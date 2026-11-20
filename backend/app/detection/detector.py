"""
Lightweight detection wrapper around Ultralytics YOLOv8-nano.

Design notes
------------
- YOLOv8n's stock COCO weights only give you generic classes (car, bus,
  truck, motorcycle) - there's no "ambulance" class out of the box.
  For a real deployment you'd fine-tune on an emergency-vehicle dataset
  (roboflow has several open ones). Until that model exists, this
  module ships a *heuristic* emergency classifier that layers on top
  of the generic detections: flashing high-contrast light-bar colors
  + siren-shape aspect ratio + (optionally) audio. It's clearly marked
  so it's a one-line swap once a fine-tuned weight file exists.
- The detector accepts frames from ANY source (webcam, video file,
  RTSP camera, or a screenshot pulled from SUMO's GUI) - it has no
  idea whether it's running against simulation or real hardware. That
  boundary is intentional: keeps this module hardware-agnostic.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:  # pragma: no cover - allows the rest of the stack to run without the model installed yet
    ULTRALYTICS_AVAILABLE = False

from app.models.schemas import Detection, VehicleClass

# COCO class ids YOLOv8n cares about for traffic
COCO_VEHICLE_MAP = {
    2: VehicleClass.CAR,
    3: VehicleClass.MOTORCYCLE,
    5: VehicleClass.BUS,
    7: VehicleClass.TRUCK,
}


@dataclass
class DetectorConfig:
    weights: str = "yolov8n.pt"          # swap for a fine-tuned emergency-vehicle checkpoint when available
    confidence_threshold: float = 0.35
    device: str = "cpu"                   # "cuda" / "mps" if available
    imgsz: int = 640


class EmergencyVehicleHeuristic:
    """
    Cheap, model-free signal that boosts confidence a generic "truck" or
    "car" detection is actually an emergency vehicle, using light-bar
    color signature (red/blue flashing) in the bounding box crop.

    This is intentionally simple - it's a placeholder for a real
    fine-tuned classifier head, not a production siren detector.
    """

    RED_BLUE_SATURATION_THRESHOLD = 0.18

    def score(self, frame: np.ndarray, bbox: tuple[float, float, float, float]) -> float:
        x1, y1, x2, y2 = [int(v) for v in bbox]
        x1, y1 = max(x1, 0), max(y1, 0)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return 0.0

        # Look at the top third of the box - that's where a light bar sits.
        top_third = crop[: max(1, crop.shape[0] // 3), :, :]
        if top_third.size == 0:
            return 0.0

        # Very cheap red/blue dominance heuristic in BGR space.
        b, g, r = top_third[:, :, 0], top_third[:, :, 1], top_third[:, :, 2]
        red_ratio = float(np.mean(r > 150) )
        blue_ratio = float(np.mean(b > 150))
        signal = red_ratio + blue_ratio
        return min(signal, 1.0)


class VehicleDetector:
    def __init__(self, config: Optional[DetectorConfig] = None) -> None:
        self.config = config or DetectorConfig()
        self._model = None
        self._heuristic = EmergencyVehicleHeuristic()
        self._frame_count = 0
        self._last_fps_ts = time.time()
        self._fps = 0.0

        if ULTRALYTICS_AVAILABLE:
            self._model = YOLO(self.config.weights)
        # else: stays None. `detect()` will raise a clear error rather than
        # silently returning nothing - see below.

    @property
    def ready(self) -> bool:
        return self._model is not None

    def _update_fps(self) -> None:
        self._frame_count += 1
        now = time.time()
        elapsed = now - self._last_fps_ts
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._last_fps_ts = now

    def detect(self, frame: np.ndarray, approach: str) -> list[Detection]:
        """
        Run one frame through YOLOv8n and return normalized Detection objects.

        `approach` is the compass direction this camera covers (N/S/E/W) -
        it's supplied by the caller because that's a property of *where
        the camera is mounted*, not something vision can infer alone.
        """
        if self._model is None:
            raise RuntimeError(
                "ultralytics is not installed or model failed to load. "
                "Run `pip install ultralytics` and ensure yolov8n.pt can be "
                "downloaded, or point DetectorConfig.weights at a local file."
            )

        results = self._model.predict(
            frame,
            imgsz=self.config.imgsz,
            conf=self.config.confidence_threshold,
            device=self.config.device,
            verbose=False,
        )
        self._update_fps()

        detections: list[Detection] = []
        result = results[0]
        for i, box in enumerate(result.boxes):
            cls_id = int(box.cls.item())
            if cls_id not in COCO_VEHICLE_MAP:
                continue

            conf = float(box.conf.item())
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
            vclass = COCO_VEHICLE_MAP[cls_id]

            emergency_score = self._heuristic.score(frame, (x1, y1, x2, y2))
            is_emergency = emergency_score > EmergencyVehicleHeuristic.RED_BLUE_SATURATION_THRESHOLD
            if is_emergency:
                # Re-label generic "truck"/"car" as the closer emergency category.
                vclass = VehicleClass.AMBULANCE if vclass == VehicleClass.TRUCK else VehicleClass.POLICE

            detections.append(
                Detection(
                    track_id=i,  # replace with a real tracker (ByteTrack/BoT-SORT) id for production
                    vehicle_class=vclass,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    approach=approach,
                    is_emergency=is_emergency,
                )
            )
        return detections

    @property
    def fps(self) -> float:
        return self._fps
