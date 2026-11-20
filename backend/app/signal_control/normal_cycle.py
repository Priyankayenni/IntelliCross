"""
Baseline fixed-time cycling so the intersection does something sane
when there's no emergency vehicle around. Real deployments would swap
this for an actuated/adaptive controller (loop detectors, etc.) - this
project's contribution is the preemption layer on top, not reinventing
standard signal timing.
"""
from __future__ import annotations

from app.models.schemas import SignalPhase
from app.signal_control.controller_base import SignalController


class NormalCycleController:
    def __init__(
        self,
        controller: SignalController,
        ns_green_seconds: float = 30.0,
        ew_green_seconds: float = 30.0,
        all_red_seconds: float = 3.0,
    ) -> None:
        self.controller = controller
        self.ns_green_seconds = ns_green_seconds
        self.ew_green_seconds = ew_green_seconds
        self.all_red_seconds = all_red_seconds
        self._next_after_all_red = SignalPhase.EW_GREEN

    def tick(self) -> None:
        """Call regularly; flips phase once its allotted time has elapsed."""
        phase = self.controller.get_phase()
        elapsed = self.controller.time_in_phase()

        if phase == SignalPhase.NS_GREEN and elapsed >= self.ns_green_seconds:
            self._next_after_all_red = SignalPhase.EW_GREEN
            self.controller.set_phase(SignalPhase.ALL_RED)
        elif phase == SignalPhase.EW_GREEN and elapsed >= self.ew_green_seconds:
            self._next_after_all_red = SignalPhase.NS_GREEN
            self.controller.set_phase(SignalPhase.ALL_RED)
        elif phase == SignalPhase.ALL_RED and elapsed >= self.all_red_seconds:
            self.controller.set_phase(self._next_after_all_red)
