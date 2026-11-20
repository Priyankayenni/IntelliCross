"""
Dynamic signal preemption engine.

Given the current traffic/detection state, this decides:
  1. Is an emergency vehicle close enough that we should act?
  2. What phase does the intersection need to be in for its approach?
  3. How long should we hold that phase (long enough to clear the
     vehicle + a safety margin, short enough not to gridlock the
     cross-street more than necessary)?

The algorithm is deliberately simple and explainable - a real deployment
needs this to be auditable by traffic engineers, not a black box.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from app.models.schemas import EmergencyEvent, PreemptionCommand, SignalPhase
from app.signal_control.controller_base import SignalController

# Which signal phase serves which approach.
APPROACH_TO_PHASE = {
    "N": SignalPhase.NS_GREEN,
    "S": SignalPhase.NS_GREEN,
    "E": SignalPhase.EW_GREEN,
    "W": SignalPhase.EW_GREEN,
}


@dataclass
class PreemptionConfig:
    trigger_eta_seconds: float = 25.0   # start preempting once ETA drops below this
    min_green_hold_seconds: float = 6.0  # never hold shorter than this once triggered
    clearance_buffer_seconds: float = 3.0  # extra hold time after vehicle's ETA, for safety
    all_red_clearance_seconds: float = 2.0  # transition interval before flipping phase


class PreemptionEngine:
    def __init__(self, controller: SignalController, config: PreemptionConfig | None = None) -> None:
        self.controller = controller
        self.config = config or PreemptionConfig()
        self._active_hold_until: float | None = None
        self._active_track_id: int | None = None

    @staticmethod
    def estimate_eta(distance_m: float, speed_mps: float) -> float:
        if speed_mps <= 0.1:
            return float("inf")
        return distance_m / speed_mps

    def evaluate(self, event: EmergencyEvent) -> PreemptionCommand | None:
        """
        Called whenever a new emergency-vehicle sighting comes in.
        Returns a PreemptionCommand if action should be taken, else None.
        """
        now = time.time()

        if event.eta_seconds > self.config.trigger_eta_seconds:
            return None  # too far out yet, don't disrupt normal cycling early

        needed_phase = APPROACH_TO_PHASE[event.approach]
        current_phase = self.controller.get_phase()

        hold_seconds = max(
            self.config.min_green_hold_seconds,
            event.eta_seconds + self.config.clearance_buffer_seconds,
        )

        if current_phase == needed_phase:
            # Already green for them - just extend the hold.
            command = PreemptionCommand(
                intersection_id=event.intersection_id,
                target_phase=needed_phase,
                hold_seconds=hold_seconds,
                reason="extend_green_for_approaching_emergency_vehicle",
                triggered_by=event.track_id,
                issued_at=now,
            )
        else:
            # Need a green-wave switch: all-red clearance, then flip.
            command = PreemptionCommand(
                intersection_id=event.intersection_id,
                target_phase=needed_phase,
                hold_seconds=hold_seconds,
                reason="green_wave_preemption_switch",
                triggered_by=event.track_id,
                issued_at=now,
            )
            self.controller.set_phase(SignalPhase.ALL_RED)

        self.controller.set_phase(needed_phase)
        self._active_hold_until = now + hold_seconds
        self._active_track_id = event.track_id
        return command

    def release_if_expired(self) -> bool:
        """
        Called periodically (e.g. once per detection loop tick). Returns
        True if the preemption hold just expired and normal cycling
        should resume.
        """
        if self._active_hold_until is None:
            return False
        if time.time() >= self._active_hold_until:
            self._active_hold_until = None
            self._active_track_id = None
            return True
        return False

    @property
    def is_holding(self) -> bool:
        return self._active_hold_until is not None
