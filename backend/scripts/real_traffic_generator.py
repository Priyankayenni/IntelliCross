"""
IntelliCross - REAL-WORLD Traffic Camera Simulation Generator
==============================================================
Generates a realistic CCTV-style traffic camera feed showing a
3D-perspective road scene with actual vehicles and an ambulance.

Features:
- Perspective view from a pole-mounted camera (like real traffic cams)
- Road with proper perspective, lane markings, and texture
- Realistic 3D vehicle models rendered via simple shapes
- Ambulance with flashing red/blue lights
- Traffic signal lights with realistic glow
- Vehicles that slow down/stop at red lights
- Green wave pre-emption for ambulance
- HUD overlay with time, location, detection info

Usage:
    python scripts/real_traffic_generator.py [--output output.mp4] [--duration 30]

Requirements:
    pip install numpy opencv-python
"""

import os
import sys
import argparse
import numpy as np
import cv2
import math
import random
from datetime import datetime


class RealWorldTrafficCam:
    """
    Generates a realistic CCTV traffic camera perspective.
    
    Camera is imagined as mounted ~8m high on a pole, angled down
    at a ~30-degree pitch, viewing a 3-lane urban road with an
    intersection in the distance.
    """
    
    def __init__(self, width=854, height=480):
        self.w = width
        self.h = height
        self.frame_count = 0
        self.flash_timer = 0
        
        # ========== Camera Perspective Geometry ==========
        # Horizon line (where sky meets road)
        self.horizon_y = int(height * 0.38)
        
        # Road vanishing point (center of road in perspective)
        self.vp_x = int(width * 0.5)
        self.vp_y = self.horizon_y
        
        # Road width at bottom of frame (wide - close to camera)
        self.road_bottom_left = int(width * 0.15)
        self.road_bottom_right = int(width * 0.85)
        
        # Road width at horizon (narrow - far from camera)
        self.road_top_left = self.vp_x - int(width * 0.08)
        self.road_top_right = self.vp_x + int(width * 0.08)
        
        # Lane divider points (3 lanes - 4 lines)
        self._compute_lane_geometry()
        
        # ========== Scene Elements ==========
        self.vehicles = []
        self.vehicle_id_counter = 0
        
        # Traffic signals (one per lane, at intersection)
        self.signal_lane_states = ['GREEN', 'RED', 'RED']
        self.signal_timer = 0
        self.signal_cycle_time = 180  # frames per cycle
        
        # Emergency vehicle state
        self.ev_active = False
        self.ev_lane = 1  # Center lane
        self.ev_preempted = False
        self.ev_spawn_frame = 180  # Spawn after ~9 seconds
        
        # Intersection area (stop line region)
        self.stop_line_y = self._world_to_screen_y(0.65)
        
        # Building silhouettes on sides
        self.buildings = self._generate_buildings()
        
        # Sky gradient
        self.sky_gradient = self._generate_sky()
        
        # Road texture (noise pattern)
        self.road_texture = self._generate_road_texture()
    
    def _compute_lane_geometry(self):
        """Compute lane divider lines in perspective."""
        # Lane boundaries from bottom to top
        t = np.linspace(0, 1, 20)  # 20 segments for curved perspective
        
        # Left edge, lane1-left, lane1-right/lane2-left, lane2-right/lane3-left, right edge
        self.lane_boundaries = []
        ratios = [0.0, 0.33, 0.67, 1.0]  # 3 lanes
        
        for ratio in ratios:
            xs = []
            ys = []
            for ti in t:
                # Interpolate between bottom and top widths
                left = self.road_bottom_left + (self.road_top_left - self.road_bottom_left) * ti
                right = self.road_bottom_right + (self.road_top_right - self.road_bottom_right) * ti
                x = left + (right - left) * ratio
                y = self.h - (self.h - self.horizon_y) * ti
                xs.append(int(x))
                ys.append(int(y))
            
            # Make lines curve slightly outward for realism
            for i in range(len(xs)):
                curve = 3 * math.sin(i / len(t) * math.pi)
                xs[i] += int(curve * (ratio - 0.5) * 2)
            
            self.lane_boundaries.append((xs, ys))
    
    def _world_to_screen_y(self, depth_ratio):
        """Convert world depth (0=bottom of frame, 1=horizon) to screen y."""
        return int(self.h - (self.h - self.horizon_y) * depth_ratio)
    
    def _world_to_screen_x(self, depth_ratio, lane_ratio):
        """Convert world position to screen x.
        depth_ratio: 0=bottom, 1=horizon
        lane_ratio: 0=left edge, 1=right edge
        """
        left = self.road_bottom_left + (self.road_top_left - self.road_bottom_left) * depth_ratio
        right = self.road_bottom_right + (self.road_top_right - self.road_bottom_right) * depth_ratio
        return int(left + (right - left) * lane_ratio)
    
    def _lane_to_screen(self, lane_idx, depth_ratio):
        """Get screen position for center of given lane at given depth."""
        lane_center = (lane_idx + 0.5) / 3.0
        x = self._world_to_screen_x(depth_ratio, lane_center)
        y = self._world_to_screen_y(depth_ratio)
        return x, y
    
    def _generate_sky(self):
        """Generate sky gradient image."""
        sky = np.zeros((self.horizon_y + 20, self.w, 3), dtype=np.uint8)
        for y in range(sky.shape[0]):
            # Blue sky gradient
            t = y / sky.shape[0]
            r = int(60 + 80 * t)
            g = int(100 + 100 * t)
            b = int(150 + 80 * t)
            sky[y, :] = (b, g, r)
            
            # Add some wispy clouds
            if random.random() < 0.3:
                cloud_y = y
                cloud_x = int(random.random() * self.w)
                cloud_w = random.randint(30, 80)
                cloud_h = random.randint(5, 10)
                brightness = 220 + random.randint(0, 35)
                for cx in range(cloud_x, min(cloud_x + cloud_w, self.w)):
                    for cy in range(max(0, cloud_y - cloud_h//2), min(cloud_y + cloud_h//2, sky.shape[0])):
                        dist = abs(cx - cloud_x - cloud_w//2) / (cloud_w//2)
                        if dist < 0.8:
                            sky[cy, cx] = (min(255, brightness), min(255, brightness), min(255, brightness))
        
        return sky
    
    def _generate_road_texture(self):
        """Generate road surface texture (asphalt noise)."""
        texture = np.zeros((self.h, self.w), dtype=np.uint8)
        # Asphalt noise pattern
        noise = np.random.randint(45, 70, (self.h, self.w))
        texture = noise.astype(np.uint8)
        return texture
    
    def _generate_buildings(self):
        """Generate building silhouettes along the road."""
        buildings = []
        # Left side buildings
        for i in range(5):
            dist = random.uniform(0.2, 0.9)
            height = random.randint(60, 150)
            width = random.randint(40, 80)
            x = self._world_to_screen_x(dist, -0.15) - width // 2
            y_top = self._world_to_screen_y(dist) - height
            y_bottom = self._world_to_screen_y(dist)
            
            # Only if visible
            if y_top < self.horizon_y:
                continue
                
            color_v = random.randint(70, 120)
            window_color = random.choice([
                (180, 160, 140),  # Warm light
                (200, 210, 220),  # Cool light
                (150, 150, 150),  # No light
                (200, 180, 120),  # Yellow light
            ])
            
            buildings.append({
                'x': x, 'y_top': y_top, 'y_bottom': y_bottom,
                'width': width, 'height': height,
                'wall_color': (color_v, color_v, color_v + 10),
                'window_color': window_color,
                'side': 'left'
            })
        
        # Right side buildings
        for i in range(6):
            dist = random.uniform(0.15, 0.85)
            height = random.randint(50, 130)
            width = random.randint(35, 70)
            x = self._world_to_screen_x(dist, 1.15) - width // 2
            y_top = self._world_to_screen_y(dist) - height
            y_bottom = self._world_to_screen_y(dist)
            
            if y_top < self.horizon_y:
                continue
            
            color_v = random.randint(65, 115)
            buildings.append({
                'x': x, 'y_top': y_top, 'y_bottom': y_bottom,
                'width': width, 'height': height,
                'wall_color': (color_v, color_v, color_v + 10),
                'window_color': (160, 150, 140),
                'side': 'right'
            })
        
        return buildings
    
    def _draw_road(self, frame):
        """Draw the road with perspective."""
        # Road surface
        pts = np.array([
            [self.road_bottom_left, self.h],
            [self.road_top_left, self.horizon_y],
            [self.road_top_right, self.horizon_y],
            [self.road_bottom_right, self.h]
        ], dtype=np.int32)
        
        # Fill road
        mask = np.zeros((self.h, self.w), dtype=np.uint8)
        cv2.fillPoly(mask, [pts], 255)
        
        # Apply road texture
        road_base = np.full((self.h, self.w, 3), (55, 55, 60), dtype=np.uint8)
        
        # Add texture noise
        noise = np.random.randint(-10, 10, (self.h, self.w, 3))
        road_base = np.clip(road_base.astype(np.int16) + noise, 30, 100).astype(np.uint8)
        
        # Blend road
        for c in range(3):
            frame[:, :, c] = np.where(mask > 0, road_base[:, :, c], frame[:, :, c])
        
        # Draw lane dividers with perspective
        for idx in range(1, len(self.lane_boundaries) - 1):  # Skip outer edges
            xs, ys = self.lane_boundaries[idx]
            # Draw dashed lines
            for i in range(0, len(xs) - 1, 4):
                if i % 8 < 4:  # Dash pattern
                    pt1 = (int(xs[i]), int(ys[i]))
                    pt2 = (int(xs[min(i+1, len(xs)-1)]), int(ys[min(i+1, len(ys)-1)]))
                    cv2.line(frame, pt1, pt2, (180, 180, 160), 2, cv2.LINE_AA)
        
        # Road edge lines (solid)
        for idx in [0, len(self.lane_boundaries) - 1]:
            xs, ys = self.lane_boundaries[idx]
            for i in range(len(xs) - 1):
                cv2.line(frame, (int(xs[i]), int(ys[i])), 
                        (int(xs[i+1]), int(ys[i+1])), (200, 200, 180), 3, cv2.LINE_AA)
        
        # Stop line at intersection
        stop_xs, stop_ys = self._get_horizontal_line(0.65)
        if stop_xs:
            for i in range(len(stop_xs) - 1):
                cv2.line(frame, (stop_xs[i], stop_ys[i]), 
                        (stop_xs[i+1], stop_ys[i+1]), (255, 255, 255), 3, cv2.LINE_AA)
        
        # Crosswalk stripes
        for stripe_idx in range(6):
            depth = 0.62 + stripe_idx * 0.008
            stripe_xs, stripe_ys = self._get_horizontal_line(depth)
            if stripe_xs:
                for i in range(len(stripe_xs) - 1):
                    cv2.line(frame, (stripe_xs[i], stripe_ys[i]), 
                            (stripe_xs[i+1], stripe_ys[i+1]), (255, 255, 255), 2, cv2.LINE_AA)
    
    def _get_horizontal_line(self, depth_ratio):
        """Get screen points for a horizontal line across the road at given depth."""
        xs = []
        ys = []
        left_x = self._world_to_screen_x(depth_ratio, 0.0)
        right_x = self._world_to_screen_x(depth_ratio, 1.0)
        y = self._world_to_screen_y(depth_ratio)
        
        # Add slight curve
        for i in range(10):
            t = i / 9.0
            x = int(left_x + (right_x - left_x) * t)
            curve = 2 * math.sin(t * math.pi)
            x += int(curve)
            xs.append(x)
            ys.append(y)
        
        return xs, ys
    
    def _draw_buildings(self, frame):
        """Draw building silhouettes."""
        for b in self.buildings:
            x, w = b['x'], b['width']
            yt, yb = b['y_top'], b['y_bottom']
            color = b['wall_color']
            
            # Building body
            cv2.rectangle(frame, (x, yt), (x + w, yb), color, -1)
            
            # Windows grid
            if b['side'] == 'left':
                for wy in range(yt + 10, yb - 5, 15):
                    for wx in range(x + 5, x + w - 5, 12):
                        lit = random.random() > 0.3
                        wc = b['window_color'] if lit else (40, 40, 45)
                        cv2.rectangle(frame, (wx, wy), (wx + 6, wy + 8), wc, -1)
            
            # Rooftop line
            cv2.line(frame, (x, yt), (x + w, yt), 
                    tuple(min(c + 30, 255) for c in color), 2)
    
    def _draw_vehicle(self, frame, vehicle):
        """Draw a realistic 3D-looking vehicle using perspective-adapted shapes."""
        lane = vehicle['lane']
        depth = vehicle['depth']  # 0=bottom, 1=horizon
        
        # Skip if beyond horizon
        if depth > 0.95 or depth < 0.02:
            return
        
        # Get screen position
        cx, cy = self._lane_to_screen(lane, depth)
        
        # Vehicle size based on depth (perspective scaling)
        base_w = vehicle['width']  # Width at bottom of screen
        base_h = vehicle['height']
        
        # Perspective scale
        scale = 1.0 - depth * 0.85
        w = max(4, int(base_w * scale))
        h = max(3, int(base_h * scale))
        
        # Screen position (vehicle center at cx, bottom at cy)
        x1 = int(cx - w // 2)
        y1 = int(cy - h)
        x2 = int(cx + w // 2)
        y2 = int(cy)
        
        color = vehicle['color']
        
        # Skip if off screen
        if x2 < 0 or x1 > self.w or y2 < 0 or y1 > self.h:
            return
        
        # === Vehicle Body ===
        # Roof (top portion)
        roof_inset_w = int(w * 0.15)
        roof_inset_h = int(h * 0.2)
        
        # Main body rectangle
        cv2.rectangle(frame, (x1, y1 + roof_inset_h), (x2, y2), color, -1)
        
        # Roof (slightly narrower)
        cv2.rectangle(frame, (x1 + roof_inset_w, y1), 
                     (x2 - roof_inset_w, y1 + roof_inset_h + 2),
                     tuple(min(c + 30, 255) for c in color), -1)
        
        # Windshield
        windshield_color = tuple(min(c + 60, 255) for c in color)
        cv2.rectangle(frame, 
                     (x1 + roof_inset_w + 2, y1 + 2),
                     (x2 - roof_inset_w - 2, y1 + roof_inset_h - 1),
                     windshield_color, -1)
        
        # Windshield reflection
        reflection = (200, 220, 240)
        cv2.line(frame, 
                (x1 + roof_inset_w + 3, y1 + roof_inset_h - 3),
                (x2 - roof_inset_w - 3, y1 + roof_inset_h - 3),
                reflection, 1)
        
        # === Wheels ===
        wheel_color = (25, 25, 25)
        wheel_w = max(2, w // 6)
        wheel_h = max(2, h // 6)
        
        # Front wheels
        if depth < 0.7:
            cv2.ellipse(frame, 
                       (x1 + wheel_w, y2 - wheel_h),
                       (wheel_w, wheel_h // 2), 0, 0, 360, wheel_color, -1)
            cv2.ellipse(frame,
                       (x2 - wheel_w, y2 - wheel_h),
                       (wheel_w, wheel_h // 2), 0, 0, 360, wheel_color, -1)
            
            # Rear wheels (smaller, farther)
            if h > 10:
                rear_offset = int(h * 0.2)
                cv2.ellipse(frame,
                           (x1 + wheel_w, y1 + roof_inset_h + rear_offset),
                           (wheel_w - 1, wheel_h // 2 - 1), 0, 0, 360, wheel_color, -1)
                cv2.ellipse(frame,
                           (x2 - wheel_w, y1 + roof_inset_h + rear_offset),
                           (wheel_w - 1, wheel_h // 2 - 1), 0, 0, 360, wheel_color, -1)
        
        # === Headlights / Tail lights ===
        if vehicle['type'] not in ['ambulance']:
            # Front lights
            light_color = (200, 220, 255)  # White/yellow headlights
            cv2.circle(frame, (x1 + w//4, y2 - 1), max(1, w//10), light_color, -1)
            cv2.circle(frame, (x2 - w//4, y2 - 1), max(1, w//10), light_color, -1)
            
            # Tail lights (red)
            if h > 8:
                tail_color = (0, 0, 200)
                cv2.circle(frame, (x1 + w//4, y1 + roof_inset_h + 1), 
                          max(1, w//12), tail_color, -1)
                cv2.circle(frame, (x2 - w//4, y1 + roof_inset_h + 1),
                          max(1, w//12), tail_color, -1)
        
        # === Shadow underneath ===
        if depth < 0.8:
            shadow_alpha = max(0.1, 0.3 - depth * 0.2)
            shadow_h = max(1, h // 4)
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1 - 2, y2), (x2 + 2, y2 + shadow_h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, shadow_alpha, frame, 1 - shadow_alpha, 0, frame)
        
        # === Ambulance specific details ===
        if vehicle.get('is_ev', False):
            self._draw_ambulance_details(frame, x1, y1, x2, y2, w, h, vehicle)
        
        # === Bounding box confidence (HUD-style) ===
        if vehicle.get('show_label', False):
            label = f"{vehicle['type']} {vehicle.get('confidence', 95)}%"
            label_y = max(0, y1 - 12)
            label_bg = (0, 0, 0, 150)
            
            # Draw label background
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)[0]
            cv2.rectangle(frame, 
                         (x1, label_y - 2),
                         (x1 + text_size[0] + 4, label_y + text_size[1] + 2),
                         (40, 40, 40), -1)
            
            # Label text
            label_color = (0, 255, 0) if not vehicle.get('is_ev') else (0, 0, 255)
            cv2.putText(frame, label, (x1 + 2, label_y + text_size[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, label_color, 1)
    
    def _draw_ambulance_details(self, frame, x1, y1, x2, y2, w, h, vehicle):
        """Draw ambulance-specific markings and lights."""
        # Ambulance markings (red cross + stripes)
        stripe_y = y1 + int(h * 0.45)
        
        # Red stripe
        cv2.rectangle(frame, (x1, stripe_y), (x2, stripe_y + int(h * 0.1)), (0, 0, 200), -1)
        
        # Red cross on roof
        cross_size = max(2, w // 5)
        cross_cx = (x1 + x2) // 2
        cross_cy = y1 + int(h * 0.15)
        
        # Vertical bar
        cv2.rectangle(frame, 
                     (cross_cx - cross_size//3, cross_cy - cross_size),
                     (cross_cx + cross_size//3, cross_cy + cross_size),
                     (0, 50, 200), -1)
        # Horizontal bar
        cv2.rectangle(frame,
                     (cross_cx - cross_size, cross_cy - cross_size//3),
                     (cross_cx + cross_size, cross_cy + cross_size//3),
                     (0, 50, 200), -1)
        
        # === Flashing Roof Lights ===
        flash = self.flash_timer % 15 < 8
        
        # Left light (Red)
        light_l_x = x1 + w // 4
        light_y = y1 - 2
        light_r = max(2, w // 8)
        
        if flash:
            # Red light glow
            for r in range(light_r * 3, light_r, -1):
                alpha = 0.3 - (r - light_r) / (light_r * 2) * 0.3
                cv2.circle(frame, (light_l_x, light_y), r, 
                          (0, max(0, int(alpha * 255)), 255), 
                          max(1, r // 3))
            cv2.circle(frame, (light_l_x, light_y), light_r, (0, 0, 255), -1)
        else:
            cv2.circle(frame, (light_l_x, light_y), light_r, (50, 0, 0), -1)
        
        # Right light (Blue)
        light_r_x = x2 - w // 4
        
        if not flash:
            # Blue light glow
            for r in range(light_r * 3, light_r, -1):
                alpha = 0.3 - (r - light_r) / (light_r * 2) * 0.3
                cv2.circle(frame, (light_r_x, light_y), r,
                          (255, max(0, int(alpha * 200)), 0),
                          max(1, r // 3))
            cv2.circle(frame, (light_r_x, light_y), light_r, (255, 50, 0), -1)
        else:
            cv2.circle(frame, (light_r_x, light_y), light_r, (0, 0, 50), -1)
        
        # "AMBULANCE" text on side (reversed for readability)
        text = "AMBULANCE"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.3, 1)[0]
        if text_size[0] < w * 0.8:
            text_x = x1 + (w - text_size[0]) // 2
            text_y = stripe_y - 2
            cv2.putText(frame, text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    def _draw_traffic_signals(self, frame):
        """Draw realistic traffic signal heads for each lane."""
        for lane_idx, state in enumerate(self.signal_lane_states):
            # Signal position - on right side of the road, near intersection
            depth = 0.58
            signal_x = self._world_to_screen_x(depth, 0.92 + lane_idx * 0.04)
            signal_y_base = self._world_to_screen_y(depth)
            signal_y_top = signal_y_base - 35 - lane_idx * 5
            
            # Pole
            cv2.line(frame, (signal_x, signal_y_top - 10), 
                    (signal_x, signal_y_base + 5), (60, 60, 60), 3)
            
            # Signal head box
            box_w, box_h = 14, 36
            box_x = signal_x - box_w // 2
            cv2.rectangle(frame, (box_x, signal_y_top), 
                         (box_x + box_w, signal_y_top + box_h), (30, 30, 30), -1)
            cv2.rectangle(frame, (box_x, signal_y_top),
                         (box_x + box_w, signal_y_top + box_h), (60, 60, 60), 1)
            
            # Red light (top)
            red_on = state in ['RED', 'YELLOW']
            cv2.circle(frame, (signal_x, signal_y_top + 7), 5, 
                      (0, 0, 200) if red_on else (20, 20, 20), -1)
            if red_on and state == 'RED':
                # Glow effect
                cv2.circle(frame, (signal_x, signal_y_top + 7), 8, 
                          (0, 0, 100), 2)
            
            # Yellow light (middle)
            yellow_on = state == 'YELLOW'
            cv2.circle(frame, (signal_x, signal_y_top + 18), 5,
                      (0, 200, 200) if yellow_on else (20, 20, 20), -1)
            if yellow_on:
                cv2.circle(frame, (signal_x, signal_y_top + 18), 8,
                          (0, 100, 100), 2)
            
            # Green light (bottom)
            green_on = state == 'GREEN'
            cv2.circle(frame, (signal_x, signal_y_top + 29), 5,
                      (0, 200, 0) if green_on else (20, 20, 20), -1)
            if green_on:
                cv2.circle(frame, (signal_x, signal_y_top + 29), 8,
                          (0, 100, 0), 2)
    
    def _spawn_vehicle(self):
        """Spawn a vehicle at the far end of the road."""
        lane = random.randint(0, 2)
        
        # Vehicle type distributions (Indian road mix)
        type_weights = {
            'car': 0.35,
            'bus': 0.10,
            'truck': 0.08,
            'auto': 0.15,
            'motorcycle': 0.25,
            'suv': 0.07
        }
        vtype = random.choices(
            list(type_weights.keys()),
            weights=list(type_weights.values())
        )[0]
        
        # Vehicle dimensions (in pixels at bottom of screen)
        dims = {
            'car': {'w': 42, 'h': 22, 'speed': (2.0, 4.5), 'color': (180, 140, 100)},
            'bus': {'w': 55, 'h': 30, 'speed': (1.5, 3.0), 'color': (60, 130, 200)},
            'truck': {'w': 52, 'h': 28, 'speed': (1.5, 3.0), 'color': (80, 90, 120)},
            'auto': {'w': 28, 'h': 18, 'speed': (2.5, 5.0), 'color': (100, 200, 255)},
            'motorcycle': {'w': 18, 'h': 14, 'speed': (3.0, 6.0), 'color': (200, 100, 50)},
            'suv': {'w': 45, 'h': 24, 'speed': (2.0, 4.5), 'color': (100, 120, 130)},
        }
        
        d = dims.get(vtype, dims['car'])
        
        # Vary color slightly for variety
        color = d['color']
        color = tuple(
            min(255, max(30, c + random.randint(-20, 20)))
            for c in color
        )
        
        self.vehicles.append({
            'id': self.vehicle_id_counter,
            'lane': lane,
            'depth': 0.92 + random.random() * 0.05,  # Start far away
            'type': vtype,
            'width': d['w'],
            'height': d['h'],
            'speed': random.uniform(d['speed'][0], d['speed'][1]) * 0.006,
            'color': color,
            'is_ev': False,
            'show_label': False,
            'stopped': False,
            'yield_to_ev': False
        })
        self.vehicle_id_counter += 1
    
    def _spawn_ambulance(self):
        """Spawn emergency vehicle at far end."""
        vehicle = {
            'id': self.vehicle_id_counter,
            'lane': 1,  # Center lane
            'depth': 0.9,
            'type': 'ambulance',
            'width': 44,
            'height': 24,
            'speed': 0.035,  # Fast
            'color': (50, 50, 255),  # White with red markings
            'is_ev': True,
            'show_label': True,
            'confidence': 97,
            'stopped': False,
            'yield_to_ev': False
        }
        self.vehicle_id_counter += 1
        self.vehicles.append(vehicle)
        self.ev_active = True
        print(f"[Frame {self.frame_count}] 🚑 AMBULANCE ENTERING FRAME - Center Lane")
    
    def update(self):
        """Advance simulation one frame."""
        self.frame_count += 1
        self.flash_timer += 1
        
        # ========== Vehicle Spawning ==========
        # Warm up traffic before ambulance
        if self.frame_count < self.ev_spawn_frame:
            if self.frame_count % 15 == 0:
                if random.random() < 0.6:
                    self._spawn_vehicle()
        else:
            # After ambulance, spawn less traffic
            if random.random() < 0.08:
                self._spawn_vehicle()
        
        # Spawn ambulance
        if self.frame_count == self.ev_spawn_frame:
            self._spawn_ambulance()
        
        # ========== Traffic Signal Logic ==========
        self.signal_timer += 1
        
        if not self.ev_active:
            # Normal cycle
            if self.signal_timer < 120:
                self.signal_lane_states = ['GREEN', 'RED', 'RED']
            elif self.signal_timer < 130:
                self.signal_lane_states = ['YELLOW', 'RED', 'RED']
            elif self.signal_timer < 180:
                self.signal_lane_states = ['RED', 'GREEN', 'RED']
            elif self.signal_timer < 190:
                self.signal_lane_states = ['RED', 'YELLOW', 'RED']
            elif self.signal_timer < 240:
                self.signal_lane_states = ['RED', 'RED', 'GREEN']
            else:
                self.signal_timer = 0
                self.signal_lane_states = ['GREEN', 'RED', 'RED']
        else:
            # EV Pre-emption
            if not self.ev_preempted:
                print(f"[Frame {self.frame_count}] 🟢 GREEN WAVE PRE-EMPTION ACTIVE")
                self.ev_preempted = True
            
            # EV Lane gets green, others yellow
            self.signal_lane_states = ['YELLOW', 'GREEN', 'YELLOW']
        
        # ========== Update Vehicles ==========
        stop_line_depth = 0.40
        
        for v in self.vehicles:
            if v.get('stopped'):
                continue
            
            # Move vehicle forward (decrease depth - moving toward camera)
            v['depth'] -= v['speed']
            
            # Signal response
            lane_state = self.signal_lane_states[v['lane']]
            
            # Emergency vehicle bypasses all signals
            if v.get('is_ev'):
                continue
            
            # Check if approaching red light at stop line
            if lane_state == 'RED' and abs(v['depth'] - stop_line_depth) < 0.15:
                if v['depth'] > stop_line_depth:
                    v['speed'] *= 0.85  # Brake
                    if v['speed'] < 0.001:
                        v['stopped'] = True
                        v['depth'] = stop_line_depth + 0.02
            elif lane_state == 'GREEN' and abs(v['depth'] - stop_line_depth) < 0.15:
                # Accelerate through green
                v['speed'] = min(v['speed'] * 1.05, 0.04)
            
            # Yield to emergency vehicle
            if self.ev_active and not v.get('is_ev'):
                # Check if EV is behind in same lane
                for other in self.vehicles:
                    if other.get('is_ev') and other['lane'] == v['lane']:
                        if other['depth'] < v['depth']:  # EV is behind
                            dist = v['depth'] - other['depth']
                            if dist < 0.15:
                                # Move to adjacent lane or speed up
                                if random.random() < 0.015:
                                    # Lane change
                                    new_lane = random.choice(
                                        [l for l in range(3) if l != v['lane']]
                                    )
                                    v['lane'] = new_lane
                                else:
                                    v['speed'] = min(v['speed'] * 1.3, 0.04)
        
        # Remove vehicles that passed the camera
        self.vehicles = [v for v in self.vehicles if v['depth'] > -0.05]
        
        # ========== Render Frame ==========
        frame = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        
        # Sky
        frame[:self.horizon_y + 10, :] = self.sky_gradient[:self.horizon_y + 10, :]
        
        # Road and markings
        self._draw_road(frame)
        
        # Buildings
        self._draw_buildings(frame)
        
        # Traffic signals
        self._draw_traffic_signals(frame)
        
        # Sort vehicles by depth (far to near) for proper occlusion
        sorted_vehicles = sorted(self.vehicles, key=lambda v: v['depth'])
        
        for v in sorted_vehicles:
            self._draw_vehicle(frame, v)
        
        # ========== HUD Overlay ==========
        self._draw_hud(frame)
        
        # Add subtle camera artifacts
        self._add_camera_effects(frame)
        
        return frame
    
    def _draw_hud(self, frame):
        """Draw realistic HUD overlay like a real traffic camera system."""
        # Top bar - semi-transparent
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.w, 36), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # System title
        cv2.putText(frame, "IntelliCross Traffic Camera  |  CP Radial Ring Road", 
                   (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 220, 255), 1)
        
        # Date/time
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, time_str, 
                   (self.w - 160, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 200, 220), 1)
        
        # Frame info
        cv2.putText(frame, f"F: {self.frame_count} | 20 FPS", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 170, 190), 1)
        
        # Camera ID
        cv2.putText(frame, "CAM-01 | CCTV-FEED", 
                   (self.w - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 170, 190), 1)
        
        # Bottom bar - detection stats
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, self.h - 30), (self.w, self.h), (0, 0, 0), -1)
        cv2.addWeighted(overlay2, 0.6, frame, 0.4, 0, frame)
        
        # Vehicle count
        active_vehicles = len(self.vehicles)
        ev_count = sum(1 for v in self.vehicles if v.get('is_ev'))
        cv2.putText(frame, f"Detected: {active_vehicles} vehicles  |  {ev_count} Emergency",
                   (10, self.h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 100), 1)
        
        # Lane densities (simulated)
        lane_counts = [sum(1 for v in self.vehicles if v['lane'] == i and not v.get('is_ev')) 
                      for i in range(3)]
        lane_labels = ['L-Lane', 'C-Lane', 'R-Lane']
        density_str = "  |  ".join(
            f"{lbl}: {cnt}" for lbl, cnt in zip(lane_labels, lane_counts)
        )
        cv2.putText(frame, f"Densities:  {density_str}",
                   (self.w - 380, self.h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 100), 1)
        
        # Signal states
        signal_colors = {
            'GREEN': (0, 255, 0),
            'RED': (0, 0, 255),
            'YELLOW': (0, 255, 255)
        }
        signal_str = "  |  ".join(
            f"L{i+1}:{s}" for i, s in enumerate(self.signal_lane_states)
        )
        cv2.putText(frame, f"Signals:  {signal_str}",
                   (self.w // 2 - 130, 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, 
                   signal_colors.get(self.signal_lane_states[1], (255, 255, 255)), 1)
        
        # Emergency vehicle banner
        if self.ev_active:
            # Top warning banner
            banner_text = "🚨 EMERGENCY VEHICLE INBOUND  |  GREEN WAVE ACTIVE  |  CLEAR CENTER LANE"
            text_size = cv2.getTextSize(banner_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            x = (self.w - text_size[0]) // 2
            
            overlay3 = frame.copy()
            cv2.rectangle(overlay3, (0, self.h - 50), (self.w, self.h - 30), (0, 0, 200), -1)
            cv2.addWeighted(overlay3, 0.7, frame, 0.3, 0, frame)
            
            # Flashing effect
            if self.flash_timer % 10 < 5:
                cv2.putText(frame, banner_text, (x, self.h - 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2)
            
            # EV lane indicator
            cv2.putText(frame, f"<<< AMBULANCE APPROACHING - LANE {self.ev_lane + 1} >>>",
                       (10, self.h - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    
    def _add_camera_effects(self, frame):
        """Add subtle artifacts to make it look like a real camera feed."""
        # 1. Subtle vignette (darkening at edges)
        rows, cols = frame.shape[:2]
        kernel_x = cv2.getGaussianKernel(cols, cols * 0.6)
        kernel_y = cv2.getGaussianKernel(rows, rows * 0.6)
        kernel = kernel_y * kernel_x.T
        mask = kernel / kernel.max()
        mask = np.clip(mask * 1.3 - 0.3, 0, 1)
        
        for c in range(3):
            frame[:, :, c] = (frame[:, :, c] * mask).astype(np.uint8)
        
        # 2. Slight noise (sensor noise)
        noise = np.random.randint(-3, 4, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # 3. Sharpening (camera processing)
        kernel_sharpen = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        frame = cv2.filter2D(frame, -1, kernel_sharpen)
        
        # 4. Slight color boost (like real traffic cameras)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= 1.1  # Saturation boost
        hsv[:, :, 2] *= 1.05  # Value boost
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def main():
    parser = argparse.ArgumentParser(
        description='Generate IntelliCross REAL-WORLD traffic camera simulation'
    )
    parser.add_argument('--output', '-o', default='uploads/ev_simulation.mp4',
                       help='Output video file path')
    parser.add_argument('--duration', '-d', type=int, default=40,
                       help='Duration in seconds (default: 40)')
    parser.add_argument('--fps', type=int, default=20,
                       help='Frames per second (default: 20)')
    parser.add_argument('--width', type=int, default=854,
                       help='Video width (default: 854)')
    parser.add_argument('--height', type=int, default=480,
                       help='Video height (default: 480)')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(os.path.abspath(args.output)) or '.'
    os.makedirs(output_dir, exist_ok=True)
    
    total_frames = args.duration * args.fps
    print(f"🎥 Generating REAL-WORLD Traffic Camera Simulation")
    print(f"   Output: {args.output}")
    print(f"   Duration: {args.duration}s at {args.fps}fps ({total_frames} frames)")
    print(f"   Resolution: {args.width}x{args.height}")
    print(f"   Style: CCTV pole-mounted camera perspective")
    print()
    
    # Initialize video writer with XVID (most compatible with browsers)
    writer = None
    for codec in ['XVID', 'mp4v', 'MJPG']:
        try:
            fourcc = cv2.VideoWriter.fourcc(*codec)
            temp = cv2.VideoWriter(args.output, fourcc, args.fps, (args.width, args.height))
            if temp.isOpened():
                writer = temp
                print(f"   Using codec: {codec}")
                break
            temp.release()
        except:
            continue
    
    if writer is None:
        print("❌ Failed to create video writer!")
        return
    
    # Create camera simulator
    cam = RealWorldTrafficCam(args.width, args.height)
    
    # Generate frames
    for frame_idx in range(total_frames):
        frame = cam.update()
        writer.write(frame)
        
        # Progress reporting
        if frame_idx % (args.fps * 5) == 0:
            progress = (frame_idx / total_frames) * 100
            print(f"   Progress: {progress:.0f}% ({frame_idx}/{total_frames} frames)")
    
    writer.release()
    file_size = os.path.getsize(args.output) / (1024 * 1024)
    print(f"\n✅ Real-world traffic camera video generated!")
    print(f"   📁 Saved to: {os.path.abspath(args.output)}")
    print(f"   📦 Size: {file_size:.1f} MB")
    print(f"   ⏱️  Duration: {args.duration}s at {args.fps}fps")
    print()
    print("   The video shows:")
    print("   - 🏙️  Realistic CCTV camera perspective of a 3-lane urban road")
    print("   - 🚗  Cars, buses, trucks, auto-rickshaws, motorcycles")
    print("   - 🚑  Ambulance with flashing red/blue lights approaching")
    print("   - 🚦  Traffic signals with green wave pre-emption")
    print("   - 📊  HUD overlay with per-frame detection statistics")
    print("   - 🎨  Camera effects: vignette, noise, sharpening")


if __name__ == '__main__':
    main()
