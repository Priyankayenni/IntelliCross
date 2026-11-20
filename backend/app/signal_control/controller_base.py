"""
Signal controller abstraction.

This is the seam between "software" and "hardware" that you asked for:
the preemption engine only ever talks to `SignalController`, and never
knows whether `set_phase()` is flipping a variable in RAM (simulation)
or driving a physical relay/GPIO pin at a real intersection cabinet.

Two implementations ship here:
  - MockSignalController: pure software, used for the SUMO/mock demo.
  - (see gpio_controller.py) RaspberryPiSignalController: drives real
    traffic-light hardware via GPIO, for when you move to a physical
    model intersection or a real controller cabinet's input contacts.
"""
from __future__ import annotations

import abc
import time

from app.models.schemas import SignalPhase


class SignalController(abc.ABC):
    """Every concrete controller (software or hardware) implements this."""

    @abc.abstractmethod
    def get_phase(self) -> SignalPhase:
        ...

    @abc.abstractmethod
    def set_phase(self, phase: SignalPhase) -> None:
        ...

    @abc.abstractmethod
    def time_in_phase(self) -> float:
        ...


class MockSignalController(SignalController):
    """Software-only controller. No physical I/O - just tracks state."""

    def __init__(self, initial_phase: SignalPhase = SignalPhase.NS_GREEN) -> None:
        self._phase = initial_phase
        self._phase_started_at = time.time()

    def get_phase(self) -> SignalPhase:
        return self._phase

    def set_phase(self, phase: SignalPhase) -> None:
        if phase != self._phase:
            self._phase = phase
            self._phase_started_at = time.time()

    def time_in_phase(self) -> float:
        return time.time() - self._phase_started_at
