"""
Approximate distance & speed estimation from 2D bounding boxes.

This is the piece that's genuinely hard to get right without a
calibrated/stereo camera or lidar, and real deployments usually solve
it with camera calibration (known mounting height/angle) rather than
this simple model. What's here is a standard, honest approximation:

  distance ≈ (real_world_height * focal_length_px) / bbox_height_px

...using a flat per-approach focal length calibration constant and an
assumed vehicle height. It's good enough to drive ETA-based preemption
decisions in a demo, and it's isolated in one file so it's a clean
swap-in point once real camera calibration (or a depth sensor) is
available - nothing else needs to know this changed.

Speed is estimated from the *change* in distance across two frames
of the same tracked object, so its accuracy depends entirely on
track continuity (see `SimpleTracker` in vision_pipeline.py).
"""
from __future__ import annotations

from dataclasses import dataclass

ASSUMED_VEHICLE_HEIGHT_M = 1.6          # sedan-ish; ambulances/trucks are taller, adds error
DEFAULT_FOCAL_LENGTH_PX = 900.0          # placeholder - calibrate per real camera + mount height


@dataclass
class DistanceEstimatorConfig:
    focal_length_px: float = DEFAULT_FOCAL_LENGTH_PX
    vehicle_height_m: float = ASSUMED_VEHICLE_HEIGHT_M


class DistanceEstimator:
    def __init__(self, config: DistanceEstimatorConfig | None = None) -> None:
        self.config = config or DistanceEstimatorConfig()

    def estimate_distance_m(self, bbox_height_px: float) -> float:
        if bbox_height_px <= 1:
            return float("inf")
        return (self.config.vehicle_height_m * self.config.focal_length_px) / bbox_height_px

    def estimate_speed_mps(self, prev_distance_m: float, curr_distance_m: float, dt: float) -> float:
        if dt <= 0:
            return 0.0
        # Positive speed = approaching (distance shrinking).
        return max(0.0, (prev_distance_m - curr_distance_m) / dt)
