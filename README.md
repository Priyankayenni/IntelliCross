# IntelliCross 🚦
## Metropolitan-Scale Intelligent Traffic Orchestration Platform

**Production-ready computer vision-powered traffic optimization system specifically designed for unconstrained Indian road conditions.**

---

## 🎯 System Overview

IntelliCross implements a **Predictive Green Wave Engine** that proactively coordinates traffic signals across metropolitan corridors to clear high-density blockages *before* Emergency Vehicles (EVs) physically arrive. The system handles India's heterogeneous traffic mix (cars, buses, trucks, motorcycles, auto-rickshaws, pedestrians, animals) through optimistic planning and dynamic lane-less road modeling.

### Key Innovations

| Feature | Description |
|---------|-------------|
| **Optimistic Green Wave** | Pre-emptively flips downstream signals to GREEN based on EV ETA predictions |
| **Indian Traffic Modeling** | Heterogeneous clearance times per vehicle class (auto-rickshaws, buses, animals) |
| **Dual-Mode Vision** | Seamless mock ↔ live YOLOv8 switching via WebSocket |
| **Corridor Orchestration** | Multi-intersection synchronization with progressive offsets |
| **Real-Time Dashboard** | Glassmorphic React UI with pulsing EV tracker and predictive ETAs |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Tailwind)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ VideoPanel  │  │ActionDashboard│ │    CorridorTracker      │  │
│  │  (YOLO viz) │  │ (Routing/Sig) │ │  (EV Timeline + GW)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                      MapPanel (Leaflet)                      │  │
│  │         Corridor Map + EV Position + Heatmap                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬─────────────────────────────────────┘
                              │ WebSocket / REST
┌─────────────────────────────▼─────────────────────────────────────┐
│                        BACKEND (FastAPI)                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐  │
│  │ Vision Engine │ │ Traffic Engine│ │   Corridor Manager       │  │
│  │ (YOLOv8 +    │ │ (Density/     │ │ (Green Wave + EV         │  │
│  │  Mock Gen)   │ │  Routing)    │ │  Tracking)               │  │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐  │
│  │  Database    │ │ Signal Ctrl  │ │   Self-Healing / RL      │  │
│  │  (SQLite)    │ │  (Mock)      │ │   (Extensible)           │  │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
IntelliCross/
│
├── backend/
│   ├── main.py                    # FastAPI app + WebSocket endpoint
│   ├── corridor_manager.py        # Multi-intersection corridor orchestration
│   ├── traffic_engine.py          # Density & routing algorithms
│   ├── vision_engine.py           # YOLOv8 + Mock generator
│   ├── database.py                # SQLite persistence
│   ├── self_healing_engine.py     # Signal fault detection
│   ├── requirements.txt
│   └── traffic.db                 # Auto-created
│
├── frontend/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       └── components/
│           ├── Header.jsx
│           ├── VideoPanel.jsx
│           ├── ActionDashboard.jsx
│           ├── MapPanel.jsx
│           └── CorridorTracker.jsx
│
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) NVIDIA GPU for YOLOv8 acceleration

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/traffic

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## 🔌 API Endpoints

### WebSocket (Real-Time Telemetry)
```
GET /ws/traffic
```
**Streaming payload (1Hz):**
```json
{
  "timestamp": "2026-07-16T...",
  "vision_mode": "mock",
  "corridor": { "name": "Connaught Place Radial Ring Road", "length_m": 1270 },
  "ev_state": { "active": true, "node_id": "Node-CP02", "lane": 1, "speed_kmph": 45 },
  "green_wave": { 
    "node_schedules": { "Node-CP02": { "trigger_at_sec": 2.5, "hold_sec": 35 } },
    "wave_speed_kmph": 45,
    "confidence": 0.92
  },
  "nodes": { "Node-CP01": { "signal_states": ["RED","GREEN","RED"], ... } },
  "routing": { "lane_densities": [30,70,45], "recommended_direction": "Straight", ... }
}
```

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | System health & info |
| `GET` | `/health` | Detailed health check |
| `POST` | `/analyze` | Offline video/image analysis |
| `POST` | `/vision/live` | Switch to live camera/RTSP |
| `POST` | `/vision/mock` | Revert to mock mode |
| `POST` | `/ev/update` | Manual EV state injection |
| `POST` | `/signal/control` | Manual signal override |
| `GET` | `/corridor/nodes` | All node configurations |
| `GET` | `/corridor/schedule` | Current green wave schedule |
| `GET` | `/history` | Routing decision history |
| `GET` | `/av/signal-advisory` | Autonomous Vehicle API |

---

## 🛣️ Default Corridor: Connaught Place Radial Ring Road

| Node ID | Name | Coordinates | Distance | Offset |
|---------|------|-------------|----------|--------|
| `Node-CP01` | Baba Kharak Singh Marg | 28.6315, 77.2167 | 0m | 0s |
| `Node-CP02` | Parliament Street | 28.6262, 77.2118 | 650m | 15s |
| `Node-CP03` | Tolstoy Marg | 28.6210, 77.2095 | 620m | 30s |

**Total Length:** ~1.27 km | **Design Speed:** 40 km/h | **Cycle:** 120s

---

## 🧠 Indian Road Paradigm Implementation

### Vehicle Class Clearance Times
```python
CLEARANCE_TIME_FACTORS = {
    VehicleClass.CAR: 2.0s,
    VehicleClass.BUS: 4.5s,        # Slow acceleration
    VehicleClass.TRUCK: 5.0s,      # Heavy inertia
    VehicleClass.MOTORCYCLE: 1.2s, # High maneuverability
    VehicleClass.AUTO_RICKSHAW: 2.5s,  # Frequent stops
    VehicleClass.PEDESTRIAN: 3.0s, # Uncontrolled crossing
    VehicleClass.ANIMAL: 6.0s,     # Unpredictable
    VehicleClass.EMERGENCY: 1.0s,  # Priority
}
```

### Density Computation
- **3 logical lanes** for unmarked roads (left/center/right)
- **Saturation flow** per vehicle class (IRC:SP:41 compliant)
- **Emergency override** forces EV lane to priority with 40-100 km/h advisory

### Green Wave Algorithm
```
For each downstream intersection:
  1. Compute EV travel time: distance / speed
  2. Compute clearance time: Σ(vehicle_count × class_factor) × 1.3 buffer
  3. Trigger time = travel_time - 8s pre-trigger margin
  4. Align to signal cycle boundary
  5. Hold duration = max(25s, clearance + EV_passage + 5s)
```

---

## 🎨 Dashboard Features

| Component | Capabilities |
|-----------|--------------|
| **Header** | Typographic hierarchy (IntelliCross largest), system status |
| **VideoPanel** | Live YOLO detections, lane density bars, class legend, EV overlay |
| **ActionDashboard** | Routing directive, signal states, corridor intelligence, EV tracking |
| **CorridorTracker** | Vertical timeline, pulsing EV marker, ETA countdowns, trigger schedule |
| **MapPanel** | Leaflet map, node markers, EV position, green wave rings, heatmap |

**Design System:** Glassmorphism, dark mode, 8px spacing scale, Inter + JetBrains Mono fonts

---

## 🔄 Dual-Mode Operation

### Mock Mode (Default)
- Zero-configuration startup
- Realistic Indian traffic simulation
- Rush hour cycles, emergency injections
- Full dashboard functionality

### Live Mode
```bash
# Via REST API
curl -X POST "http://localhost:8000/vision/live?source=0"  # Webcam
curl -X POST "http://localhost:8000/vision/live?source=rtsp://..."  # IP Camera
curl -X POST "http://localhost:8000/vision/live?source=video.mp4"  # Video file
```
- Auto-switches on source provision
- Falls back to mock on inference failure (5 errors)
- `/vision/mock` to revert

---

## 🗄️ Database Schema

```sql
-- Routing decisions
CREATE TABLE routing_history (
    id, timestamp, lane_density, recommended_direction,
    recommended_speed, emergency_detected, emergency_lane,
    vision_mode, node_states
);

-- Emergency vehicle events
CREATE TABLE ev_events (
    id, timestamp, event_type, node_id, lane,
    speed_kmph, distance_m, green_wave_triggered, schedule_json
);

-- Signal audit trail
CREATE TABLE signal_audit (
    id, timestamp, node_id, lane, old_state, new_state,
    trigger_reason, triggered_by
);
```

---

## 🧪 Testing Offline Analysis

```bash
curl -X POST "http://localhost:8000/analyze?source=test_video.mp4&incoming_ev_lane=1"
```

Response:
```json
{
  "lane_density": [25.0, 68.0, 42.0],
  "recommended_direction": "Left",
  "recommended_speed_kmph": 52.3,
  "emergency_detected": false,
  "frames_processed": 150
}
```

---

## 🔮 Extensibility Points

| Module | Purpose | Integration |
|--------|---------|-------------|
| `self_healing_engine.py` | Signal fault detection & recovery | Auto-integrated in WebSocket loop |
| `rl_signal_agent.py` | Q-learning adaptive timing | Drop-in replacement for optimizer |
| `gnn_optimizer.py` | Graph neural network corridor opt | PyTorch Geometric compatible |
| `federated_server.py` | Cross-intersection FL aggregation | HTTP endpoint for edge nodes |
| `edge_agent.py` | Jetson Nano TensorRT deployment | Local inference + cloud sync |

---

## 📦 Production Deployment

### Docker
```dockerfile
# Backend
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes
```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intellicross-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: intellicross-backend
  template:
    spec:
      containers:
      - name: backend
        image: intellicross-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: INTELLICROSS_DEPLOYMENT
          value: "mock"
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: intellicross-backend
  ports:
  - port: 8000
    targetPort: 8000
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🙏 Acknowledgments

- **Ultralytics** for YOLOv8
- **Indian Road Congress (IRC)** for traffic engineering guidelines
- **OpenStreetMap** contributors for map data
- **Framer Motion** for animations
- **Tailwind CSS** for utility-first styling

---

**Built for Smart Cities Mission • Indian Traffic Intelligence Research • Production-Ready Architecture**

*IntelliCross v4.0 — Metropolitan-Scale Intelligent Traffic Orchestration*