"""
IntelliCross - Traffic Density & Emergency Routing Logic Engine
===============================================================
Core algorithms for Indian road paradigm-compatible traffic analysis.

Indian Road Paradigm Compliance:
- Heterogeneous vehicle taxonomy (IDD classes + emergency)
- Lane-less road handling via dynamic logical lane partitioning
- Density-weighted routing with emergency override
- Speed advisory accounting for mixed traffic flow characteristics
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from corridor_manager import VehicleClass


# Indian Driving Dataset (IDD) compatible classes
IDD_CLASSES = [
    'car', 'bus', 'truck', 'motorcycle', 'rider',
    'person', 'autorickshaw', 'animal',
    'traffic sign', 'traffic light',
    'ambulance', 'firetruck', 'police'
]

# Emergency vehicle class identifiers
EMERGENCY_CLASSES = ['ambulance', 'firetruck', 'police']

# Mapping from YOLO/IDD class names to VehicleClass enum
CLASS_TO_VEHICLE_CLASS = {
    'car': VehicleClass.CAR,
    'bus': VehicleClass.BUS,
    'truck': VehicleClass.TRUCK,
    'motorcycle': VehicleClass.MOTORCYCLE,
    'rider': VehicleClass.MOTORCYCLE,
    'person': VehicleClass.PEDESTRIAN,
    'autorickshaw': VehicleClass.AUTO_RICKSHAW,
    'animal': VehicleClass.ANIMAL,
    'ambulance': VehicleClass.EMERGENCY,
    'firetruck': VehicleClass.EMERGENCY,
    'police': VehicleClass.EMERGENCY,
}


def calculate_perspective_lane(
    x: float,
    y: float,
    frame_width: int,
    frame_height: int,
    horizon_ratio: float = 0.38,
    num_lanes: int = 3
) -> int:
    """
    Calculate lane using perspective road geometry converging at the horizon.
    Accounts for pole-mounted CCTV camera angle where lanes converge towards the vanishing point.
    """
    horizon_y = frame_height * horizon_ratio
    road_bottom_left = frame_width * 0.15
    road_bottom_right = frame_width * 0.85
    road_top_left = frame_width * 0.42
    road_top_right = frame_width * 0.58
    
    # Depth ratio (0 at bottom of screen, 1 at horizon)
    if y <= horizon_y:
        depth = 1.0
    else:
        depth = (frame_height - y) / max(1.0, (frame_height - horizon_y))
    depth = max(0.0, min(1.0, depth))
    
    left_x = road_bottom_left + (road_top_left - road_bottom_left) * depth
    right_x = road_bottom_right + (road_top_right - road_bottom_right) * depth
    road_width = max(1.0, right_x - left_x)
    
    rel_x = (x - left_x) / road_width
    lane = int(rel_x * num_lanes)
    return max(0, min(num_lanes - 1, lane))


def compute_lane_density(
    detections: List[Dict],
    frame_width: int,
    num_lanes: int = 3,
    frame_height: Optional[int] = None
) -> Tuple[List[float], List[Dict[VehicleClass, int]], Optional[int]]:
    """
    Compute lane density and vehicle composition from detections.
    
    Indian Road Adaptation:
    - Logical 3-lane partitioning for unmarked roads
    - Perspective-aware lane assignment when camera geometry is available
    - Returns density %, composition per lane, and emergency lane if detected
    
    Args:
        detections: List of detection dicts with 'x', 'y', 'class_name', 'confidence', 'is_emergency'
        frame_width: Image frame width in pixels
        num_lanes: Number of logical lanes (default 3)
        frame_height: Optional frame height in pixels for perspective correction
    
    Returns:
        (density_percent_list, composition_list, emergency_lane_index_or_None)
    """
    lane_width = frame_width / num_lanes
    lane_counts = [0] * num_lanes
    lane_composition = [{vc: 0 for vc in VehicleClass} for _ in range(num_lanes)]
    emergency_lane = None
    
    for det in detections:
        x_center = det.get("x", 0)
        y_center = det.get("y", 0)
        class_name = det.get("class_name", "").lower()
        is_ev = det.get("is_emergency", False) or (class_name in EMERGENCY_CLASSES)
        
        # Determine lane index (perspective-aware if height available, else orthogonal)
        if frame_height is not None and y_center > 0:
            lane_index = calculate_perspective_lane(x_center, y_center, frame_width, frame_height, num_lanes=num_lanes)
        else:
            lane_index = min(max(0, int(x_center // lane_width)), num_lanes - 1)
            
        lane_counts[lane_index] += 1
        
        # Map to vehicle class
        vclass = VehicleClass.EMERGENCY if is_ev else CLASS_TO_VEHICLE_CLASS.get(class_name, VehicleClass.CAR)
        lane_composition[lane_index][vclass] = lane_composition[lane_index].get(vclass, 0) + 1
        
        # Check for emergency vehicle
        if is_ev:
            emergency_lane = lane_index
    
    # Convert counts to density percentage
    # Indian road saturation: ~20 vehicles per lane segment at standstill
    max_capacity = 20
    density_percent = [
        min((count / max_capacity) * 100, 100.0)
        for count in lane_counts
    ]
    
    return density_percent, lane_composition, emergency_lane


def calculate_dynamic_route(
    density_matrix: List[float],
    emergency_lane: Optional[int] = None,
    vehicle_composition: Optional[List[Dict[VehicleClass, int]]] = None
) -> Tuple[str, float, bool]:
    """
    Core emergency routing algorithm with Indian road optimization.
    
    Algorithm:
    1. If emergency vehicle detected -> FORCE that lane as priority
    2. Else -> Select lane with lowest effective density
    3. Compute speed advisory based on clearance factor & traffic composition
    
    Args:
        density_matrix: Density percentage per lane [3 lanes]
        emergency_lane: Lane index with detected EV (None if no EV)
        vehicle_composition: Optional per-lane vehicle composition for refined speed
    
    Returns:
        (direction: "Left"/"Straight"/"Right", target_speed_kmph, emergency_flag)
    """
    # Ensure valid density matrix
    if len(density_matrix) < 3:
        density_matrix = density_matrix + [0.0] * (3 - len(density_matrix))
    
    # ============================================================
    # EMERGENCY OVERRIDE LOGIC
    # ============================================================
    if emergency_lane is not None:
        emergency_lane = max(0, min(2, emergency_lane))
        
        direction_map = {0: "Left", 1: "Straight", 2: "Right"}
        direction = direction_map[emergency_lane]
        
        # Emergency speed calculation
        # Base priority speed + clearance factor bonus
        lane_density = density_matrix[emergency_lane]
        clearance_factor = 100 - lane_density
        
        # Emergency vehicles: 40-100 kmph based on clearance
        # Higher clearance = higher safe speed
        target_speed = 40 + (clearance_factor / 100) * 60  # 40-100 kmph
        
        # Cap at 100 kmph for safety on Indian roads
        target_speed = min(target_speed, 100.0)
        
        # Further adjust for heavy vehicle presence in EV lane
        if vehicle_composition and emergency_lane < len(vehicle_composition):
            comp = vehicle_composition[emergency_lane]
            heavy_count = comp.get(VehicleClass.BUS, 0) + comp.get(VehicleClass.TRUCK, 0)
            if heavy_count > 2:
                target_speed *= 0.8  # Reduce for heavy platoons
        
        return direction, round(target_speed, 1), True
    
    # ============================================================
    # NORMAL OPERATION - Density-based routing
    # ============================================================
    # Find lane with minimum density
    best_lane = int(np.argmin(density_matrix))
    
    direction_map = {0: "Left", 1: "Straight", 2: "Right"}
    direction = direction_map[best_lane]
    
    # Speed based on clearance in best lane
    clearance_factor = 100 - density_matrix[best_lane]
    
    # Normal traffic: 20-80 kmph
    target_speed = 20 + (clearance_factor / 100) * 60
    
    # Refine with vehicle composition if available
    if vehicle_composition and best_lane < len(vehicle_composition):
        comp = vehicle_composition[best_lane]
        # Heavy vehicles reduce achievable speed
        heavy_ratio = (comp.get(VehicleClass.BUS, 0) + comp.get(VehicleClass.TRUCK, 0)) / max(1, sum(comp.values()))
        target_speed *= (1.0 - 0.3 * heavy_ratio)
        
        # 2-wheelers increase throughput
        two_wheeler_ratio = (comp.get(VehicleClass.MOTORCYCLE, 0) + comp.get(VehicleClass.AUTO_RICKSHAW, 0)) / max(1, sum(comp.values()))
        target_speed *= (1.0 + 0.1 * two_wheeler_ratio)
    
    # Safety bounds for Indian conditions
    target_speed = max(15.0, min(80.0, target_speed))
    
    return direction, round(target_speed, 1), False


def compute_intersection_throughput(
    densities: List[float],
    composition: List[Dict[VehicleClass, int]],
    signal_timing: Dict[str, float]
) -> Dict[str, float]:
    """
    Compute intersection throughput metrics for adaptive signal control.
    
    Returns:
        Dict with per-lane throughput (veh/hr), delay (sec), queue length
    """
    results = {}
    cycle_length = signal_timing.get("cycle_length", 120)
    green_times = signal_timing.get("green_times", [30, 30, 30])
    
    for lane_idx in range(3):
        density = densities[lane_idx] if lane_idx < len(densities) else 0
        comp = composition[lane_idx] if lane_idx < len(composition) else {}
        
        # Effective saturation flow based on vehicle mix
        total_veh = sum(comp.values())
        if total_veh > 0:
            weighted_sat = 0
            for vclass, count in comp.items():
                from corridor_manager import SATURATION_FLOW
                weighted_sat += SATURATION_FLOW.get(vclass, 1800) * count
            saturation_flow = weighted_sat / total_veh
        else:
            saturation_flow = 1800  # Default passenger car equivalents
        
        # Green time for this lane
        green_time = green_times[lane_idx] if lane_idx < len(green_times) else 30
        
        # Capacity (veh/hr)
        capacity = saturation_flow * (green_time / cycle_length)
        
        # Demand (veh/hr) - estimate from density
        # Density % -> vehicles in 100m segment -> flow estimate
        demand = (density / 100) * 20 * 3600 / 100  # Simplified
        
        # Degree of saturation
        x = demand / capacity if capacity > 0 else 1.0
        
        # Average delay (Webster's formula approximation)
        if x < 0.95:
            delay = (cycle_length * (1 - green_time/cycle_length)**2) / (2 * (1 - x)) + \
                    (x**2 / (2 * demand * (1 - x))) if demand > 0 else 0
        else:
            delay = 999  # Oversaturated
        
        # Queue length (vehicles)
        queue = demand * delay / 3600 if delay < 999 else 999
        
        results[f"lane_{lane_idx}"] = {
            "capacity_veh_hr": round(capacity, 1),
            "demand_veh_hr": round(demand, 1),
            "degree_of_saturation": round(x, 2),
            "avg_delay_sec": round(delay, 1),
            "queue_length_veh": round(queue, 1)
        }
    
    return results


def optimize_signal_timing(
    densities: List[float],
    composition: List[Dict[VehicleClass, int]],
    cycle_length: float = 120,
    min_green: float = 10,
    lost_time: float = 12
) -> Dict[str, float]:
    """
    Optimize signal timing using Webster's method adapted for Indian traffic.
    
    Returns optimal green times per lane and cycle length.
    """
    # Critical lane flow ratios
    y_values = []
    for lane_idx in range(3):
        density = densities[lane_idx] if lane_idx < len(densities) else 0
        comp = composition[lane_idx] if lane_idx < len(composition) else {}
        
        total_veh = sum(comp.values())
        if total_veh > 0:
            weighted_sat = 0
            for vclass, count in comp.items():
                from corridor_manager import SATURATION_FLOW
                weighted_sat += SATURATION_FLOW.get(vclass, 1800) * count
            sat_flow = weighted_sat / total_veh
        else:
            sat_flow = 1800
        
        # Flow ratio y = q/s
        demand = (density / 100) * 20 * 3600 / 100
        y = demand / sat_flow if sat_flow > 0 else 0
        y_values.append(y)
    
    Y = sum(y_values)  # Total critical flow ratio
    
    # Optimal cycle length (Webster)
    if Y < 0.95:
        C_opt = (1.5 * lost_time + 5) / (1 - Y)
        C_opt = max(60, min(180, C_opt))  # Clamp to reasonable range
    else:
        C_opt = 180  # Max cycle for oversaturated
    
    # Green time allocation
    green_times = []
    available_green = C_opt - lost_time
    for y in y_values:
        g = max(min_green, (y / Y) * available_green) if Y > 0 else available_green / 3
        green_times.append(g)
    
    return {
        "cycle_length": round(C_opt),
        "green_times": [round(g) for g in green_times],
        "total_critical_ratio": round(Y, 3),
        "lost_time": lost_time
    }