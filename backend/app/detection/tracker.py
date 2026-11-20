"""
A deliberately small IoU tracker.

YOLOv8n's raw output has no notion of "the same car as last frame" -
that's what lets us compute speed (distance delta / dt) and avoid
re-triggering preemption for a vehicle we're already tracking. A real
deployment should use ByteTrack or BoT-SORT (both ship inside
ultralytics via `model.track()`); this hand-rolled version exists so
the tracking behavior is transparent and dependency-free for the demo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models.schemas import Detection


def iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter_w, inter_h = max(0.0, inter_x2 - inter_x1), max(0.0, inter_y2 - inter_y1)
    inter = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


@dataclass
class Track:
    track_id: int
    bbox: tuple[float, float, float, float]
    vehicle_class: str
    frames_missing: int = 0
    distance_history: list[float] = field(default_factory=list)


class SimpleTracker:
    def __init__(self, iou_threshold: float = 0.3, max_missing_frames: int = 5) -> None:
        self.iou_threshold = iou_threshold
        self.max_missing_frames = max_missing_frames
        self._tracks: dict[int, Track] = {}
        self._next_id = 0

    def update(self, detections: list[Detection]) -> list[Detection]:
        """Assigns stable track_ids in-place (returns the same list) by
        greedy IoU matching against tracks seen in the previous frame."""
        unmatched_tracks = set(self._tracks.keys())
        for det in detections:
            best_id, best_iou = None, 0.0
            for tid in unmatched_tracks:
                score = iou(det.bbox, self._tracks[tid].bbox)
                if score > best_iou:
                    best_id, best_iou = tid, score

            if best_id is not None and best_iou >= self.iou_threshold:
                det.track_id = best_id
                self._tracks[best_id].bbox = det.bbox
                self._tracks[best_id].frames_missing = 0
                unmatched_tracks.discard(best_id)
            else:
                self._next_id += 1
                det.track_id = self._next_id
                self._tracks[det.track_id] = Track(
                    track_id=det.track_id, bbox=det.bbox, vehicle_class=det.vehicle_class.value
                )

        # Age out tracks that went unmatched this frame; drop if stale too long.
        for tid in unmatched_tracks:
            self._tracks[tid].frames_missing += 1
        self._tracks = {
            tid: t for tid, t in self._tracks.items() if t.frames_missing <= self.max_missing_frames
        }
        return detections

    def record_distance(self, track_id: int, distance_m: float) -> float | None:
        """Stores this frame's distance for the track and returns the
        previous frame's distance (or None if this is a new track)."""
        track = self._tracks.get(track_id)
        if track is None:
            return None
        prev = track.distance_history[-1] if track.distance_history else None
        track.distance_history.append(distance_m)
        if len(track.distance_history) > 10:
            track.distance_history.pop(0)
        return prev
