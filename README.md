# IntelliCross

IntelliCross is a smart emergency response and intelligent traffic monitoring platform designed to detect emergency vehicles in real time, prioritize route clearance, and support faster emergency response coordination. The system combines a modern React frontend, a FastAPI backend, and a YOLO-based detection pipeline to simulate and support situational awareness for emergency operations.

The project is built as a full-stack demo platform for emergency vehicle detection, traffic signal preemption, hospital routing, and control-room visualization. It is designed to help visualize how AI-assisted emergency response systems can improve response times, improve signal coordination, and support emergency dispatch decisions.

## Project Overview

The IntelliCross system includes:
- A React dashboard for monitoring emergency vehicles and traffic conditions
- Real-time traffic signal and hospital panel views
- Emergency detection results with confidence scoring and bounding boxes
- Simulated corridor-based emergency routing logic
- Backend services for image-based detection and live alert processing
- A Python AI pipeline for collecting, labeling, and training detection models

This project demonstrates a practical AI-powered emergency infrastructure concept for smart cities, emergency response, and transportation safety.

## Why This Project Matters

Emergency vehicles such as ambulances, fire trucks, and police vehicles often face delays caused by traffic congestion, poor route coordination, or signal delays. IntelliCross addresses this by creating a connected decision-support system that can:
- detect emergency vehicles from camera feeds or images,
- highlight them as high-priority objects,
- display their location and route progress,
- suggest hospitals or response corridors,
- and support real-time operational awareness for traffic control teams.

## Core Features

### 1. Emergency Vehicle Detection
- Detects emergency classes such as ambulance, fire truck, police, and disaster vehicles
- Uses YOLO-based object detection logic with confidence-aware predictions
- Supports detection overlays on uploaded images and simulated video frames
- Flags high-priority emergency detection cases visually

### 2. Real-Time Dashboard
- Traffic signal panel with status indicators and countdowns
- Emergency corridors and vehicle route tracking
- Regional hospital information with bed availability and response times
- Control-room style visual monitoring interface

### 3. Signals and Emergency Routing
- Simulates traffic signals with preemption logic
- Tracks vehicle proximity to intersections and corridor radius
- Provides operational context for emergency vehicles moving through monitored zones

### 4. Inference API
- FastAPI endpoints for health checks, image detection, and alert workflows
- Provides consistent JSON outputs for detection and system status
- Supports both mock and model-based detection flows

### 5. AI Data Pipeline
- Collects publicly available emergency vehicle training data
- Extracts frames and labels from video or image sources
- Organizes a YOLO dataset structure
- Trains or stubs a model for emergency detection workflows

## System Architecture

The project is divided into two main parts:

### Frontend
Built with React + Vite + TypeScript and styled with Tailwind CSS.

Main frontend responsibilities:
- display live emergency dashboard information,
- render maps and traffic panels,
- show vehicle cards and hospital cards,
- overlay detection boxes on images,
- allow users to upload images for demo detection.

### Backend
Built with Python and FastAPI.

Main backend responsibilities:
- serve API routes,
- process uploaded images or streams,
- execute detection logic,
- expose health checks and system metrics,
- support alerting and monitoring flows.

## Project Structure

```text
project/
├── README.md
├── index.html
├── package.json
├── package-lock.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── postcss.config.js
├── tailwind.config.js
├── eslint.config.js
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── data.ts
│   ├── detection.ts
│   ├── index.css
│   └── components/
│       ├── AlertTray.tsx
│       ├── ContactPanel.tsx
│       ├── DetectionPanel.tsx
│       ├── DriverView.tsx
│       ├── EmergencyHeader.tsx
│       ├── HospitalCard.tsx
│       ├── IncidentTimeline.tsx
│       ├── LiveVideoFeed.tsx
│       ├── RealTimeMap.tsx
│       ├── TrafficSignalPanel.tsx
│       ├── VehicleCard.tsx
│
├── backend/
│   ├── README.md
│   ├── main.py
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── collect_web_data.py
│   │   ├── extract_frames.py
│   │   └── train_model.py
│   └── tests/
│       ├── __init__.py
│       ├── test_collector.py
│       ├── test_extractor.py
│       └── test_integration.py
└── .gitignore
```

## Tech Stack

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- Framer Motion
- Leaflet and React Leaflet
- Lucide React icons

### Backend
- Python
- FastAPI
- Uvicorn
- OpenCV
- NumPy
- Pillow
- Pydantic
- Ultralytics
- PyTorch

### AI / Detection Pipeline
- YOLOv8-based object detection
- Emergency vehicle classification
- Mock detection mode for frontend demo operation
- Training-ready dataset generation flow

## Application Workflow

### 1. Frontend loads dashboard
The application starts with a control-room dashboard showing:
- emergency vehicles,
- hospital availability,
- traffic signals,
- status cards,
- live event logs.

### 2. User uploads an image
The detection panel allows the user to upload an image for analysis.

### 3. Detection engine runs
The system processes the image and identifies objects, such as:
- ambulance,
- fire_truck,
- police,
- car,
- bus,
- truck,
- motorcycle,
- pedestrian,
- animal.

### 4. Detection results are displayed
The detection output includes:
- class name,
- confidence score,
- bounding box coordinates,
- severity/emergency flag,
- top class summary.

### 5. Emergency logic is surfaced
If an emergency vehicle is detected, the UI highlights it and presents it as a high-priority signal for response coordination.

## API Endpoints

The backend exposes these core routes:

- `GET /health` — returns health and model status
- `POST /api/detect-image` — analyzes an uploaded image
- `POST /api/detect-stream` — analyzes a video stream or uploaded video
- `GET /api/hospitals` — returns known emergency hospitals
- `GET /api/signals` — returns traffic signal data
- `GET /api/corridors` — returns emergency corridor locations
- `POST /api/alerts` — creates alert data
- `POST /api/contact` — logs contact attempts
- WebSocket endpoints for live alert streams and vehicle updates

## Example Detection Output

```json
{
  "detections": [
    {
      "class_name": "ambulance",
      "class_id": 0,
      "confidence": 0.94,
      "bbox": { "x1": 100, "y1": 50, "x2": 250, "y2": 180 },
      "is_emergency": true
    }
  ],
  "top_class": "ambulance",
  "top_confidence": 0.94,
  "emergency_detected": true,
  "model_source": "base_model",
  "processing_time_ms": 42,
  "image_width": 640,
  "image_height": 480
}
```

## Data Pipeline Details

### 1. Data Collection
The backend pipeline can collect images from Wikimedia Commons using a data collection script. It stores metadata such as:
- source URL,
- license,
- collection timestamp,
- hash for deduplication.

### 2. Frame Extraction
The extraction phase prepares image frames and organizes them for YOLO training. It also supports stub output if the full AI dependencies are not available.

### 3. Training
The model training script prepares a YOLO-based detector and writes outputs such as:
- model weights,
- training metrics,
- logs and evaluation results.

### 4. Inference
Inference routes run detection on uploaded images or streams and return structured outputs for the frontend.

## Setup Instructions

### Prerequisites
- Node.js and npm
- Python 3.10+
- Git
- A browser for frontend testing

### Frontend Setup
```bash
cd project
npm install
npm run dev -- --host 0.0.0.0
```

Then open:
- http://localhost:5173

### Backend Setup
```bash
cd project/backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open:
- http://localhost:8000/docs
- http://localhost:8000/health

## Testing

The backend includes unit and integration tests for:
- collector logic,
- frame extraction logic,
- dataset generation,
- API validation.

Run tests with:
```bash
cd project/backend
.\venv\Scripts\python.exe -m pytest -v
```

## Important Notes

### Network Access
The project has been configured to work across local network access and browser environments beyond just localhost.

### GitHub / Repo Notes
The repository is intended to be used as a public or private project repo for AI-based emergency monitoring demo work. Generated environment folders like virtual environments and node_modules should remain ignored in Git.

### Model Behavior
If a trained model is unavailable, the backend falls back to:
- a base YOLO model,
- or a mock detection mode for demos and UI testing.

## Future Enhancements

Possible future improvements include:
- connecting real CCTV or camera streams,
- integrating with a real database,
- adding real geolocation services,
- using live traffic APIs,
- adding user authentication,
- deploying to cloud hosting,
- improving model accuracy with real emergency vehicle datasets.

## Project Impact

IntelliCross is meant to demonstrate how AI technologies can support smarter emergency response systems. It highlights practical use cases in:
- urban mobility,
- smart city infrastructure,
- emergency dispatch optimization,
- vehicle prioritization logic,
- and real-time situational awareness.

## License

This project is intended for educational and demonstration use. Please check the repository and licensing context before using it for commercial deployment.

## Conclusion

IntelliCross is a complete concept prototype for an AI-driven emergency vehicle detection and signal coordination system. It combines a live dashboard, backend inference services, and a training-ready AI pipeline to show how emergency detection can be operationalized in a smart city environment.

The project demonstrates both the visual interface and the technical backend logic needed to support an intelligent emergency response platform.
