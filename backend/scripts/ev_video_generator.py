"""
IntelliCross - Realistic Emergency Vehicle Simulation Video Generator
======================================================================
Generates a realistic traffic scene with an ambulance approaching an
intersection. Shows:
- Normal traffic (cars, trucks, auto-rickshaws, buses, motorcycles)
- Ambulance with flashing lights approaching from distance
- Lane-based density visualization
- Traffic clearing for the emergency vehicle

Usage:
    python scripts/ev_video_generator.py [--output output.mp4] [--duration 30]
    
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
import subprocess

# Vehicle types for the simulation
VEHICLE_TYPES = {
    'car': {'color': (180, 140, 100), 'w': 40, 'h': 20, 'speed_range': (2, 5)},
    'bus': {'color': (60, 130, 200), 'w': 55, 'h': 25, 'speed_range': (1, 3)},
    'truck': {'color': (80, 80, 120), 'w': 50, 'h': 24, 'speed_range': (1, 3)},
    'auto': {'color': (100, 200, 255), 'w': 28, 'h': 18, 'speed_range': (2, 5)},
    'motorcycle': {'color': (200, 100, 50), 'w': 20, 'h': 12, 'speed_range': (3, 7)},
    'ambulance': {'color': (50, 50, 255), 'w': 42, 'h': 22, 'speed_range': (6, 10)},
}

class TrafficSimulator:
    """Generates realistic traffic animation frames."""
    
    def __init__(self, width=640, height=480):
        self.w = width
        self.h = height
        self.frame_count = 0
        
        # Road geometry
        self.road_top = 150
        self.road_bottom = 380
        self.road_center = (self.road_top + self.road_bottom) // 2
        self.lane_height = (self.road_bottom - self.road_top) // 3
        self.lane_markers = [
            self.road_top + self.lane_height,
            self.road_top + self.lane_height * 2
        ]
        
        # Vehicles list
        self.vehicles = []
        
        # Intersection zone
        self.intersection_x = self.w // 2
        
        # Signal lights
        self.signal_states = ['GREEN', 'RED', 'RED']  # Lane 0=green, 1=red, 2=red
        self.signal_timer = 0
        self.ev_active = False
        self.ev_lane = 1  # Center lane for ambulance
        self.ev_preempted = False
        self.ev_flash_timer = 0
        
        # Background
        self.sky_color = (100, 150, 200)
        self.road_color = (60, 60, 65)
        self.road_marking_color = (200, 200, 180)
        self.sidewalk_color = (80, 80, 85)
        self.building_color = (110, 110, 120)
        
        # Spawn ambulance at frame 100
        self.ev_spawn_frame = 100
        self.ev_position = None  # Will be set later
        
        # Static background elements
        self.buildings = self._generate_buildings()
        self.trees = self._generate_trees()
        
    def _generate_buildings(self):
        buildings = []
        # Left side buildings
        for i in range(0, self.w, 50):
            h = random.randint(40, 90)
            buildings.append({
                'x': i, 'y': self.road_top - h - 10,
                'w': 45, 'h': h,
                'color': (random.randint(90, 130), random.randint(90, 130), random.randint(100, 140))
            })
        return buildings
    
    def _generate_trees(self):
        trees = []
        for i in range(0, self.w, 40):
            if random.random() < 0.4:
                trees.append({
                    'x': i + 10,
                    'y': self.road_bottom + 15,
                    'size': random.randint(15, 25)
                })
        return trees
    
    def _draw_background(self, frame):
        # Sky gradient
        for y in range(self.road_top):
            blend = y / self.road_top
            r = int(self.sky_color[0] * (1 - blend) + 140 * blend)
            g = int(self.sky_color[1] * (1 - blend) + 170 * blend)
            b = int(self.sky_color[2] * (1 - blend) + 210 * blend)
            frame[y, :] = (b, g, r)
        
        # Road
        frame[self.road_top:self.road_bottom, :] = self.road_color
        
        # Lane markings (dashed lines)
        for y_marker in self.lane_markers:
            for x in range(0, self.w, 30):
                if (x // 30) % 2 == 0:  # Dashed pattern
                    cv2.line(frame, (x, y_marker), (min(x + 15, self.w), y_marker), 
                             self.road_marking_color, 2)
        
        # Road edge lines
        cv2.line(frame, (0, self.road_top), (self.w, self.road_top), (180, 180, 160), 2)
        cv2.line(frame, (0, self.road_bottom), (self.w, self.road_bottom), (180, 180, 160), 2)
        
        # Sidewalks
        frame[self.road_top-8:self.road_top, :] = self.sidewalk_color
        frame[self.road_bottom:self.road_bottom+8, :] = self.sidewalk_color
        
        # Buildings
        for b in self.buildings:
            color = b['color']
            cv2.rectangle(frame, (b['x'], b['y']), (b['x']+b['w'], b['y']+b['h']), color, -1)
            # Windows
            for wy in range(b['y']+5, b['y']+b['h']-5, 12):
                for wx in range(b['x']+5, b['x']+b['w']-5, 12):
                    brightness = 100 + random.randint(0, 50)
                    cv2.rectangle(frame, (wx, wy), (wx+5, wy+5), 
                                 (brightness, brightness, brightness+20), -1)
        
        # Trees along sidewalk
        for t in self.trees:
            s = t['size']
            cv2.circle(frame, (t['x']+s//2, t['y']), s, (50, 130, 50), -1)
            cv2.circle(frame, (t['x']+s//2, t['y']-s//2), s-5, (40, 110, 40), -1)
        
        # Intersection markings (crosswalk)
        for x_off in range(-40, 45, 8):
            cv2.line(frame, 
                    (self.intersection_x + x_off, self.road_top),
                    (self.intersection_x + x_off, self.road_bottom),
                    (200, 200, 200), 2)
    
    def _draw_vehicle(self, frame, x, y, vtype, lane, is_ev=False):
        """Draw a simplified 2D vehicle."""
        vinfo = VEHICLE_TYPES[vtype]
        w, h = vinfo['w'], vinfo['h']
        color = vinfo['color']
        
        # Position
        x1 = int(x - w//2)
        y1 = int(y - h//2)
        x2 = int(x + w//2)
        y2 = int(y + h//2)
        
        # Vehicle body
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        
        # Windshield
        cv2.rectangle(frame, (x1+3, y1+3), (x2-3, y1+8), 
                     tuple(min(c+40, 255) for c in color), -1)
        
        # Wheels
        wheel_color = (30, 30, 30)
        cv2.circle(frame, (x1+5, y2-2), 3, wheel_color, -1)
        cv2.circle(frame, (x2-5, y2-2), 3, wheel_color, -1)
        cv2.circle(frame, (x1+5, y1+2), 3, wheel_color, -1)
        cv2.circle(frame, (x2-5, y1+2), 3, wheel_color, -1)
        
        # Roof light bar for ambulance
        if is_ev:
            flash_on = (self.ev_flash_timer % 10) < 5
            # Red light
            light_color = (0, 0, 255) if flash_on else (0, 0, 100)
            cv2.circle(frame, (x1+7, y1-4), 4, light_color, -1)
            cv2.circle(frame, (x1+7, y1-4), 7, light_color, 2)
            
            # Blue light
            light_color2 = (255, 100, 50) if not flash_on else (100, 50, 20)
            cv2.circle(frame, (x2-7, y1-4), 4, light_color2, -1)
            cv2.circle(frame, (x2-7, y1-4), 7, light_color2, 2)
            
            # Siren text
            cv2.putText(frame, "🚑", (x1-5, y1-12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # EV lane indicator - flashing border
            if flash_on:
                cv2.rectangle(frame, (x1-2, y1-2), (x2+2, y2+2), (0, 0, 255), 2)
    
    def _draw_signal(self, frame, lane_idx, state):
        """Draw traffic signal for a lane."""
        x = self.intersection_x - 20 if lane_idx < 2 else self.intersection_x + 10
        y = self.road_top - 35 - lane_idx * 10
        
        # Signal box
        cv2.rectangle(frame, (x, y), (x+16, y+40), (40, 40, 40), -1)
        cv2.rectangle(frame, (x, y), (x+16, y+40), (80, 80, 80), 1)
        
        # Red light
        red_on = state == 'RED' or state == 'YELLOW'
        cv2.circle(frame, (x+8, y+8), 5, (0, 0, 200) if red_on else (30, 30, 30), -1)
        if red_on:
            cv2.circle(frame, (x+8, y+8), 8, (0, 0, 200), 1)
        
        # Yellow light
        yellow_on = state == 'YELLOW'
        cv2.circle(frame, (x+8, y+20), 5, (0, 200, 200) if yellow_on else (30, 30, 30), -1)
        
        # Green light
        green_on = state == 'GREEN'
        cv2.circle(frame, (x+8, y+32), 5, (0, 200, 0) if green_on else (30, 30, 30), -1)
        if green_on:
            cv2.circle(frame, (x+8, y+32), 8, (0, 200, 0), 1)
    
    def _spawn_vehicle(self):
        """Spawn a random vehicle in a random lane."""
        lane = random.randint(0, 2)
        vtype = random.choice(['car', 'car', 'car', 'bus', 'truck', 'auto', 'motorcycle', 'motorcycle'])
        
        y_base = self.road_top + lane * self.lane_height + self.lane_height // 2
        
        self.vehicles.append({
            'x': self.w + 50 + random.randint(0, 100),
            'y': y_base,
            'lane': lane,
            'type': vtype,
            'speed': random.uniform(VEHICLE_TYPES[vtype]['speed_range'][0], 
                                     VEHICLE_TYPES[vtype]['speed_range'][1]),
            'active': True,
            'is_ev': False
        })
    
    def _spawn_ambulance(self):
        """Spawn emergency vehicle."""
        lane = 1  # Center lane
        y_base = self.road_top + lane * self.lane_height + self.lane_height // 2
        
        self.vehicles.append({
            'x': self.w + 30,
            'y': y_base,
            'lane': lane,
            'type': 'ambulance',
            'speed': 8.0,
            'active': True,
            'is_ev': True
        })
        self.ev_active = True
        self.ev_lane = lane
        self.ev_position = len(self.vehicles) - 1
    
    def _detect_collision(self, x, lane, exclude_idx=None):
        """Check if position collides with existing vehicle."""
        for idx, v in enumerate(self.vehicles):
            if idx == exclude_idx or not v['active']:
                continue
            if v['lane'] != lane:
                continue
            if abs(v['x'] - x) < 45:
                return True
        return False
    
    def step(self):
        """Advance simulation one frame."""
        self.frame_count += 1
        self.ev_flash_timer += 1
        
        # Create frame
        frame = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        self._draw_background(frame)
        
        # Vehicle spawn logic
        if self.frame_count < 200:  # Warm up period
            if random.random() < 0.08:
                self._spawn_vehicle()
        
        # Spawn ambulance at designated frame
        if self.frame_count == self.ev_spawn_frame:
            self._spawn_ambulance()
            print(f"[Frame {self.frame_count}] 🚑 Ambulance spawned in Lane 2 (Center)")
        
        # Update signal lights
        self.signal_timer += 1
        
        # Normal signal cycle (pre-EV)
        if not self.ev_active:
            if self.signal_timer < 120:
                self.signal_states = ['GREEN', 'RED', 'RED']
            elif self.signal_timer < 130:
                self.signal_states = ['YELLOW', 'RED', 'RED']
            elif self.signal_timer < 180:
                self.signal_states = ['RED', 'GREEN', 'RED']
            elif self.signal_timer < 190:
                self.signal_states = ['RED', 'YELLOW', 'RED']
            elif self.signal_timer < 240:
                self.signal_states = ['RED', 'RED', 'GREEN']
            else:
                self.signal_timer = 0
                self.signal_states = ['GREEN', 'RED', 'RED']
        else:
            # EV mode: pre-empt signals for EV lane
            if not self.ev_preempted:
                print(f"[Frame {self.frame_count}] 🟢 Green wave engaged for Lane 2 (EV)")
                self.ev_preempted = True
            
            # Give green to EV lane + clear adjacent lanes
            self.signal_states = ['YELLOW', 'GREEN', 'YELLOW']
            
            # Check if EV has passed intersection
            if self.ev_position is not None and self.ev_position < len(self.vehicles):
                ev = self.vehicles[self.ev_position]
                if ev['x'] < self.intersection_x - 50:
                    # EV passed, resume normal
                    pass  # Keep green for now
        
        # Draw signals
        for lane_idx, state in enumerate(self.signal_states):
            self._draw_signal(frame, lane_idx, state)
        
        # Update and draw vehicles
        vehicles_to_remove = []
        sorted_vehicles = sorted(enumerate(self.vehicles), key=lambda v: v[1]['x'], reverse=True)
        
        for idx, v in sorted_vehicles:
            if not v['active']:
                continue
            
            # Move vehicle left (toward intersection)
            v['x'] -= v['speed']
            
            # Handle signal logic
            lane = v['lane']
            signal = self.signal_states[lane]
            intersection_zone = self.intersection_x - 30
            
            # If approaching red light, slow down
            if signal == 'RED' and abs(v['x'] - intersection_zone) < 80:
                if v['x'] > intersection_zone:
                    v['speed'] *= 0.85  # Brake
                    if v['speed'] < 0.5:
                        v['speed'] = 0
            elif signal == 'GREEN' and abs(v['x'] - intersection_zone) < 80:
                # Accelerate through green
                max_speed = VEHICLE_TYPES[v['type']]['speed_range'][1]
                v['speed'] = min(max_speed, v['speed'] * 1.05)
            
            # Ambulance gets priority - clear path
            if v['is_ev']:
                # Move faster
                v['speed'] = 9.0
                # Other vehicles yield
                for other_idx, other_v in enumerate(self.vehicles):
                    if other_idx == idx or not other_v['active']:
                        continue
                    if other_v['lane'] == v['lane']:
                        dist = abs(v['x'] - other_v['x'])
                        if dist < 80 and other_v['x'] > v['x']:
                            # Vehicle ahead of ambulance - move to other lane or speed up
                            if random.random() < 0.02:
                                # Change lane
                                new_lane = random.choice([l for l in range(3) if l != other_v['lane']])
                                if not self._detect_collision(other_v['x'], new_lane, other_idx):
                                    old_y = other_v['y']
                                    other_v['lane'] = new_lane
                                    other_v['y'] = self.road_top + new_lane * self.lane_height + self.lane_height // 2
                                    print(f"[Frame {self.frame_count}] Vehicle changing lane for ambulance")
                            else:
                                other_v['speed'] = max(5, other_v['speed'] * 1.2)  # Speed up to clear
            
            # Draw vehicle
            self._draw_vehicle(frame, v['x'], v['y'], v['type'], v['lane'], v['is_ev'])
            
# Remove if off screen
            if v['x'] < -60:
                vehicles_to_remove.append(idx)
                if v['is_ev']:
                    self.ev_position = None
                    self.ev_active = False
        
        for idx in reversed(vehicles_to_remove):
            self.vehicles.pop(idx)
        
        # Update EV position reference if needed
        if self.ev_position is not None and self.ev_position >= len(self.vehicles):
            self.ev_position = None
            self.ev_active = False
        
        # Periodic vehicle spawning (reduce after EV arrives)
        spawn_rate = 0.02 if self.ev_active else 0.06
        if random.random() < spawn_rate:
            # Don't spawn in EV lane if EV is active
            if self.ev_active:
                lane = random.choice([0, 2])
            else:
                lane = random.randint(0, 2)
            
            vtype = random.choice(['car', 'car', 'bus', 'truck', 'auto', 'motorcycle'])
            y_base = self.road_top + lane * self.lane_height + self.lane_height // 2
            
            x_pos = self.w + 50 + random.randint(0, 50)
            if not self._detect_collision(x_pos, lane):
                self.vehicles.append({
                    'x': x_pos,
                    'y': y_base,
                    'lane': lane,
                    'type': vtype,
                    'speed': random.uniform(VEHICLE_TYPES[vtype]['speed_range'][0], 
                                           VEHICLE_TYPES[vtype]['speed_range'][1]),
                    'active': True,
                    'is_ev': False
                })
        
        # Draw HUD overlay
        self._draw_hud(frame)
        
        return frame
    
    def _draw_hud(self, frame):
        """Draw information overlay."""
        # Top bar
        cv2.rectangle(frame, (0, 0), (self.w, 35), (0, 0, 0, 180), -1)
        
        # Title
        cv2.putText(frame, "IntelliCross  |  Emergency Vehicle Simulation", 
                   (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Frame counter
        cv2.putText(frame, f"Frame: {self.frame_count}", 
                   (self.w - 120, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        # Lane labels
        lane_labels = ['LEFT', 'CENTER', 'RIGHT']
        for i, label in enumerate(lane_labels):
            y_pos = self.road_top + i * self.lane_height + 10
            cv2.putText(frame, f"Lane {i+1}: {label}", 
                       (10, y_pos + self.lane_height//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1)
        
        # Emergency vehicle overlay
        if self.ev_active:
            text = "🚨 EMERGENCY VEHICLE ACTIVE - GREEN WAVE ENGAGED 🚨"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            x = (self.w - text_size[0]) // 2
            
            # Warning bar
            cv2.rectangle(frame, (0, self.h - 35), (self.w, self.h), (0, 0, 200), -1)
            cv2.putText(frame, text, (x, self.h - 12), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Lane indicator
            cv2.rectangle(frame, (0, 0), (self.w, 35), (0, 0, 150), -1)
            cv2.putText(frame, f"🟢 GREEN WAVE ACTIVE  |  EV Lane: {self.ev_lane+1} (Center)  |  All other lanes: YELLOW/STOP", 
                       (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Signal status
        for i, state in enumerate(self.signal_states):
            color = (0, 200, 0) if state == 'GREEN' else (0, 0, 200) if state == 'RED' else (0, 200, 200)
            cv2.putText(frame, f"L{i+1}:{state}", 
                       (self.w - 100, self.road_top + i * self.lane_height + self.lane_height//2),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)


def main():
    parser = argparse.ArgumentParser(description='Generate IntelliCross EV simulation video')
    parser.add_argument('--output', '-o', default='ev_simulation.mp4',
                       help='Output video file path')
    parser.add_argument('--duration', '-d', type=int, default=30,
                       help='Duration in seconds (default: 30)')
    parser.add_argument('--fps', type=int, default=20,
                       help='Frames per second (default: 20)')
    parser.add_argument('--width', type=int, default=640,
                       help='Video width (default: 640)')
    parser.add_argument('--height', type=int, default=480,
                       help='Video height (default: 480)')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(output_dir, exist_ok=True)
    
    total_frames = args.duration * args.fps
    print(f"🚦 Generating IntelliCross EV Simulation Video")
    print(f"   Output: {args.output}")
    print(f"   Duration: {args.duration}s at {args.fps}fps ({total_frames} frames)")
    print(f"   Resolution: {args.width}x{args.height}")
    print()
    
# Initialize video writer - try H.264 for browser compatibility
    codecs_to_try = ['avc1', 'h264', 'H264', 'mp4v']
    writer = None
    used_fourcc = None
    for codec in codecs_to_try:
        try:
            fourcc = cv2.VideoWriter.fourcc(*codec)
            temp_writer = cv2.VideoWriter(args.output, fourcc, args.fps, (args.width, args.height))
            if temp_writer.isOpened():
                writer = temp_writer
                used_fourcc = codec
                break
            else:
                temp_writer.release()
        except:
            continue
    
    if writer is None or not writer.isOpened():
        print("Failed to create video writer with any codec!")
        return
    
    print(f"   Using codec: {used_fourcc}")
    
    # Create simulator
    sim = TrafficSimulator(args.width, args.height)
    
    # Generate frames
    for frame_idx in range(total_frames):
        frame = sim.step()
        writer.write(frame)
        
        # Progress
        if frame_idx % (args.fps * 5) == 0:
            progress = (frame_idx / total_frames) * 100
            print(f"   Progress: {progress:.0f}% ({frame_idx}/{total_frames} frames)")
    
    writer.release()
    print(f"\n✅ Video generated successfully!")
    print(f"   Saved to: {os.path.abspath(args.output)}")
    print(f"   Size: {os.path.getsize(args.output) / (1024*1024):.1f} MB")


if __name__ == '__main__':
    main()

