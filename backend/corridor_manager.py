"""
IntelliCross - Metropolitan Corridor Manager
============================================
Synchronized multi-intersection corridor system for Emergency Vehicle (EV)
green wave orchestration under unconstrained Indian road conditions.

Indian Road Paradigm Compliance:
- Heterogeneous traffic mix (cars, buses, trucks, motorcycles, auto-rickshaws,
  pedestrians, animals) modeled via dynamic clearance factors
- Lane-less road geometry handled through logical lane partitioning
- Optimistic planning: pre-emptively opens green waves downstream before EV arrival
- Accounts for slow-moving vehicle platoons (auto-rickshaws, buses) clearance time

Architecture:
- IntersectionNode: Tracks individual intersection state, coordinates, signal timing
- CorridorManager: Orchestrates predictive green wave across registered nodes
- Calculates exact trigger schedule for downstream signal pre-emption
"""

import time
import math
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import threading


class SignalState(Enum):
    """Traffic signal states with Indian context."""
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    FLASHING_AMBER = "FLASHING_AMBER"  # For un-signalized intersections


class VehicleClass(Enum):
    """Indian vehicle taxonomy for clearance time computation."""
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    AUTO_RICKSHAW = "autorickshaw"
    PEDESTRIAN = "person"
    ANIMAL = "animal"
    EMERGENCY = "emergency"


# Clearance time multipliers for Indian heterogeneous traffic (seconds per vehicle)
# Based on IRC:SP:41 guidelines and field observations
CLEARANCE_TIME_FACTORS = {
    VehicleClass.CAR: 2.0,
    VehicleClass.BUS: 4.5,
    VehicleClass.TRUCK: 5.0,
    VehicleClass.MOTORCYCLE: 1.2,
    VehicleClass.AUTO_RICKSHAW: 2.5,
    VehicleClass.PEDESTRIAN: 3.0,
    VehicleClass.ANIMAL: 6.0,
    VehicleClass.EMERGENCY: 1.0,
}

# Default saturation flow rates (vehicles/hour/lane) for Indian conditions
SATURATION_FLOW = {
    VehicleClass.CAR: 1800,
    VehicleClass.BUS: 1200,
    VehicleClass.TRUCK: 1000,
    VehicleClass.MOTORCYCLE: 2400,
    VehicleClass.AUTO_RICKSHAW: 2000,
}


@dataclass
class IntersectionNode:
    """
    Represents a single intersection in the corridor.
    
    Attributes:
        node_id: Unique identifier (e.g., "Node-CP01")
        name: Human-readable name (e.g., "Connaught Place Inner Circle")
        latitude: GPS latitude
        longitude: GPS longitude
        distance_from_prev_m: Distance from previous node in meters
        signal_states: Current signal state per logical lane [3 lanes]
        green_duration_sec: Current green phase duration
        cycle_length_sec: Full signal cycle length
        offset_sec: Offset from corridor reference time (for coordination)
        lane_densities: Current density percentage per lane [3 lanes]
        vehicle_composition: Count of each vehicle class per lane
        is_active: Whether node is actively controlled
        last_update_ts: Timestamp of last state update
    """
    node_id: str
    name: str
    latitude: float
    longitude: float
    distance_from_prev_m: float = 0.0
    
    # Signal control state
    signal_states: List[SignalState] = field(default_factory=lambda: [SignalState.RED, SignalState.RED, SignalState.GREEN])
    green_duration_sec: float = 30.0
    cycle_length_sec: float = 120.0
    offset_sec: float = 0.0
    
    # Traffic state
    lane_densities: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    vehicle_composition: List[Dict[VehicleClass, int]] = field(default_factory=lambda: [{}, {}, {}])
    
    # Metadata
    is_active: bool = True
    last_update_ts: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Initialize vehicle composition dicts if empty."""
        for i in range(3):
            if not self.vehicle_composition[i]:
                self.vehicle_composition[i] = {vc: 0 for vc in VehicleClass}
    
    def get_distance_to_next(self, next_node: 'IntersectionNode') -> float:
        """Calculate geodesic distance to next node using Haversine formula."""
        R = 6371000  # Earth radius in meters
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(next_node.latitude), math.radians(next_node.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def compute_clearance_time(self, lane_idx: int) -> float:
        """
        Compute time needed to clear lane based on Indian heterogeneous traffic composition.
        
        Accounts for:
        - Mixed vehicle types with different acceleration profiles
        - Auto-rickshaw/bus platoons that clear slowly
        - Pedestrian/animal conflicts on unconstrained roads
        """
        if lane_idx >= len(self.vehicle_composition):
            return 0.0
        
        composition = self.vehicle_composition[lane_idx]
        total_clearance = 0.0
        
        for vclass, count in composition.items():
            if count > 0 and vclass in CLEARANCE_TIME_FACTORS:
                # Base clearance time per vehicle
                base_time = CLEARANCE_TIME_FACTORS[vclass]
                # Platoon effect: subsequent vehicles clear faster but not linearly
                platoon_factor = 1.0 + (count - 1) * 0.3
                total_clearance += base_time * platoon_factor
        
        # Minimum clearance for safety (pedestrian/animal buffer)
        return max(total_clearance, 5.0)
    
    def get_active_green_lane(self) -> int:
        """Return index of currently green lane, or -1 if none."""
        for i, state in enumerate(self.signal_states):
            if state == SignalState.GREEN:
                return i
        return -1
    
    def set_signal(self, lane_idx: int, state: SignalState):
        """Set signal state for specific lane, ensuring mutual exclusion."""
        # Red all lanes first
        self.signal_states = [SignalState.RED] * 3
        # Set requested lane
        if 0 <= lane_idx < 3:
            self.signal_states[lane_idx] = state
        self.last_update_ts = time.time()
    
    def trigger_preemption(self, lane_idx: int, min_green_sec: float = 30.0):
        """Emergency pre-emption: immediate green for EV lane with minimum hold time."""
        self.set_signal(lane_idx, SignalState.GREEN)
        self.green_duration_sec = max(self.green_duration_sec, min_green_sec)
        self.last_update_ts = time.time()


@dataclass
class GreenWaveSchedule:
    """
    Represents a computed green wave trigger schedule for the corridor.
    
    Attributes:
        ev_node_id: Current/nearest node to EV
        ev_lane: Lane index EV is traveling in
        ev_speed_kmph: Current EV speed
        ev_distance_to_node_m: Distance from EV to its current target node
        node_schedules: Per-node trigger timing {node_id: (trigger_time_sec, hold_duration_sec)}
        wave_speed_kmph: Effective green wave propagation speed
        total_corridor_clearance_sec: Time to clear entire corridor
        confidence: Prediction confidence 0-1
    """
    ev_node_id: str
    ev_lane: int
    ev_speed_kmph: float
    ev_distance_to_node_m: float
    node_schedules: Dict[str, Tuple[float, float]]  # node_id -> (trigger_at_sec, hold_sec)
    wave_speed_kmph: float
    total_corridor_clearance_sec: float
    confidence: float
    computed_at: float = field(default_factory=time.time)
    
    def get_trigger_for_node(self, node_id: str) -> Optional[Tuple[float, float]]:
        """Get trigger time and hold duration for a specific node."""
        return self.node_schedules.get(node_id)
    
    def get_eta_to_node(self, node_id: str) -> float:
        """Get estimated time of arrival at node (seconds from now)."""
        if node_id in self.node_schedules:
            return self.node_schedules[node_id][0]
        return float('inf')


class CorridorManager:
    """
    Metropolitan-scale corridor orchestration engine.
    
    Manages a sequence of IntersectionNodes and computes predictive green wave
    schedules for Emergency Vehicle priority transit under Indian road conditions.
    
    Key Features:
    - Optimistic planning: Pre-triggers downstream signals before EV arrival
    - Heterogeneous traffic clearance modeling (auto-rickshaws, buses, animals)
    - Dynamic adaptation to real-time density feeds
    - Fallback to mock simulation when live feeds unavailable
    - Thread-safe for concurrent WebSocket + analytics access
    """
    
    def __init__(self, corridor_name: str = "Default Corridor"):
        self.corridor_name = corridor_name
        self.nodes: Dict[str, IntersectionNode] = {}
        self.node_order: List[str] = []  # Maintains sequential order
        self._lock = threading.RLock()
        
        # EV tracking state
        self.current_ev_node_id: Optional[str] = None
        self.current_ev_lane: int = 1  # Default center lane
        self.current_ev_speed_kmph: float = 40.0
        self.current_ev_distance_m: float = 0.0
        self.ev_active: bool = False
        
        # Green wave state
        self.current_schedule: Optional[GreenWaveSchedule] = None
        self.last_schedule_update: float = 0.0
        
        # Simulation fallback
        self.mock_mode: bool = True
        self.mock_ev_position: float = 0.0  # 0.0 to 1.0 along corridor
        self.mock_ev_speed: float = 40.0
        self.mock_last_update: float = time.time()
    
    def register_node(self, node: IntersectionNode) -> None:
        """Register an intersection node in the corridor."""
        with self._lock:
            self.nodes[node.node_id] = node
            if node.node_id not in self.node_order:
                self.node_order.append(node.node_id)
            # Sort by distance from corridor start
            self.node_order.sort(key=lambda nid: self.nodes[nid].distance_from_prev_m)
    
    def build_default_corridor(self) -> None:
        """
        Build the default "Connaught Place Radial Ring Road" corridor.
        
        Three major intersections on the inner/outer circle with realistic
        Delhi coordinates and distances.
        """
        with self._lock:
            # Node-CP01: Connaught Place Inner Circle - Radial Road 1
            cp01 = IntersectionNode(
                node_id="Node-CP01",
                name="Connaught Place - Radial Road 1 (Baba Kharak Singh Marg)",
                latitude=28.6315,
                longitude=77.2167,
                distance_from_prev_m=0.0,
                offset_sec=0.0,
                cycle_length_sec=120.0,
                green_duration_sec=35.0
            )
            
            # Node-CP02: Connaught Place Middle Circle - Radial Road 3
            cp02 = IntersectionNode(
                node_id="Node-CP02",
                name="Connaught Place - Radial Road 3 (Parliament Street)",
                latitude=28.6262,
                longitude=77.2118,
                distance_from_prev_m=650.0,  # ~650m from CP01
                offset_sec=15.0,  # 15s offset for 40km/h progression
                cycle_length_sec=120.0,
                green_duration_sec=40.0
            )
            
            # Node-CP03: Connaught Place Outer Circle - Radial Road 5
            cp03 = IntersectionNode(
                node_id="Node-CP03",
                name="Connaught Place - Radial Road 5 (Tolstoy Marg)",
                latitude=28.6210,
                longitude=77.2095,
                distance_from_prev_m=620.0,  # ~620m from CP02
                offset_sec=30.0,  # 30s cumulative offset
                cycle_length_sec=120.0,
                green_duration_sec=45.0
            )
            
            self.register_node(cp01)
            self.register_node(cp02)
            self.register_node(cp03)
            
            # Set initial signal states (staggered greens for normal flow)
            cp01.set_signal(1, SignalState.GREEN)  # Center lane green
            cp02.set_signal(1, SignalState.GREEN)
            cp03.set_signal(1, SignalState.GREEN)
    
    def update_node_traffic(self, node_id: str, densities: List[float], 
                           composition: Optional[List[Dict[VehicleClass, int]]] = None) -> None:
        """Update real-time traffic state for a node (from live YOLO or mock)."""
        with self._lock:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                node.lane_densities = densities[:3] if len(densities) >= 3 else [0.0, 0.0, 0.0]
                if composition:
                    node.vehicle_composition = composition
                node.last_update_ts = time.time()
    
    def update_ev_state(self, node_id: str, lane: int, speed_kmph: float, 
                       distance_to_node_m: float, active: bool = True) -> None:
        """Update Emergency Vehicle tracking state."""
        with self._lock:
            self.current_ev_node_id = node_id
            self.current_ev_lane = max(0, min(2, lane))
            self.current_ev_speed_kmph = max(10.0, min(120.0, speed_kmph))
            self.current_ev_distance_m = max(0.0, distance_to_node_m)
            self.ev_active = active
            self.mock_mode = False  # Live EV data overrides mock
    
    def calculate_predictive_green_wave(self, ev_position_m: Optional[float] = None,
                                       ev_speed_kmph: Optional[float] = None,
                                       ev_lane: Optional[int] = None,
                                       target_node_id: Optional[str] = None) -> GreenWaveSchedule:
        """
        Compute predictive green wave trigger schedule for EV corridor transit.
        
        This is the CORE optimistic planning algorithm. It:
        1. Estimates EV arrival time at each downstream intersection
        2. Computes required clearance time for heterogeneous Indian traffic
        3. Pre-triggers signals with safety margins BEFORE EV arrives
        4. Accounts for signal cycle constraints and coordination offsets
        
        Args:
            ev_position_m: Distance from corridor start (meters). If None, uses tracked EV.
            ev_speed_kmph: EV speed. If None, uses tracked EV speed.
            ev_lane: EV lane index (0=left, 1=center, 2=right). If None, uses tracked.
            target_node_id: Specific node EV is approaching. If None, uses current.
        
        Returns:
            GreenWaveSchedule with per-node trigger times and hold durations
        """
        with self._lock:
            # Use tracked EV state if not overridden
            if ev_position_m is None:
                # Compute position from current node + distance
                if self.current_ev_node_id and self.current_ev_node_id in self.nodes:
                    current_node = self.nodes[self.current_ev_node_id]
                    # Sum distances of all previous nodes
                    pos = 0.0
                    for nid in self.node_order:
                        if nid == self.current_ev_node_id:
                            break
                        pos += self.nodes[nid].distance_from_prev_m
                    ev_position_m = pos + (current_node.distance_from_prev_m - self.current_ev_distance_m)
                else:
                    ev_position_m = self.mock_ev_position * self.get_corridor_length()
            
            if ev_speed_kmph is None:
                ev_speed_kmph = self.current_ev_speed_kmph if self.ev_active else self.mock_ev_speed
            
            if ev_lane is None:
                ev_lane = self.current_ev_lane if self.ev_active else 1
            
            ev_lane = max(0, min(2, ev_lane))
            ev_speed_kmph = max(15.0, min(100.0, ev_speed_kmph))
            
            # Find current target node (next intersection ahead of EV)
            if target_node_id is None:
                target_node_id = self._find_next_node_ahead(ev_position_m)
            
            if not target_node_id or target_node_id not in self.nodes:
                # Fallback: return empty schedule
                return GreenWaveSchedule(
                    ev_node_id="unknown",
                    ev_lane=ev_lane,
                    ev_speed_kmph=ev_speed_kmph,
                    ev_distance_to_node_m=0.0,
                    node_schedules={},
                    wave_speed_kmph=ev_speed_kmph,
                    total_corridor_clearance_sec=0.0,
                    confidence=0.0
                )
            
            # Compute schedule for all nodes from target onwards
            node_schedules = {}
            cumulative_time = 0.0
            wave_speed = ev_speed_kmph
            
            # Safety margins for Indian conditions
            PRE_TRIGGER_MARGIN_SEC = 8.0   # Trigger this many seconds BEFORE EV arrival
            MIN_HOLD_SEC = 25.0            # Minimum green hold for EV passage
            CLEARANCE_BUFFER_FACTOR = 1.3  # 30% buffer for unpredictable traffic
            
            start_idx = self.node_order.index(target_node_id)
            
            for idx in range(start_idx, len(self.node_order)):
                node_id = self.node_order[idx]
                node = self.nodes[node_id]
                
                # Distance from EV current position to this node
                if idx == start_idx:
                    distance_to_node = self.current_ev_distance_m if self.ev_active else \
                                     (node.distance_from_prev_m * (1.0 - self.mock_ev_position))
                else:
                    # Sum distances from target to this node
                    distance_to_node = sum(
                        self.nodes[self.node_order[j]].distance_from_prev_m 
                        for j in range(start_idx, idx + 1)
                    )
                    if self.ev_active and idx == start_idx:
                        distance_to_node = self.current_ev_distance_m
                
                # EV travel time to this node
                ev_speed_mps = ev_speed_kmph / 3.6
                travel_time_sec = distance_to_node / ev_speed_mps if ev_speed_mps > 0 else float('inf')
                
                # Clearance time for this node's EV lane (heterogeneous traffic)
                clearance_time = node.compute_clearance_time(ev_lane) * CLEARANCE_BUFFER_FACTOR
                
                # Required green hold: clearance + EV passage + safety margin
                ev_passage_time = (node.distance_from_prev_m / 2) / ev_speed_mps  # Approx intersection crossing
                hold_duration = max(MIN_HOLD_SEC, clearance_time + ev_passage_time + 5.0)
                
                # Trigger time: when to flip signal to GREEN (pre-emptive)
                trigger_time = travel_time_sec - PRE_TRIGGER_MARGIN_SEC
                trigger_time = max(0.0, trigger_time)  # Can't trigger in past
                
                # Adjust for signal cycle constraints (can only change at cycle boundaries)
                cycle_phase = (trigger_time + node.offset_sec) % node.cycle_length_sec
                if cycle_phase > node.cycle_length_sec - node.green_duration_sec:
                    # Too close to natural green end, wait for next cycle
                    trigger_time += (node.cycle_length_sec - cycle_phase)
                
                node_schedules[node_id] = (trigger_time + cumulative_time, hold_duration)
                cumulative_time = trigger_time + hold_duration
            
            # Total corridor clearance time
            last_node_id = self.node_order[-1]
            total_clearance = node_schedules.get(last_node_id, (0, 0))[0] + \
                             node_schedules.get(last_node_id, (0, 0))[1]
            
            # Confidence based on data freshness and mock mode
            confidence = 0.9 if not self.mock_mode else 0.6
            for node_id in self.node_order[start_idx:]:
                node = self.nodes[node_id]
                age = time.time() - node.last_update_ts
                if age > 10.0:  # Stale data
                    confidence *= 0.8
            
            schedule = GreenWaveSchedule(
                ev_node_id=target_node_id,
                ev_lane=ev_lane,
                ev_speed_kmph=ev_speed_kmph,
                ev_distance_to_node_m=self.current_ev_distance_m if self.ev_active else 0.0,
                node_schedules=node_schedules,
                wave_speed_kmph=wave_speed,
                total_corridor_clearance_sec=total_clearance,
                confidence=max(0.3, min(1.0, confidence))
            )
            
            self.current_schedule = schedule
            self.last_schedule_update = time.time()
            
            return schedule
    
    def _find_next_node_ahead(self, ev_position_m: float) -> Optional[str]:
        """Find the next intersection node ahead of EV position."""
        cumulative_dist = 0.0
        for node_id in self.node_order:
            node = self.nodes[node_id]
            cumulative_dist += node.distance_from_prev_m
            if cumulative_dist >= ev_position_m:
                return node_id
        return self.node_order[-1] if self.node_order else None
    
    def get_corridor_length(self) -> float:
        """Total corridor length in meters."""
        return sum(node.distance_from_prev_m for node in self.nodes.values())
    
    def get_node_states(self) -> Dict[str, dict]:
        """Get serializable state of all nodes for WebSocket broadcast."""
        with self._lock:
            states = {}
            for node_id, node in self.nodes.items():
                states[node_id] = {
                    "node_id": node.node_id,
                    "name": node.name,
                    "latitude": node.latitude,
                    "longitude": node.longitude,
                    "distance_from_prev_m": node.distance_from_prev_m,
                    "signal_states": [s.value for s in node.signal_states],
                    "green_duration_sec": node.green_duration_sec,
                    "cycle_length_sec": node.cycle_length_sec,
                    "offset_sec": node.offset_sec,
                    "lane_densities": node.lane_densities,
                    "vehicle_composition": {
                        str(k): v for lane in node.vehicle_composition for k, v in lane.items()
                    } if node.vehicle_composition else {},
                    "clearance_times": [node.compute_clearance_time(i) for i in range(3)],
                    "active_green_lane": node.get_active_green_lane(),
                    "is_active": node.is_active,
                    "last_update_ts": node.last_update_ts
                }
            return states
    
    def get_ev_state(self) -> dict:
        """Get current EV tracking state."""
        with self._lock:
            return {
                "active": self.ev_active,
                "node_id": self.current_ev_node_id,
                "lane": self.current_ev_lane,
                "speed_kmph": self.current_ev_speed_kmph,
                "distance_to_node_m": self.current_ev_distance_m,
                "position_ratio": self.mock_ev_position if self.mock_mode else None,
                "mock_mode": self.mock_mode
            }
    
    def get_green_wave_schedule(self) -> Optional[dict]:
        """Get current green wave schedule for frontend visualization."""
        with self._lock:
            if not self.current_schedule:
                return None
            
            sched = self.current_schedule
            return {
                "ev_node_id": sched.ev_node_id,
                "ev_lane": sched.ev_lane,
                "ev_speed_kmph": sched.ev_speed_kmph,
                "ev_distance_to_node_m": sched.ev_distance_to_node_m,
                "node_schedules": {
                    nid: {"trigger_at_sec": t, "hold_sec": h}
                    for nid, (t, h) in sched.node_schedules.items()
                },
                "wave_speed_kmph": sched.wave_speed_kmph,
                "total_corridor_clearance_sec": sched.total_corridor_clearance_sec,
                "confidence": sched.confidence,
                "computed_at": sched.computed_at
            }
    
    def execute_green_wave(self, schedule: GreenWaveSchedule) -> None:
        """
        Execute the green wave schedule by triggering signal pre-emption.
        
        In production, this would interface with hardware controllers.
        Here we update local node states immediately.
        """
        with self._lock:
            for node_id, (trigger_at, hold_sec) in schedule.node_schedules.items():
                if node_id in self.nodes:
                    node = self.nodes[node_id]
                    node.trigger_preemption(schedule.ev_lane, min_green_sec=hold_sec)
    
    def simulate_mock_ev_movement(self, dt_sec: float = 1.0) -> None:
        """
        Simulate EV movement in mock mode for demonstration.
        
        Updates mock EV position along corridor at configured speed.
        """
        with self._lock:
            if not self.mock_mode:
                return
            
            corridor_length = self.get_corridor_length()
            if corridor_length <= 0:
                return
            
            speed_mps = self.mock_ev_speed / 3.6
            distance_delta = speed_mps * dt_sec
            position_delta = distance_delta / corridor_length
            
            self.mock_ev_position = min(1.0, self.mock_ev_position + position_delta)
            
            # Loop back when reaching end
            if self.mock_ev_position >= 1.0:
                self.mock_ev_position = 0.0
            
            # Update tracked EV state from mock
            self.ev_active = True
            target_node = self._find_next_node_ahead(self.mock_ev_position * corridor_length)
            if target_node:
                self.current_ev_node_id = target_node
                node = self.nodes[target_node]
                cumulative_before = sum(
                    self.nodes[n].distance_from_prev_m 
                    for n in self.node_order[:self.node_order.index(target_node)]
                )
                self.current_ev_distance_m = max(0.0, 
                    (self.mock_ev_position * corridor_length) - cumulative_before
                )
                self.current_ev_speed_kmph = self.mock_ev_speed
                self.current_ev_lane = 1  # Center lane default
    
    def apply_schedule_to_nodes(self) -> None:
        """
        Apply current green wave schedule to node signal states.
        
        Called periodically to pre-emptively flip signals based on schedule.
        """
        with self._lock:
            if not self.current_schedule:
                return
            
            now = time.time()
            elapsed = now - self.last_schedule_update
            
            for node_id, (trigger_at, hold_sec) in self.current_schedule.node_schedules.items():
                if node_id in self.nodes:
                    node = self.nodes[node_id]
                    # If trigger time has passed (within tolerance), activate pre-emption
                    if elapsed >= trigger_at - 1.0:  # 1 sec early tolerance
                        if node.get_active_green_lane() != self.current_schedule.ev_lane:
                            node.trigger_preemption(self.current_schedule.ev_lane, hold_sec)


# Global corridor manager instance
corridor_manager = CorridorManager("Connaught Place Radial Ring Road")
corridor_manager.build_default_corridor()