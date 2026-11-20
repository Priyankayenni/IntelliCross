"""
The real-camera counterpart to `core/pipeline.py`'s mock/SUMO loop.

This is what "computer vision pipeline" actually means in the project
title: frames in, `EmergencyEvent`s and `PreemptionCommand`s out, using
the *same* `PreemptionEngine` and `SignalController` the mock pipeline
uses. Only the traffic source differs.

Source can be a video file path, a webcam index (0, 1, ...), or an
RTSP URL - anything `cv2.VideoCapture` accepts.
"""
from __future__ import annotations

import asyncio
import time

import cv2

from app.core.event_bus import bus
from app.core.pipeline import TELEMETRY_TOPIC
from app.detection.detector import DetectorConfig, VehicleDetector
from app.detection.distance import DistanceEstimator
from app.detection.tracker import SimpleTracker
from app.models.schemas import EmergencyEvent, FrameResult, IntersectionStatus
from app.signal_control.controller_base import MockSignalController
from app.signal_control.normal_cycle import NormalCycleController
from app.signal_control.preemption import PreemptionEngine

# Which side of the frame counts as which compass approach - set this
# per camera mount. Default assumes a single camera watching one
# approach (the common real-world case: one camera per approach).
DEFAULT_APPROACH = "N"


class VisionPipeline:
    def __init__(
        self,
        source: str | int,
        intersection_id: str = "INT-1",
        approach: str = DEFAULT_APPROACH,
        weights: str = "yolov8n.pt",
    ) -> None:
        self.intersection_id = intersection_id
        self.approach = approach
        self.detector = VehicleDetector(DetectorConfig(weights=weights))
        self.tracker = SimpleTracker()
        self.distance_estimator = DistanceEstimator()
        self.controller = MockSignalController()
        self.normal_cycle = NormalCycleController(self.controller)
        self.preemption = PreemptionEngine(self.controller)

        self._cap = cv2.VideoCapture(source)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open video source: {source!r}")

        # Live sources (webcam index / RTSP stream) deliver frames in real
        # time, so wall-clock dt between processed frames is correct.
        # A pre-recorded FILE does NOT - two frames processed 0.14s apart
        # in wall-clock time might be 0.1s or 2s apart *in the video's own
        # timeline*, entirely depending on how fast inference happens to
        # run. For file sources we instead use the video's own frame rate
        # to compute dt, so speed/ETA estimates reflect the footage's
        # actual motion rather than this machine's inference speed.
        self._is_live_source = isinstance(source, int) or str(source).lower().startswith(
            ("rtsp://", "http://", "https://")
        )
        video_fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._nominal_dt = (1.0 / video_fps) if (not self._is_live_source and video_fps > 0) else None

        self._frame_id = 0
        self._running = False
        self._last_preemption = None
        self._last_frame_ts = time.time()

    async def _process_frame(self, frame) -> None:
        detections = self.detector.detect(frame, approach=self.approach)
        detections = self.tracker.update(detections)

        now = time.time()
        if self._nominal_dt is not None:
            dt = self._nominal_dt  # trust the video's own frame timing, not inference wall-clock
        else:
            dt = now - self._last_frame_ts
        self._last_frame_ts = now

        active_event: EmergencyEvent | None = None

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            bbox_height = max(1.0, y2 - y1)
            distance = self.distance_estimator.estimate_distance_m(bbox_height)
            prev_distance = self.tracker.record_distance(det.track_id, distance)

            det.distance_m = distance
            speed = (
                self.distance_estimator.estimate_speed_mps(prev_distance, distance, dt)
                if prev_distance is not None
                else 0.0
            )
            det.speed_mps = speed

            if det.is_emergency and speed > 0.5:
                eta = PreemptionEngine.estimate_eta(distance, speed)
                event = EmergencyEvent(
                    intersection_id=self.intersection_id,
                    track_id=det.track_id,
                    vehicle_class=det.vehicle_class,
                    approach=det.approach,
                    distance_m=distance,
                    speed_mps=speed,
                    eta_seconds=eta,
                    confidence=det.confidence,
                    timestamp=now,
                )
                active_event = event
                command = self.preemption.evaluate(event)
                if command is not None:
                    self._last_preemption = command
                    await bus.publish("preemption", command)

        if self.preemption.release_if_expired():
            pass
        if not self.preemption.is_holding:
            self.normal_cycle.tick()

        counts = {"N": 0, "S": 0, "E": 0, "W": 0}
        for det in detections:
            counts[det.approach] = counts.get(det.approach, 0) + 1

        frame_result = FrameResult(
            intersection_id=self.intersection_id,
            frame_id=self._frame_id,
            timestamp=now,
            fps=self.detector.fps,
            detections=detections,
            vehicle_count_by_approach=counts,
        )
        await bus.publish("frames", frame_result)

        status = IntersectionStatus(
            intersection_id=self.intersection_id,
            current_phase=self.controller.get_phase(),
            time_in_phase=self.controller.time_in_phase(),
            normal_traffic_density=counts,
            active_emergency=active_event,
            last_preemption=self._last_preemption,
            avg_detection_fps=self.detector.fps,
            mode="vision",
        )
        await bus.publish(TELEMETRY_TOPIC, status)

    async def run_forever(self) -> None:
        self._running = True
        while self._running:
            ok, frame = self._cap.read()
            if not ok:
                break  # end of file / stream dropped
            self._frame_id += 1
            await self._process_frame(frame)
            await asyncio.sleep(0)  # yield to event loop between frames

    def stop(self) -> None:
        self._running = False
        self._cap.release()
