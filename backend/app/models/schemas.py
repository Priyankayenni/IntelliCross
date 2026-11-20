"""
Shared data contracts for IntelliCross.

Keeping these in one place means the detector, the simulator, the
preemption engine and the API/WebSocket layer are all speaking the
same language, regardless of whether the data originated from a real
camera + real intersection hardware, or from the SUMO/mock simulator.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class VehicleClass(str, Enum):
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE = "police"


class SignalPhase(str, Enum):
    NS_GREEN = "NS_GREEN"   # north-south green, east-west red
    EW_GREEN = "EW_GREEN"   # east-west green, north-south red
    ALL_RED = "ALL_RED"     # transition / clearance interval


class Detection(BaseModel):
    """A single detected object in one frame."""
    track_id: int
    vehicle_class: VehicleClass
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2 (pixels)
    approach: str  # "N" | "S" | "E" | "W"
    distance_m: Optional[float] = None
    speed_mps: Optional[float] = None
    is_emergency: bool = False


class FrameResult(BaseModel):
    """Output of the detection pipeline for one processed frame."""
    intersection_id: str
    frame_id: int
    timestamp: float
    fps: float
    detections: list[Detection]
    vehicle_count_by_approach: dict[str, int]


class EmergencyEvent(BaseModel):
    """Raised the moment an emergency vehicle is confirmed and tracked."""
    intersection_id: str
    track_id: int
    vehicle_class: VehicleClass
    approach: str
    distance_m: float
    speed_mps: float
    eta_seconds: float
    confidence: float
    timestamp: float


class PreemptionCommand(BaseModel):
    """Instruction sent from the preemption engine to a signal controller."""
    intersection_id: str
    target_phase: SignalPhase
    hold_seconds: float
    reason: str
    triggered_by: Optional[int] = None  # track_id of triggering vehicle
    issued_at: float


class IntersectionStatus(BaseModel):
    """Live telemetry snapshot pushed to the dashboard over WebSocket."""
    intersection_id: str
    current_phase: SignalPhase
    time_in_phase: float
    normal_traffic_density: dict[str, int]
    active_emergency: Optional[EmergencyEvent] = None
    last_preemption: Optional[PreemptionCommand] = None
    avg_detection_fps: float
    mode: str  # "simulation" | "hardware"
