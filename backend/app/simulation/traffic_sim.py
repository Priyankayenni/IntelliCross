"""
Traffic source abstraction.

Priya doesn't have SUMO installed yet, so this module ships a
`MockTrafficSimulator` that generates plausible vehicle flow (including
occasional emergency vehicles) without any external dependency, so the
whole pipeline runs end-to-end today.

`SumoTrafficSimulator` is the real integration point for later: once
SUMO + TraCI (`pip install traci sumolib`, plus the SUMO binaries) are
installed, flip `SIMULATOR_BACKEND=sumo` in config and this class takes
over. Both implementations satisfy the same `TrafficSimulator`
interface, so nothing else in the codebase needs to change.

Neither class produces camera *pixels* - that's a separate concern
(see `simulation/synthetic_frame.py` for a stand-in until real/SUMO
camera frames are wired up). This module produces ground-truth vehicle
state, which is what SUMO is actually good at simulating.
"""
from __future__ import annotations

import abc
import random
import time
from dataclasses import dataclass, field

from app.models.schemas import VehicleClass

APPROACHES = ["N", "S", "E", "W"]


@dataclass
class SimVehicle:
    vehicle_id: str
    vehicle_class: VehicleClass
    approach: str
    distance_m: float       # distance from stop line
    speed_mps: float
    is_emergency: bool = False


@dataclass
class TrafficState:
    intersection_id: str
    timestamp: float
    vehicles: list[SimVehicle] = field(default_factory=list)

    def count_by_approach(self) -> dict[str, int]:
        counts = {a: 0 for a in APPROACHES}
        for v in self.vehicles:
            counts[v.approach] += 1
        return counts


class TrafficSimulator(abc.ABC):
    """Common interface both the mock and the real SUMO backend implement."""

    @abc.abstractmethod
    def step(self, dt: float) -> TrafficState:
        """Advance simulation time by `dt` seconds and return current state."""

    @abc.abstractmethod
    def close(self) -> None:
        ...


class MockTrafficSimulator(TrafficSimulator):
    """
    Generates a believable stream of traffic without any external
    simulator. Good enough to exercise detection, preemption and the
    dashboard end-to-end while SUMO isn't set up yet.
    """

    def __init__(
        self,
        intersection_id: str = "INT-1",
        base_arrival_rate: float = 0.35,   # avg vehicles spawned per approach per second
        emergency_probability: float = 0.01,  # per step, per approach
        seed: int | None = None,
    ) -> None:
        self.intersection_id = intersection_id
        self.base_arrival_rate = base_arrival_rate
        self.emergency_probability = emergency_probability
        self._rng = random.Random(seed)
        self._vehicles: dict[str, SimVehicle] = {}
        self._next_id = 0

    def _spawn(self, approach: str, emergency: bool = False) -> SimVehicle:
        self._next_id += 1
        vclass = VehicleClass.AMBULANCE if emergency else self._rng.choice(
            [VehicleClass.CAR, VehicleClass.CAR, VehicleClass.CAR, VehicleClass.BUS, VehicleClass.TRUCK]
        )
        speed = self._rng.uniform(11.0, 16.0) if not emergency else self._rng.uniform(16.0, 22.0)
        return SimVehicle(
            vehicle_id=f"veh-{self._next_id}",
            vehicle_class=vclass,
            approach=approach,
            distance_m=self._rng.uniform(180, 260),
            speed_mps=speed,
            is_emergency=emergency,
        )

    def step(self, dt: float) -> TrafficState:
        # Spawn new vehicles.
        for approach in APPROACHES:
            if self._rng.random() < self.base_arrival_rate * dt:
                v = self._spawn(approach)
                self._vehicles[v.vehicle_id] = v
            if self._rng.random() < self.emergency_probability * dt:
                v = self._spawn(approach, emergency=True)
                self._vehicles[v.vehicle_id] = v

        # Advance existing vehicles, remove ones that reached the stop line.
        finished = []
        for vid, v in self._vehicles.items():
            v.distance_m -= v.speed_mps * dt
            # mild jitter so traffic isn't perfectly uniform
            v.speed_mps = max(3.0, v.speed_mps + self._rng.uniform(-0.4, 0.4))
            if v.distance_m <= 0:
                finished.append(vid)
        for vid in finished:
            del self._vehicles[vid]

        return TrafficState(
            intersection_id=self.intersection_id,
            timestamp=time.time(),
            vehicles=list(self._vehicles.values()),
        )

    def close(self) -> None:
        self._vehicles.clear()


class SumoTrafficSimulator(TrafficSimulator):
    """
    Real SUMO integration via TraCI. Not active until SUMO is installed
    and a .sumocfg is supplied - see hardware/../README for setup.

    Install:  pip install traci sumolib
              (+ SUMO itself: https://sumo.dlr.de/docs/Installing/index.html)
    """

    def __init__(self, sumocfg_path: str, intersection_id: str = "INT-1", gui: bool = False) -> None:
        try:
            import traci  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "traci is not installed. Run `pip install traci sumolib` and "
                "install the SUMO binaries before selecting the sumo backend."
            ) from e

        self._traci = __import__("traci")
        self.intersection_id = intersection_id
        binary = "sumo-gui" if gui else "sumo"
        self._traci.start([binary, "-c", sumocfg_path, "--start", "--quit-on-end"])

    def step(self, dt: float) -> TrafficState:
        traci = self._traci
        traci.simulationStep()
        vehicles = []
        for vid in traci.vehicle.getIDList():
            vtype = traci.vehicle.getTypeID(vid)
            is_emergency = "emergency" in vtype.lower() or "ambulance" in vtype.lower()
            vehicles.append(
                SimVehicle(
                    vehicle_id=vid,
                    vehicle_class=VehicleClass.AMBULANCE if is_emergency else VehicleClass.CAR,
                    approach=self._infer_approach(traci, vid),
                    distance_m=traci.vehicle.getLanePosition(vid),
                    speed_mps=traci.vehicle.getSpeed(vid),
                    is_emergency=is_emergency,
                )
            )
        return TrafficState(intersection_id=self.intersection_id, timestamp=time.time(), vehicles=vehicles)

    @staticmethod
    def _infer_approach(traci, vid: str) -> str:
        # Map SUMO edge id -> compass approach. Customize per your .net.xml
        # edge naming convention - this is a reasonable default.
        edge = traci.vehicle.getRoadID(vid)
        for tag, approach in (("north", "N"), ("south", "S"), ("east", "E"), ("west", "W")):
            if tag in edge.lower():
                return approach
        return "N"

    def close(self) -> None:
        self._traci.close()
