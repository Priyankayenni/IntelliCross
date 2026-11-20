"""
The orchestrator. Runs as a background asyncio task started at app
startup. Each tick it:

  1. Pulls the latest traffic state (mock generator or real SUMO/vision).
  2. Runs normal fixed-time cycling.
  3. Checks for emergency vehicles close enough to matter, computes ETA,
     and hands them to the preemption engine.
  4. Publishes an IntersectionStatus snapshot onto the event bus for the
     WebSocket layer to broadcast to the dashboard.

Swapping MockTrafficSimulator for SumoTrafficSimulator, or the ground-
truth vehicle list for real VehicleDetector output, only touches this
file - everything downstream (preemption, controller, dashboard) is
unaffected, which is the whole point of the layered design.
"""
from __future__ import annotations

import asyncio
import time

from app.core.event_bus import bus
from app.models.schemas import EmergencyEvent, IntersectionStatus
from app.signal_control.controller_base import MockSignalController
from app.signal_control.normal_cycle import NormalCycleController
from app.signal_control.preemption import PreemptionEngine
from app.simulation.traffic_sim import MockTrafficSimulator, SimVehicle

TELEMETRY_TOPIC = "telemetry"
TICK_SECONDS = 0.5


class IntersectionPipeline:
    def __init__(self, intersection_id: str = "INT-1") -> None:
        self.intersection_id = intersection_id
        self.simulator = MockTrafficSimulator(intersection_id=intersection_id)
        self.controller = MockSignalController()
        self.normal_cycle = NormalCycleController(self.controller)
        self.preemption = PreemptionEngine(self.controller)
        self._running = False
        self._paused = False  # set True while a VisionPipeline has taken over telemetry
        self._last_preemption = None
        self._fps_stub = 30.0  # mock-mode has no real frame pipeline; vision mode overwrites this

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def _closest_emergency(self, vehicles: list[SimVehicle]) -> SimVehicle | None:
        emergencies = [v for v in vehicles if v.is_emergency]
        if not emergencies:
            return None
        return min(emergencies, key=lambda v: v.distance_m / max(v.speed_mps, 0.1))

    async def _tick(self) -> None:
        if self._paused:
            return
        state = self.simulator.step(TICK_SECONDS)

        active_event: EmergencyEvent | None = None
        closest = self._closest_emergency(state.vehicles)

        if closest is not None:
            eta = PreemptionEngine.estimate_eta(closest.distance_m, closest.speed_mps)
            active_event = EmergencyEvent(
                intersection_id=self.intersection_id,
                track_id=hash(closest.vehicle_id) % 100000,
                vehicle_class=closest.vehicle_class,
                approach=closest.approach,
                distance_m=closest.distance_m,
                speed_mps=closest.speed_mps,
                eta_seconds=eta,
                confidence=0.9,  # ground-truth in mock mode; real confidence in vision mode
                timestamp=time.time(),
            )
            command = self.preemption.evaluate(active_event)
            if command is not None:
                self._last_preemption = command
                await bus.publish("preemption", command)

        if self.preemption.release_if_expired():
            pass  # normal cycling resumes automatically next tick since controller is now free

        if not self.preemption.is_holding:
            self.normal_cycle.tick()

        status = IntersectionStatus(
            intersection_id=self.intersection_id,
            current_phase=self.controller.get_phase(),
            time_in_phase=self.controller.time_in_phase(),
            normal_traffic_density=state.count_by_approach(),
            active_emergency=active_event,
            last_preemption=self._last_preemption,
            avg_detection_fps=self._fps_stub,
            mode="simulation",
        )
        await bus.publish(TELEMETRY_TOPIC, status)

    async def run_forever(self) -> None:
        self._running = True
        while self._running:
            await self._tick()
            await asyncio.sleep(TICK_SECONDS)

    def stop(self) -> None:
        self._running = False
        self.simulator.close()


# One pipeline instance per intersection; a real deployment would keep
# a dict of these keyed by intersection_id.
pipeline = IntersectionPipeline()
