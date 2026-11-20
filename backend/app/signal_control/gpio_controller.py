"""
Real-hardware signal controller for a Raspberry Pi driving either:
  (a) a physical model-intersection rig (LEDs/relays for demo purposes), or
  (b) a real traffic-cabinet's "priority/preemption input" contacts,
      which is how commercial systems like Opticom actually integrate
      (they close a dry contact, they don't reprogram the controller).

This mirrors `MockSignalController`'s interface exactly, so
`preemption.py` doesn't need to know which one it's talking to.

Wiring assumptions (documented in hardware/README.md):
  NS_GREEN relay -> GPIO 17
  EW_GREEN relay -> GPIO 27
  ALL_RED  relay -> GPIO 22
Adjust BCM pin numbers to match your build.

Only import RPi.GPIO on the Pi itself - this module is written so it
raises a clear error rather than crashing the whole app if imported on
a dev machine without the library.
"""
from __future__ import annotations

import time

from app.models.schemas import SignalPhase
from app.signal_control.controller_base import SignalController

PHASE_PIN_MAP = {
    SignalPhase.NS_GREEN: 17,
    SignalPhase.EW_GREEN: 27,
    SignalPhase.ALL_RED: 22,
}


class RaspberryPiSignalController(SignalController):
    def __init__(self, pin_map: dict[SignalPhase, int] | None = None) -> None:
        try:
            import RPi.GPIO as GPIO  # noqa: N814
        except ImportError as e:
            raise RuntimeError(
                "RPi.GPIO is not available. This controller only runs on a "
                "Raspberry Pi. Use MockSignalController for development."
            ) from e

        self._gpio = GPIO
        self._pin_map = pin_map or PHASE_PIN_MAP

        self._gpio.setmode(self._gpio.BCM)
        for pin in self._pin_map.values():
            self._gpio.setup(pin, self._gpio.OUT, initial=self._gpio.LOW)

        self._phase = SignalPhase.NS_GREEN
        self._phase_started_at = time.time()
        self._drive(self._phase)

    def _drive(self, phase: SignalPhase) -> None:
        for p, pin in self._pin_map.items():
            self._gpio.output(pin, self._gpio.HIGH if p == phase else self._gpio.LOW)

    def get_phase(self) -> SignalPhase:
        return self._phase

    def set_phase(self, phase: SignalPhase) -> None:
        if phase != self._phase:
            self._phase = phase
            self._phase_started_at = time.time()
            self._drive(phase)

    def time_in_phase(self) -> float:
        return time.time() - self._phase_started_at

    def shutdown(self) -> None:
        self._gpio.cleanup()
