"""
IntelliCross - Automated Test Suite
Tests vision engine, traffic density, perspective lane mapping,
emergency strobe detection, green wave scheduling, and hospital routing.
"""

import sys
import os
import unittest
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from traffic_engine import (
    compute_lane_density, calculate_dynamic_route,
    calculate_perspective_lane, IDD_CLASSES, EMERGENCY_CLASSES
)
from corridor_manager import (
    CorridorManager, IntersectionNode, SignalState, VehicleClass, CLEARANCE_TIME_FACTORS
)
from vision_engine import (
    EmergencyStrobeDetector, HybridMotionDetector, _box_iou, MockGenerator
)
import database
import main


class TestTrafficEngine(unittest.TestCase):
    def test_perspective_lane_mapping(self):
        # Frame 854x480, horizon at y=182
        # Bottom of screen (depth ~0.0): Left lane < 0.38, Center 0.38-0.62, Right > 0.62
        lane_left = calculate_perspective_lane(x=200, y=450, frame_width=854, frame_height=480)
        lane_center = calculate_perspective_lane(x=427, y=450, frame_width=854, frame_height=480)
        lane_right = calculate_perspective_lane(x=700, y=450, frame_width=854, frame_height=480)
        
        self.assertEqual(lane_left, 0, "Left side of bottom should map to Lane 0")
        self.assertEqual(lane_center, 1, "Center of bottom should map to Lane 1")
        self.assertEqual(lane_right, 2, "Right side of bottom should map to Lane 2")
        
        # Near horizon (depth ~0.9): road converges between x=358 and x=495
        # An x=400 near horizon is in the left portion of the converging road
        lane_far_left = calculate_perspective_lane(x=380, y=200, frame_width=854, frame_height=480)
        lane_far_right = calculate_perspective_lane(x=470, y=200, frame_width=854, frame_height=480)
        self.assertEqual(lane_far_left, 0, "Converging left near horizon should map to Lane 0")
        self.assertEqual(lane_far_right, 2, "Converging right near horizon should map to Lane 2")

    def test_density_and_ev_extraction(self):
        dets = [
            {"x": 200, "y": 400, "class_name": "car", "confidence": 0.9},
            {"x": 210, "y": 380, "class_name": "motorcycle", "confidence": 0.85},
            {"x": 427, "y": 420, "class_name": "ambulance", "confidence": 0.95, "is_emergency": True},
            {"x": 700, "y": 400, "class_name": "truck", "confidence": 0.88}
        ]
        densities, comp, ev_lane = compute_lane_density(dets, frame_width=854, frame_height=480)
        
        self.assertEqual(len(densities), 3)
        self.assertEqual(ev_lane, 1, "Ambulance in center should identify Lane 1 as emergency lane")
        self.assertEqual(comp[1][VehicleClass.EMERGENCY], 1)
        self.assertGreater(densities[0], 0.0)

    def test_dynamic_route_emergency_override(self):
        # Heavy density in Lane 1, but EV detected in Lane 1
        density = [20.0, 85.0, 15.0]
        direction, speed, is_ev = calculate_dynamic_route(density, emergency_lane=1)
        
        self.assertTrue(is_ev)
        self.assertEqual(direction, "Straight", "Lane 1 must force Straight direction for EV")
        self.assertGreaterEqual(speed, 45.0, "EV priority route must advise high transit speed (>= 45 km/h)")

    def test_dynamic_route_normal_lowest_density(self):
        density = [60.0, 75.0, 20.0]
        direction, speed, is_ev = calculate_dynamic_route(density, emergency_lane=None)
        
        self.assertFalse(is_ev)
        self.assertEqual(direction, "Right", "Lane 2 has lowest density, direction must be Right")


class TestVisionHead(unittest.TestCase):
    def test_box_iou(self):
        boxA = [100, 100, 200, 200]
        boxB = [100, 100, 200, 200]
        self.assertAlmostEqual(_box_iou(boxA, boxB), 1.0)
        
        boxC = [300, 300, 400, 400]
        self.assertAlmostEqual(_box_iou(boxA, boxC), 0.0)
        
        boxD = [150, 150, 250, 250]
        self.assertGreater(_box_iou(boxA, boxD), 0.1)

    def test_emergency_strobe_rejection_on_solid_colors(self):
        # Solid red image (e.g. red car or red wall) without blue strobes
        solid_red = np.zeros((100, 100, 3), dtype=np.uint8)
        solid_red[:, :] = (0, 0, 220)  # BGR
        is_ev, _ = EmergencyStrobeDetector.evaluate_crop(solid_red, "car")
        self.assertFalse(is_ev, "Solid red without blue strobe must not trigger EV")

        # Solid blue image (e.g. blue bus)
        solid_blue = np.zeros((100, 100, 3), dtype=np.uint8)
        solid_blue[:, :] = (220, 0, 0)
        is_ev, _ = EmergencyStrobeDetector.evaluate_crop(solid_blue, "bus")
        self.assertFalse(is_ev, "Solid blue without red strobe must not trigger EV")

    def test_emergency_strobe_detection_on_flasher(self):
        # Synthetic emergency flasher: white body with flashing red and blue regions
        flasher = np.full((60, 60, 3), 240, dtype=np.uint8)
        # Left half red flasher
        flasher[5:20, 10:25] = (0, 0, 240)
        # Right half blue flasher
        flasher[5:20, 35:50] = (240, 0, 0)
        
        is_ev, score = EmergencyStrobeDetector.evaluate_crop(flasher, "car")
        self.assertTrue(is_ev, "Co-occurring red and blue strobes must be recognized as EV")
        self.assertGreater(score, 0.1)


class TestCorridorAndGreenWave(unittest.TestCase):
    def setUp(self):
        self.cm = CorridorManager("Test Corridor")
        self.cm.build_default_corridor()

    def test_corridor_nodes_registration(self):
        self.assertEqual(len(self.cm.nodes), 3)
        self.assertIn("Node-CP01", self.cm.nodes)
        self.assertIn("Node-CP02", self.cm.nodes)
        self.assertIn("Node-CP03", self.cm.nodes)

    def test_predictive_green_wave_calculation(self):
        # EV approaching Node-CP01 in lane 1 at 45 km/h, 200m away
        self.cm.update_ev_state("Node-CP01", lane=1, speed_kmph=45.0, distance_to_node_m=200.0, active=True)
        schedule = self.cm.calculate_predictive_green_wave()
        
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.ev_lane, 1)
        self.assertIn("Node-CP01", schedule.node_schedules)
        
        s1 = schedule.node_schedules["Node-CP01"]
        trigger_at, hold_sec = s1
        self.assertGreater(hold_sec, 20.0)
        self.assertGreaterEqual(trigger_at, 0.0)


class TestHospitalRouting(unittest.TestCase):
    def test_hospital_list(self):
        hospitals = main.get_hospitals()
        self.assertGreaterEqual(hospitals["total"], 5)
        names = [h["name"] for h in hospitals["hospitals"]]
        self.assertIn("AIIMS Delhi", names)

    def test_ev_route_calculation(self):
        route = main.get_ev_route_to_hospital("HOS-001", "Node-CP01")
        self.assertEqual(route["hospital"]["name"], "AIIMS Delhi")
        self.assertGreater(route["total_distance_km"], 0.0)
        self.assertGreater(route["total_eta_min"], 0.0)
        self.assertGreater(route["estimated_clearance_time_sec"], 0.0)


if __name__ == '__main__':
    unittest.main()
