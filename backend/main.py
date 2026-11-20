"""
IntelliCross - Metropolitan-Scale FastAPI Backend
=================================================
Production-ready backend for Intelligent Traffic Orchestration platform
optimized for unconstrained Indian road conditions.

Features:
- Dual-mode WebSocket: Mock simulation (default) ↔ Live YOLOv8 inference
- Metropolitan corridor management with predictive green wave
- SQLite routing history with full audit trail
- REST endpoints for offline analysis and AV integration
- Thread-safe global state management
"""

import os
import json
import math
import asyncio
import random
import time
import threading
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Local imports
from database import init_db, insert_record, get_history
from traffic_engine import (
    IDD_CLASSES, EMERGENCY_CLASSES,
    compute_lane_density, calculate_dynamic_route
)
from vision_engine import run_inference, set_live_source, get_vision_mode, get_vision_manager
from corridor_manager import (
    corridor_manager, IntersectionNode, SignalState, VehicleClass,
    GreenWaveSchedule
)

# ============================================================
# GLOBAL STATE MANAGEMENT
# ============================================================

class GlobalState:
    """
    Thread-safe global state container for dual-mode operation.
    
    MOCK MODE (default): 
    - Simulated traffic densities, EV positions
    - No external dependencies
    - Immediate startup for development/demo
    
    LIVE MODE (activated by real video source):
    - YOLOv8 inference on provided feed
    - Real-time density computation
    - Automatic fallback to mock on inference failure
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self.vision_mode: str = "mock"  # "mock" | "live" | "error"
        self.live_source: Optional[str] = None
        self.last_live_densities: List[float] = [30.0, 50.0, 40.0]
        self.last_live_composition: List[Dict[VehicleClass, int]] = [
            {vc: 0 for vc in VehicleClass} for _ in range(3)
        ]
        self.last_live_emergency_lane: Optional[int] = None
        self.last_live_detections: List[Dict] = []
        self.last_inference_ts: float = 0.0
        self.inference_error_count: int = 0
        self.mock_density_base: List[float] = [30.0, 70.0, 45.0]
        self.mock_cycle_phase: float = 0.0
    
    def set_live_mode(self, source: str) -> None:
        """Switch to live inference mode with given source."""
        with self._lock:
            self.vision_mode = "live"
            self.live_source = source
            self.inference_error_count = 0
            set_live_source(source)
    
    def set_mock_mode(self) -> None:
        """Revert to mock simulation mode."""
        with self._lock:
            self.vision_mode = "mock"
            self.live_source = None
            set_live_source(None)
    
    def update_live_densities(self, densities: List[float], 
                             composition: List[Dict[VehicleClass, int]],
                             emergency_lane: Optional[int] = None,
                             detections: Optional[List[Dict]] = None) -> None:
        """Update latest live inference results."""
        with self._lock:
            self.last_live_densities = densities[:3]
            self.last_live_composition = composition
            self.last_live_emergency_lane = emergency_lane
            if detections is not None:
                self.last_live_detections = detections
            self.last_inference_ts = time.time()
            self.inference_error_count = 0
    
    def record_inference_error(self) -> None:
        """Track consecutive inference failures for auto-fallback."""
        with self._lock:
            self.inference_error_count += 1
            if self.inference_error_count >= 5:
                self.vision_mode = "error"
                # Auto-fallback to mock after 5 failures
                self.set_mock_mode()
    
    def get_current_densities(self) -> List[float]:
        """Get current densities (live or mock)."""
        with self._lock:
            if self.vision_mode == "live" and self.last_inference_ts > 0:
                return self.last_live_densities
            return self._generate_mock_densities()
    
    def get_current_composition(self) -> List[Dict[VehicleClass, int]]:
        """Get current vehicle composition (live or mock)."""
        with self._lock:
            if self.vision_mode == "live" and self.last_inference_ts > 0:
                return self.last_live_composition
            return self._generate_mock_composition()
    
    def _generate_mock_densities(self) -> List[float]:
        """Generate realistic mock densities with Indian traffic patterns."""
        self.mock_cycle_phase += 0.15
        base = self.mock_density_base
        
        # Simulate rush hour variations
        rush_factor = 1.0 + 0.3 * abs(random.random() - 0.5)
        # Add wave-like variation per lane
        densities = []
        for i, b in enumerate(base):
            variation = 15 * random.random() * rush_factor
            wave = 10 * math.sin(self.mock_cycle_phase + i * 2.0)
            density = max(5.0, min(95.0, b * rush_factor + variation + wave))
            densities.append(round(density, 1))
        return densities
    
    def _generate_mock_composition(self) -> List[Dict[VehicleClass, int]]:
        """Generate realistic Indian traffic composition per lane."""
        compositions = []
        for lane in range(3):
            comp = {}
            # Lane 0: More heavy vehicles (left lane)
            # Lane 1: Mixed (center)
            # Lane 2: More 2-wheelers (right lane)
            if lane == 0:
                comp[VehicleClass.TRUCK] = random.randint(0, 3)
                comp[VehicleClass.BUS] = random.randint(0, 2)
                comp[VehicleClass.CAR] = random.randint(2, 6)
                comp[VehicleClass.AUTO_RICKSHAW] = random.randint(1, 4)
            elif lane == 1:
                comp[VehicleClass.CAR] = random.randint(3, 8)
                comp[VehicleClass.AUTO_RICKSHAW] = random.randint(2, 5)
                comp[VehicleClass.MOTORCYCLE] = random.randint(2, 6)
                comp[VehicleClass.BUS] = random.randint(0, 1)
            else:
                comp[VehicleClass.MOTORCYCLE] = random.randint(5, 12)
                comp[VehicleClass.AUTO_RICKSHAW] = random.randint(1, 3)
                comp[VehicleClass.CAR] = random.randint(1, 4)
            
            # Always some pedestrians in Indian conditions
            comp[VehicleClass.PEDESTRIAN] = random.randint(0, 4)
            comp[VehicleClass.ANIMAL] = random.randint(0, 1)
            
            # Fill missing classes with 0
            for vc in VehicleClass:
                if vc not in comp:
                    comp[vc] = 0
            compositions.append(comp)
        return compositions
    
    def get_vision_status(self) -> Dict[str, Any]:
        """Get current vision system status."""
        with self._lock:
            return {
                "mode": self.vision_mode,
                "source": self.live_source,
                "last_inference_ts": self.last_inference_ts,
                "error_count": self.inference_error_count,
                "is_healthy": self.vision_mode != "error"
            }


# Global state instance
global_state = GlobalState()

# Background task management
background_tasks: List[asyncio.Task] = []
shutdown_event = asyncio.Event()


# ============================================================
# PYDANTIC MODELS
# ============================================================

class AnalyzeRequest(BaseModel):
    """Request model for offline analysis endpoint."""
    source: str = Field(..., description="Video/image path or camera index")
    incoming_ev_lane: int = Field(default=1, ge=0, le=2, description="EV approach lane")


class EVStateRequest(BaseModel):
    """Request model for manual EV state update (for testing/integration)."""
    node_id: str = Field(..., description="Current nearest intersection node ID")
    lane: int = Field(..., ge=0, le=2, description="EV lane index")
    speed_kmph: float = Field(..., ge=10, le=120, description="EV speed in km/h")
    distance_to_node_m: float = Field(..., ge=0, description="Distance to intersection")
    active: bool = Field(default=True, description="Whether EV is active")


class SignalControlRequest(BaseModel):
    """Request model for manual signal control."""
    node_id: str = Field(..., description="Target intersection node ID")
    lane: int = Field(..., ge=0, le=2, description="Lane to set green")
    duration_sec: float = Field(default=30.0, ge=5, le=300, description="Green hold duration")


# ============================================================
# LIFESPAN MANAGEMENT
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    init_db()
    print("✅ IntelliCross Backend initialized")
    print(f"📍 Corridor: {corridor_manager.corridor_name}")
    print(f"🛣️  Nodes: {', '.join(corridor_manager.node_order)}")
    print(f"🔄 Vision Mode: {global_state.vision_mode.upper()}")
    
    # Start background simulation task
    sim_task = asyncio.create_task(simulation_loop())
    background_tasks.append(sim_task)
    
    yield
    
    # Shutdown
    shutdown_event.set()
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    print("🛑 IntelliCross Backend shutdown complete")


app = FastAPI(
    title="IntelliCross Metropolitan Traffic Orchestration API",
    version="4.0.0",
    description="AI-powered corridor management for unconstrained Indian roads",
    lifespan=lifespan
)

# CORS Configuration
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# BACKGROUND SIMULATION LOOP
# ============================================================

async def simulation_loop():
    """
    Background task that:
    1. Updates mock EV position in mock mode
    2. Computes predictive green wave schedules
    3. Applies schedules to corridor nodes
    4. Runs at 1Hz for real-time feel
    """
    while not shutdown_event.is_set():
        try:
            # Update mock EV movement
            corridor_manager.simulate_mock_ev_movement(dt_sec=1.0)
            
            # Get current traffic state (live or mock)
            if global_state.vision_mode == "live":
                try:
                    vm = get_vision_manager()
                    detections, densities, composition, emergency_lane = vm.get_current_detections()
                    # Push live densities, emergency lane, and detections into global state
                    global_state.update_live_densities(densities, composition, emergency_lane, detections)
                    if emergency_lane is not None:
                        corridor_manager.update_ev_state(
                            node_id=corridor_manager.node_order[0] if corridor_manager.node_order else "Node-CP01",
                            lane=emergency_lane,
                            speed_kmph=corridor_manager.current_ev_speed_kmph if corridor_manager.ev_active else 45.0,
                            distance_to_node_m=corridor_manager.current_ev_distance_m if corridor_manager.ev_active else 200.0,
                            active=True
                        )
                except Exception as ex:
                    print(f"⚠️ Live detection update error: {ex}")
                    densities = global_state.get_current_densities()
                    composition = global_state.get_current_composition()
            else:
                densities = global_state.get_current_densities()
                composition = global_state.get_current_composition()
            
            # Update all corridor nodes with current traffic
            for node_id in corridor_manager.node_order:
                corridor_manager.update_node_traffic(node_id, densities, composition)
            
            # Compute predictive green wave if EV active
            if corridor_manager.ev_active or corridor_manager.mock_mode:
                schedule = corridor_manager.calculate_predictive_green_wave()
                corridor_manager.apply_schedule_to_nodes()
            
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"⚠️ Simulation loop error: {e}")
            await asyncio.sleep(1.0)


# ============================================================
# WEBSOCKET ENDPOINT - DUAL MODE
# ============================================================

@app.websocket("/ws/traffic")
async def websocket_endpoint(websocket: WebSocket):
    """
    Dual-mode WebSocket endpoint for real-time traffic telemetry.
    
    MOCK MODE (default): 
    - Simulated densities, EV movement, green wave schedules
    - Updates at 1Hz
    
    LIVE MODE (when real source provided):
    - Streams actual YOLOv8 inference results
    - Seamlessly switches when live source configured
    - Auto-fallback to mock on inference failure
    
    Message Format:
    {
        "timestamp": "ISO8601",
        "vision_mode": "mock|live",
        "corridor": {...},
        "ev_state": {...},
        "green_wave": {...},
        "nodes": {...},
        "routing": {...}
    }
    """
    await websocket.accept()
    client_id = id(websocket)
    print(f"🔌 WebSocket client connected: {client_id}")
    
    try:
        while not shutdown_event.is_set():
            # Get vision status
            vision_status = global_state.get_vision_status()
            
            # Get current traffic data
            densities = global_state.get_current_densities()
            composition = global_state.get_current_composition()
            
            # Update corridor nodes
            for node_id in corridor_manager.node_order:
                corridor_manager.update_node_traffic(node_id, densities, composition)
            
            # Compute routing recommendation
            emergency_lane = corridor_manager.current_ev_lane if corridor_manager.ev_active else global_state.last_live_emergency_lane
            direction, speed, emergency_flag = calculate_dynamic_route(densities, emergency_lane)
            
            # Compute green wave schedule
            schedule = None
            if corridor_manager.ev_active or corridor_manager.mock_mode:
                schedule = corridor_manager.calculate_predictive_green_wave()
                corridor_manager.apply_schedule_to_nodes()
            
            # Log to database (every 5th update to avoid spam)
            if random.random() < 0.2:
                insert_record(densities, direction, speed, int(emergency_flag))
            
            # Build comprehensive payload
            payload = {
                "timestamp": datetime.now().isoformat(),
                "vision_mode": vision_status["mode"],
                "vision_healthy": vision_status["is_healthy"],
                "corridor": {
                    "name": corridor_manager.corridor_name,
                    "length_m": corridor_manager.get_corridor_length(),
                    "node_order": corridor_manager.node_order
                },
                "ev_state": corridor_manager.get_ev_state(),
                "green_wave": corridor_manager.get_green_wave_schedule(),
                "nodes": corridor_manager.get_node_states(),
                "detections": global_state.last_live_detections[:20] if global_state.vision_mode == "live" else [],
                "routing": {
                    "lane_densities": densities,
                    "recommended_direction": direction,
                    "recommended_speed_kmph": speed,
                    "emergency_detected": emergency_flag,
                    "emergency_lane": emergency_lane
                }
            }
            
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1.0)  # 1Hz update rate
            
    except WebSocketDisconnect:
        print(f"🔌 WebSocket client disconnected: {client_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


# ============================================================
# REST ENDPOINTS
# ============================================================

@app.get("/")
def root():
    """Health check and system info."""
    return {
        "system": "IntelliCross Metropolitan Traffic Orchestration",
        "version": "4.0.0",
        "status": "operational",
        "corridor": corridor_manager.corridor_name,
        "nodes": len(corridor_manager.nodes),
        "vision_mode": global_state.vision_mode,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
def health_check():
    """Detailed health check for load balancers."""
    return {
        "status": "healthy",
        "vision": global_state.get_vision_status(),
        "corridor_active": len(corridor_manager.nodes) > 0,
        "ev_active": corridor_manager.ev_active,
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/analyze")
def analyze_offline(request: AnalyzeRequest):
    """
    Offline analysis endpoint for video/image files.
    
    Runs full YOLOv8 inference pipeline on provided source.
    Returns density, routing recommendation, and emergency detection.
    """
    try:
        results = run_inference(request.source)
        if not results:
            raise HTTPException(status_code=400, detail="No frames processed")
        
        latest = results[-1]
        density = latest["density"]
        emergency_lane = latest.get("emergency_lane")
        
        direction, speed, emergency_flag = calculate_dynamic_route(density, emergency_lane)
        insert_record(density, direction, speed, int(emergency_flag))
        
        return {
            "lane_density": density,
            "recommended_direction": direction,
            "recommended_speed_kmph": speed,
            "emergency_detected": emergency_flag,
            "emergency_lane": emergency_lane,
            "frames_processed": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/vision/live")
def set_live_vision_source(source: str = Query(..., description="Camera index, RTSP URL, or video file path")):
    """
    Switch vision engine to live mode with specified source.
    
    Triggers immediate transition from mock to live inference.
    """
    try:
        # Validate source (basic check)
        if source.isdigit():
            source = int(source)  # Camera index
        
        global_state.set_live_mode(str(source))
        return {
            "status": "success",
            "mode": "live",
            "source": source,
            "message": "Live inference activated. WebSocket will stream real data."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid source: {str(e)}")


@app.post("/vision/mock")
def set_mock_vision_mode():
    """Revert to mock simulation mode."""
    global_state.set_mock_mode()
    return {
        "status": "success",
        "mode": "mock",
        "message": "Mock simulation mode activated."
    }


@app.get("/vision/status")
def get_vision_status():
    """Get current vision system status."""
    return global_state.get_vision_status()


@app.post("/ev/update")
def update_ev_state(request: EVStateRequest):
    """
    Manually update EV tracking state (for testing or external integration).
    
    Used by: CAD systems, AV fleets, manual operator input
    """
    if request.node_id not in corridor_manager.nodes:
        raise HTTPException(status_code=404, detail=f"Node {request.node_id} not found")
    
    corridor_manager.update_ev_state(
        node_id=request.node_id,
        lane=request.lane,
        speed_kmph=request.speed_kmph,
        distance_to_node_m=request.distance_to_node_m,
        active=request.active
    )
    
    # Immediately compute new green wave
    schedule = corridor_manager.calculate_predictive_green_wave()
    corridor_manager.apply_schedule_to_nodes()
    
    return {
        "status": "success",
        "ev_state": corridor_manager.get_ev_state(),
        "green_wave": corridor_manager.get_green_wave_schedule()
    }


@app.post("/signal/control")
def manual_signal_control(request: SignalControlRequest):
    """Manual signal override for operators."""
    if request.node_id not in corridor_manager.nodes:
        raise HTTPException(status_code=404, detail=f"Node {request.node_id} not found")
    
    node = corridor_manager.nodes[request.node_id]
    node.trigger_preemption(request.lane, request.duration_sec)
    
    return {
        "status": "success",
        "node_id": request.node_id,
        "lane": request.lane,
        "signal_states": [s.value for s in node.signal_states],
        "hold_duration_sec": request.duration_sec
    }


@app.get("/corridor/nodes")
def get_corridor_nodes():
    """Get all corridor node configurations."""
    return {
        "corridor": corridor_manager.corridor_name,
        "nodes": corridor_manager.get_node_states()
    }


@app.get("/corridor/schedule")
def get_green_wave_schedule():
    """Get current predictive green wave schedule."""
    schedule = corridor_manager.get_green_wave_schedule()
    if not schedule:
        return {"schedule": None, "message": "No active green wave computed"}
    return {"schedule": schedule}


@app.get("/history")
def get_routing_history(limit: int = Query(100, ge=1, le=1000)):
    """Get routing decision history from SQLite."""
    return {"history": get_history(limit)}


# ============================================================
# AUTONOMOUS VEHICLE API (Phase 7+ integration)
# ============================================================

@app.get("/av/signal-advisory")
def get_av_signal_advisory(
    node_id: str = Query(..., description="Target intersection node ID"),
    lane: int = Query(default=1, ge=0, le=2, description="Vehicle lane")
):
    """
    Direct API for Autonomous Vehicle signal advisory.
    
    Returns recommended speed and signal state for cooperative driving.
    """
    if node_id not in corridor_manager.nodes:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    node = corridor_manager.nodes[node_id]
    densities = global_state.get_current_densities()
    
    # Get signal state for requested lane
    signal_state = node.signal_states[lane].value if lane < len(node.signal_states) else "RED"
    
    # Compute advisory speed based on signal and density
    if signal_state == "GREEN":
        advisory_speed = 40.0  # Approach speed for green
    elif signal_state == "YELLOW":
        advisory_speed = 20.0  # Caution
    else:
        advisory_speed = 0.0   # Stop
    
    # Adjust for downstream green wave
    schedule = corridor_manager.get_green_wave_schedule()
    corridor_status = "CLEAR"
    if schedule and schedule["node_schedules"]:
        next_trigger = min(schedule["node_schedules"].values(), key=lambda x: x["trigger_at_sec"])
        if next_trigger["trigger_at_sec"] < 10:
            corridor_status = "GREEN_WAVE_APPROACHING"
    
    return {
        "node_id": node_id,
        "lane": lane,
        "signal_state": signal_state,
        "recommended_speed_kmph": advisory_speed,
        "corridor_status": corridor_status,
        "distance_to_stop_line_m": 50.0,  # Would come from map matching
        "timestamp": datetime.now().isoformat()
    }


# ============================================================
# IMPORT MATH (needed for mock generation)
# ============================================================

import math
from fastapi.staticfiles import StaticFiles

# ============================================================
# STATIC FILE SERVING FOR SIMULATION VIDEO
# ============================================================

# Mount the uploads directory to serve simulation videos
import os
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/simulation/video")
def get_simulation_video():
    """
    Get the simulation video URL for the dashboard.
    Returns the URL of the generated EV simulation video.
    """
    video_path = os.path.join(uploads_dir, "ev_simulation.mp4")
    if os.path.exists(video_path):
        return {
            "status": "available",
            "url": "/uploads/ev_simulation.mp4",
            "filename": "ev_simulation.mp4",
            "size_mb": round(os.path.getsize(video_path) / (1024*1024), 1),
            "description": "Realistic traffic simulation with ambulance approaching an intersection. Shows green wave pre-emption in action."
        }
    else:
        return {
            "status": "not_found",
            "url": None,
            "message": "Simulation video not generated yet. Run: python scripts/ev_video_generator.py"
        }


# ============================================================
# HOSPITAL DATABASE (for EV routing)
# ============================================================

HOSPITALS = [
    {
        "id": "HOS-001",
        "name": "AIIMS Delhi",
        "address": "Ansari Nagar, New Delhi",
        "latitude": 28.5672,
        "longitude": 77.2100,
        "capacity": 2500,
        "emergency_available": True,
        "distance_from_corridor_km": 1.2
    },
    {
        "id": "HOS-002",
        "name": "Sir Ganga Ram Hospital",
        "address": "Rajinder Nagar, New Delhi",
        "latitude": 28.6390,
        "longitude": 77.1890,
        "capacity": 1200,
        "emergency_available": True,
        "distance_from_corridor_km": 0.8
    },
    {
        "id": "HOS-003",
        "name": "Max Hospital Saket",
        "address": "Saket, New Delhi",
        "latitude": 28.5280,
        "longitude": 77.2150,
        "capacity": 800,
        "emergency_available": True,
        "distance_from_corridor_km": 2.5
    },
    {
        "id": "HOS-004",
        "name": "Apollo Hospital",
        "address": "Sarita Vihar, New Delhi",
        "latitude": 28.5280,
        "longitude": 77.2900,
        "capacity": 1500,
        "emergency_available": True,
        "distance_from_corridor_km": 3.1
    },
    {
        "id": "HOS-005",
        "name": "Fortis Hospital",
        "address": "Shalimar Bagh, New Delhi",
        "latitude": 28.7100,
        "longitude": 77.1600,
        "capacity": 600,
        "emergency_available": True,
        "distance_from_corridor_km": 4.0
    }
]


@app.get("/hospitals")
def get_hospitals():
    """Get all registered hospitals for EV routing."""
    return {
        "hospitals": HOSPITALS,
        "total": len(HOSPITALS)
    }


@app.get("/ev/route-to-hospital")
def get_ev_route_to_hospital(
    hospital_id: str = Query(..., description="Target hospital ID"),
    current_node_id: str = Query(..., description="Current EV node position")
):
    """
    Compute optimal route from current EV position to target hospital.
    Returns route through corridor nodes + traffic-impacted ETA.
    """
    # Find hospital
    hospital = next((h for h in HOSPITALS if h["id"] == hospital_id), None)
    if not hospital:
        raise HTTPException(status_code=404, detail=f"Hospital {hospital_id} not found")
    
    # Find current node position in corridor
    if current_node_id not in corridor_manager.nodes:
        raise HTTPException(status_code=404, detail=f"Node {current_node_id} not found")
    
    current_idx = corridor_manager.node_order.index(current_node_id)
    remaining_nodes = corridor_manager.node_order[current_idx:]
    
    # Build route
    route = []
    total_distance = 0
    total_clearance = 0
    
    for node_id in remaining_nodes:
        node = corridor_manager.nodes[node_id]
        dist = node.distance_from_prev_m or 0
        total_distance += dist
        
        # Estimate clearance time based on density
        densities = global_state.get_current_densities()
        avg_density = sum(densities) / 3 if densities else 50
        clearance_sec = avg_density * 0.3  # ~0.3s per density point
        
        # Add signal cycle time
        signal_cycle_sec = 120  # Default cycle
        clearance_sec += signal_cycle_sec * 0.3  # 30% of cycle
        
        total_clearance += clearance_sec
        
        route.append({
            "node_id": node_id,
            "name": node.name,
            "latitude": node.latitude,
            "longitude": node.longitude,
            "distance_from_prev_m": dist,
            "estimated_clearance_sec": round(clearance_sec, 1),
            "signal_states": [s.value for s in node.signal_states]
        })
    
    # Distance from corridor end to hospital
    corridor_end_to_hospital_km = hospital["distance_from_corridor_km"]
    corridor_end_to_hospital_m = corridor_end_to_hospital_km * 1000
    total_distance += corridor_end_to_hospital_m
    
    # Travel time at 40 km/h average
    travel_speed_kmh = 40.0
    travel_time_sec = (total_distance / 1000) / travel_speed_kmh * 3600
    total_eta_sec = travel_time_sec + total_clearance
    
    return {
        "hospital": hospital,
        "route": route,
        "total_distance_m": round(total_distance),
        "total_distance_km": round(total_distance / 1000, 1),
        "estimated_travel_time_sec": round(travel_time_sec, 1),
        "estimated_clearance_time_sec": round(total_clearance, 1),
        "total_eta_sec": round(total_eta_sec, 1),
        "total_eta_min": round(total_eta_sec / 60, 1),
        "recommended_speed_kmph": travel_speed_kmh,
        "nodes_along_route": len(route)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
