"""
IntelliCross - YOLOv8 Vision Engine with Dual-Mode Operation
============================================================
Supports seamless switching between mock simulation and live inference.

Architecture:
- MockGenerator: Produces realistic synthetic detections for demo/development
- LiveInference: YOLOv8 inference on camera/video/RTSP streams
- VisionManager: Coordinates mode switching, health monitoring, fallback

Indian Road Optimization:
- IDD class mapping (cars, buses, trucks, motorcycles, auto-rickshaws, etc.)
- Emergency vehicle detection (ambulance, firetruck, police)
- Logical lane partitioning for unmarked roads
- Confidence filtering for noisy Indian traffic scenes
"""

import numpy as np
import threading
import time
import random
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Import traffic engine functions
from traffic_engine import compute_lane_density, IDD_CLASSES, EMERGENCY_CLASSES
from corridor_manager import VehicleClass


class VisionMode(Enum):
    MOCK = "mock"
    LIVE = "live"
    ERROR = "error"


@dataclass
class InferenceResult:
    """Single frame inference result."""
    detections: List[Dict]
    density: List[float]
    composition: List[Dict[VehicleClass, int]]
    emergency_lane: Optional[int]
    timestamp: float
    frame_shape: Tuple[int, int]
    inference_time_ms: float


class MockGenerator:
    """
    Generates realistic mock detections simulating Indian traffic.
    
    Produces:
    - Heterogeneous vehicle mix per Indian traffic surveys
    - Time-varying densities (rush hour patterns)
    - Occasional emergency vehicle injections
    - Realistic spatial distribution across lanes
    """
    
    def __init__(self, frame_width: int = 640, frame_height: int = 480):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.lane_width = frame_width / 3
        
        # Traffic pattern state
        self.time_phase = 0.0
        self.rush_hour = False
        self.emergency_injected = False
        self.emergency_timer = 0.0
        
        # Vehicle type probabilities for Indian roads (per lane)
        # Lane 0 (left): Heavy vehicles | Lane 1 (center): Mixed | Lane 2 (right): 2-wheelers
        self.lane_vehicle_probs = [
            {  # Left lane
                'truck': 0.15, 'bus': 0.10, 'car': 0.35, 
                'autorickshaw': 0.20, 'motorcycle': 0.15, 'person': 0.05
            },
            {  # Center lane
                'car': 0.40, 'autorickshaw': 0.25, 'motorcycle': 0.20,
                'bus': 0.05, 'truck': 0.05, 'person': 0.05
            },
            {  # Right lane
                'motorcycle': 0.50, 'autorickshaw': 0.20, 'car': 0.15,
                'person': 0.10, 'truck': 0.03, 'bus': 0.02
            }
        ]
    
    def generate_frame_detections(self) -> Tuple[List[Dict], List[float], List[Dict[VehicleClass, int]], Optional[int]]:
        """Generate one frame of mock detections."""
        self.time_phase += 0.1
        
        # Rush hour simulation (peak every ~30 seconds)
        rush_cycle = np.sin(self.time_phase * 0.2)
        self.rush_hour = rush_cycle > 0.5
        
        # Base vehicle count per lane (higher in rush hour)
        base_counts = [8, 10, 12] if self.rush_hour else [4, 5, 6]
        
        all_detections = []
        emergency_lane = None
        
        # Occasional emergency vehicle (every ~60 seconds)
        self.emergency_timer += 0.1
        inject_emergency = (self.emergency_timer > 60 and random.random() < 0.02)
        if inject_emergency:
            self.emergency_timer = 0
            emergency_lane = random.randint(0, 2)
        
        for lane_idx in range(3):
            # Determine number of vehicles in this lane
            count = max(1, int(base_counts[lane_idx] * (0.7 + 0.6 * random.random())))
            
            probs = self.lane_vehicle_probs[lane_idx]
            vehicle_types = list(probs.keys())
            weights = list(probs.values())
            
            for v_idx in range(count):
                # Select vehicle type
                vtype = random.choices(vehicle_types, weights=weights)[0]
                
                # Emergency override
                if v_idx == 0 and lane_idx == emergency_lane and inject_emergency:
                    vtype = random.choice(['ambulance', 'firetruck', 'police'])
                
                # Random X position within lane
                lane_start = lane_idx * self.lane_width
                lane_end = (lane_idx + 1) * self.lane_width
                x_center = random.uniform(lane_start + 20, lane_end - 20)
                
                # Random Y position (perspective effect)
                y_center = random.uniform(100, self.frame_height - 50)
                
                # Bounding box size by vehicle type
                box_sizes = {
                    'truck': (120, 80), 'bus': (140, 90), 'car': (80, 60),
                    'autorickshaw': (70, 65), 'motorcycle': (40, 50),
                    'person': (30, 60), 'ambulance': (100, 70),
                    'firetruck': (130, 85), 'police': (80, 60)
                }
                w, h = box_sizes.get(vtype, (60, 50))
                
                x1 = max(0, int(x_center - w/2))
                y1 = max(0, int(y_center - h/2))
                x2 = min(self.frame_width, int(x_center + w/2))
                y2 = min(self.frame_height, int(y_center + h/2))
                
                all_detections.append({
                    "class_id": IDD_CLASSES.index(vtype) if vtype in IDD_CLASSES else 0,
                    "class_name": vtype,
                    "confidence": round(0.7 + 0.25 * random.random(), 2),
                    "x": int(x_center),
                    "y": int(y_center),
                    "bbox": [x1, y1, x2, y2]
                })
        
        # Compute densities and composition
        density, composition, computed_emergency_lane = compute_lane_density(
            all_detections, self.frame_width
        )
        
        # Use injected emergency lane if present
        if emergency_lane is not None:
            computed_emergency_lane = emergency_lane
        
        return all_detections, density, composition, computed_emergency_lane


# ============================================================
# OPTICAL EMERGENCY STROBE & HYBRID MOTION DETECTION HEADS
# ============================================================

def _box_iou(boxA: List[int], boxB: List[int]) -> float:
    """Compute Intersection over Union between two bounding boxes [x1, y1, x2, y2]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = max(1, (boxA[2] - boxA[0]) * (boxA[3] - boxA[1]))
    boxBArea = max(1, (boxB[2] - boxB[0]) * (boxB[3] - boxB[1]))
    return interArea / float(boxAArea + boxBArea - interArea)


class EmergencyStrobeDetector:
    """
    Real-time optical detector for Emergency Vehicle light-bars, strobes, and high-contrast markings.
    Evaluates HSV saturation signatures for alternating Red (620-750nm) and Blue (450-495nm) flasher strobes.
    """
    @staticmethod
    def evaluate_crop(crop_bgr: np.ndarray, candidate_class: str = "car") -> Tuple[bool, float]:
        if crop_bgr is None or crop_bgr.size < 40:
            return False, 0.0
        
        # Non-vehicle classes can never be emergency vehicles
        if candidate_class.lower() in ['person', 'traffic light', 'backpack', 'handbag', 'bench']:
            return False, 0.0
        
        try:
            import cv2
            hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
            
            # Red flasher mask (two ranges in HSV space)
            r1 = cv2.inRange(hsv, np.array([0, 110, 90]), np.array([12, 255, 255]))
            r2 = cv2.inRange(hsv, np.array([168, 110, 90]), np.array([180, 255, 255]))
            red_mask = r1 | r2
            
            # Blue flasher mask
            blue_mask = cv2.inRange(hsv, np.array([95, 110, 90]), np.array([135, 255, 255]))
            
            total_px = max(1, crop_bgr.shape[0] * crop_bgr.shape[1])
            red_ratio = float(np.count_nonzero(red_mask)) / total_px
            blue_ratio = float(np.count_nonzero(blue_mask)) / total_px
            
            # Emergency strobe requires co-occurrence of high saturation red and blue flasher signatures
            is_ev = (red_ratio >= 0.015 and blue_ratio >= 0.012 and (red_ratio + blue_ratio) >= 0.035)
            score = (red_ratio * 2.2) + (blue_ratio * 3.2)
            return is_ev, min(1.0, score)
        except Exception:
            return False, 0.0


class HybridMotionDetector:
    """
    Adaptive background subtraction motion detector for CCTV traffic cameras.
    Bridges domain gap for geometric, synthetic, low-contrast, or distant vehicles.
    """
    def __init__(self, history: int = 120, var_threshold: int = 30):
        self.fgbg = None
        self.history = history
        self.var_threshold = var_threshold
        self.frame_count = 0
        self._init_subtractor()

    def _init_subtractor(self):
        try:
            import cv2
            self.fgbg = cv2.createBackgroundSubtractorMOG2(
                history=self.history,
                varThreshold=self.var_threshold,
                detectShadows=False
            )
        except Exception:
            self.fgbg = None

    def detect_vehicles(self, frame: np.ndarray, horizon_ratio: float = 0.38) -> List[Dict]:
        if self.fgbg is None or frame is None:
            return []
        
        try:
            import cv2
            h, w, _ = frame.shape
            horizon_y = int(h * horizon_ratio)
            
            # Focus on road region below horizon
            road_crop = frame[horizon_y:, :]
            fgmask = self.fgbg.apply(road_crop)
            self.frame_count += 1
            
            # Skip warmup frames
            if self.frame_count < 15:
                return []
                
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_DILATE, kernel, iterations=2)
            
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 100:  # Minimum vehicle bounding box area
                    continue
                
                bx, by, bw, bh = cv2.boundingRect(cnt)
                by_full = by + horizon_y
                xc = bx + bw // 2
                yc = by_full + bh // 2
                
                crop = frame[by_full:by_full + bh, bx:bx + bw]
                is_ev, ev_score = EmergencyStrobeDetector.evaluate_crop(crop)
                
                if is_ev:
                    vclass = "ambulance"
                    conf = max(0.95, 0.85 + ev_score * 0.1)
                elif bw * bh > 2200:
                    vclass = "bus" if bw > bh else "truck"
                    conf = 0.80
                elif bw < 30 and bh < 40:
                    vclass = "motorcycle"
                    conf = 0.70
                else:
                    vclass = "car"
                    conf = 0.75
                
                detections.append({
                    "class_name": vclass,
                    "confidence": conf,
                    "x": int(xc),
                    "y": int(yc),
                    "bbox": [int(bx), int(by_full), int(bx + bw), int(by_full + bh)],
                    "is_emergency": is_ev,
                    "source": "motion_head"
                })
            
            return detections
        except Exception:
            return []


class LiveInference:
    """
    Live YOLOv8 inference on video streams.
    
    Features:
    - Camera index, video file, or RTSP URL support
    - Threaded inference for non-blocking operation
    - Automatic reconnection on stream failure
    - Performance monitoring (FPS, latency)
    """
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        self.model = None
        self.cap = None
        self.source = None
        self.running = False
        self.inference_thread = None
        self.latest_result: Optional[InferenceResult] = None
        self.result_lock = threading.Lock()
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 0.0
        self.error_count = 0
        
        # Defer model loading until start() to avoid heavy imports at module import time
        # (allows mock-mode operation without OpenCV/YOLO installed)
    
    def _load_model(self):
        """Load YOLOv8 model."""
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            print(f"✅ YOLOv8 model loaded: {self.model_path}")
        except Exception as e:
            print(f"❌ Failed to load YOLOv8 model: {e}")
            self.model = None
    
    def start(self, source: Any) -> bool:
        """Start inference on given source."""
        # Ensure model is loaded when starting live inference
        self._load_model()

        if self.model is None:
            return False

        self.stop()  # Stop any existing

        self.source = source
        try:
            import cv2
            self.cap = cv2.VideoCapture(source)
            if not self.cap.isOpened():
                print(f"❌ Failed to open video source: {source}")
                return False
            
            # Set buffer size to minimize latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.running = True
            self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
            self.inference_thread.start()
            
            print(f"🎥 Live inference started on source: {source}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start inference: {e}")
            return False
    
    def stop(self):
        """Stop inference thread."""
        self.running = False
        if self.inference_thread:
            self.inference_thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.latest_result = None
    
    def _inference_loop(self):
        """Background inference loop."""
        import cv2
        motion_detector = HybridMotionDetector()
        
        while self.running and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    # Loop video files automatically or reconnect for RTSP streams
                    if isinstance(self.source, str):
                        if self.source.startswith('rtsp'):
                            time.sleep(1.0)
                            self.cap.release()
                            self.cap = cv2.VideoCapture(self.source)
                            continue
                        elif self.source.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            # Loop video file for continuous demonstration
                            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                    break
                
                # Run inference
                start_time = time.time()
                results = self.model(frame, verbose=False, conf=0.20)[0]
                
                # Parse YOLO detections
                yolo_detections = []
                for box in results.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cls = int(box.cls[0].cpu().numpy())
                    conf = float(box.conf[0].cpu().numpy())
                    
                    class_name = self.model.names[cls] if cls < len(self.model.names) else "unknown"
                    x_center = int((x1 + x2) / 2)
                    y_center = int((y1 + y2) / 2)
                    
                    # Evaluate emergency strobe on vehicle crop
                    crop = frame[max(0, int(y1)):min(frame.shape[0], int(y2)), max(0, int(x1)):min(frame.shape[1], int(x2))]
                    is_ev, ev_score = EmergencyStrobeDetector.evaluate_crop(crop, candidate_class=class_name)
                    if is_ev or class_name in EMERGENCY_CLASSES:
                        class_name = "ambulance"
                        conf = max(conf, 0.95)
                        is_ev = True
                    
                    yolo_detections.append({
                        "class_id": cls,
                        "class_name": class_name,
                        "confidence": conf,
                        "x": x_center,
                        "y": y_center,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "is_emergency": is_ev,
                        "source": "yolo"
                    })
                
                # Run hybrid motion detector for CCTV geometric/low-contrast vehicles
                motion_detections = motion_detector.detect_vehicles(frame)
                
                # Fuse detections (avoid duplicate bounding boxes)
                final_detections = list(yolo_detections)
                for m_det in motion_detections:
                    m_box = m_det["bbox"]
                    overlap = any(_box_iou(m_box, y_det["bbox"]) > 0.25 for y_det in yolo_detections)
                    if not overlap:
                        final_detections.append(m_det)
                
                inference_time = (time.time() - start_time) * 1000
                
                # Compute densities with perspective-aware lane geometry
                density, composition, emergency_lane = compute_lane_density(
                    final_detections,
                    frame.shape[1],
                    frame_height=frame.shape[0]
                )
                
                # Update FPS
                self.fps_counter += 1
                if time.time() - self.fps_timer >= 1.0:
                    self.current_fps = self.fps_counter / (time.time() - self.fps_timer)
                    self.fps_counter = 0
                    self.fps_timer = time.time()
                
                # Store result
                with self.result_lock:
                    self.latest_result = InferenceResult(
                        detections=final_detections,
                        density=density,
                        composition=composition,
                        emergency_lane=emergency_lane,
                        timestamp=time.time(),
                        frame_shape=(frame.shape[1], frame.shape[0]),
                        inference_time_ms=inference_time
                    )
                
                self.error_count = 0
                
            except Exception as e:
                self.error_count += 1
                print(f"⚠️ Inference error ({self.error_count}): {e}")
                if self.error_count > 10:
                    print("❌ Too many inference errors, stopping")
                    self.running = False
                time.sleep(0.1)
    
    def get_latest(self) -> Optional[InferenceResult]:
        """Get latest inference result (thread-safe)."""
        with self.result_lock:
            return self.latest_result
    
    def get_stats(self) -> Dict:
        """Get inference performance stats."""
        return {
            "fps": round(self.current_fps, 1),
            "error_count": self.error_count,
            "running": self.running,
            "source": str(self.source)
        }


# ============================================================
# VISION MANAGER - Dual Mode Coordinator
# ============================================================

class VisionManager:
    """
    Coordinates mock and live modes with automatic fallback.
    
    State Machine:
    MOCK -> (live source provided) -> LIVE
    LIVE -> (errors > threshold) -> MOCK (fallback)
    LIVE -> (source stopped) -> MOCK
    """
    
    def __init__(self):
        self.mode = VisionMode.MOCK
        self.mock_generator = MockGenerator()
        self.live_inference = LiveInference()
        self.current_source = None
        self.mode_lock = threading.Lock()
        
        # Callbacks for mode changes
        self.on_mode_change = None
    
    def set_mode(self, mode: VisionMode, source: Any = None):
        """Set vision mode with optional source."""
        with self.mode_lock:
            old_mode = self.mode
            
            if mode == VisionMode.LIVE and source is not None:
                # Try to start live inference
                success = self.live_inference.start(source)
                if success:
                    self.mode = VisionMode.LIVE
                    self.current_source = source
                    self.mock_generator = MockGenerator()  # Reset mock
                else:
                    self.mode = VisionMode.ERROR
                    
            elif mode == VisionMode.MOCK:
                self.live_inference.stop()
                self.mode = VisionMode.MOCK
                self.current_source = None
            
            # Notify callback
            if self.mode != old_mode and self.on_mode_change:
                try:
                    self.on_mode_change(self.mode.value, old_mode.value)
                except:
                    pass
    
    def get_current_detections(self) -> Tuple[List[Dict], List[float], List[Dict[VehicleClass, int]], Optional[int]]:
        """Get current detections based on active mode."""
        with self.mode_lock:
            if self.mode == VisionMode.LIVE:
                result = self.live_inference.get_latest()
                if result:
                    return (result.detections, result.density, 
                           result.composition, result.emergency_lane)
                else:
                    # No live data yet, fallback to mock
                    return self.mock_generator.generate_frame_detections()
            else:
                return self.mock_generator.generate_frame_detections()
    
    def get_mode(self) -> str:
        """Get current mode as string."""
        return self.mode.value
    
    def get_stats(self) -> Dict:
        """Get comprehensive vision system stats."""
        with self.mode_lock:
            stats = {
                "mode": self.mode.value,
                "source": str(self.current_source) if self.current_source else None
            }
            if self.mode == VisionMode.LIVE:
                stats.update(self.live_inference.get_stats())
            return stats


# Global vision manager instance
_vision_manager = VisionManager()
_vision_manager_lock = threading.Lock()


def get_vision_manager() -> VisionManager:
    """Get global vision manager instance."""
    return _vision_manager


def set_live_source(source: Any):
    """Switch to live mode with given source (called from main.py)."""
    with _vision_manager_lock:
        if source is None:
            _vision_manager.set_mode(VisionMode.MOCK)
        else:
            _vision_manager.set_mode(VisionMode.LIVE, source)


def get_vision_mode() -> str:
    """Get current vision mode (called from main.py)."""
    return _vision_manager.get_mode()


def run_inference(source: str) -> List[Dict]:
    """
    Offline analysis: run inference on entire video/image file.
    
    Used by /analyze endpoint for batch processing.
    Returns list of frame results.
    """
    # For offline, we use a temporary LiveInference in blocking mode
    temp_inference = LiveInference()
    
    # Handle camera index vs file path
    try:
        src = int(source) if source.isdigit() else source
    except:
        src = source
    
    if not temp_inference.start(src):
        return []
    
    results = []
    max_frames = 300  # Limit for offline analysis
    
    for _ in range(max_frames):
        result = temp_inference.get_latest()
        if result:
            results.append({
                "detections": result.detections,
                "density": result.density,
                "emergency_lane": result.emergency_lane
            })
        time.sleep(0.033)  # ~30 FPS simulation
        
        # Check if video ended
        if not temp_inference.running:
            break
    
    temp_inference.stop()
    return results


# ============================================================
# UTILITY: Draw detections on frame (for debugging/visualization)
# ============================================================

def draw_detections(frame: np.ndarray, detections: List[Dict], 
                   densities: List[float], emergency_lane: Optional[int]) -> np.ndarray:
    """
    Draw detection boxes, lane dividers, and density info on frame.
    
    Used for debug visualization and optional video output.
    """
    import cv2

    vis_frame = frame.copy()
    h, w = frame.shape[:2]
    lane_width = w / 3
    
    # Draw lane dividers
    for i in range(1, 3):
        x = int(i * lane_width)
        cv2.line(vis_frame, (x, 0), (x, h), (100, 100, 100), 2)
    
    # Draw detections
    for det in detections:
        bbox = det.get("bbox", [])
        if len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            class_name = det.get("class_name", "unknown")
            conf = det.get("confidence", 0)
            
            # Color by class
            if class_name in EMERGENCY_CLASSES:
                color = (0, 0, 255)  # Red for emergency
            elif class_name in ['bus', 'truck']:
                color = (255, 100, 0)  # Orange for heavy
            elif class_name in ['motorcycle', 'autorickshaw']:
                color = (0, 255, 255)  # Yellow for 2/3-wheelers
            else:
                color = (0, 255, 0)  # Green for cars
            
            cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, 2)
            label = f"{class_name} {conf:.2f}"
            cv2.putText(vis_frame, label, (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # Draw density info per lane
    for i in range(3):
        x_pos = int(i * lane_width + 10)
        density = densities[i] if i < len(densities) else 0
        
        # Density bar
        bar_height = int(density * 2)
        cv2.rectangle(vis_frame, (x_pos, h - 50), (x_pos + 30, h - 50 - bar_height), 
                     (0, 255, 0), -1)
        
        # Lane label
        lane_labels = ["LEFT", "CENTER", "RIGHT"]
        cv2.putText(vis_frame, f"{lane_labels[i]}: {density:.0f}%", 
                   (x_pos, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Emergency indicator
        if emergency_lane == i:
            cv2.putText(vis_frame, "🚨 EV", (x_pos, h - 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    return vis_frame