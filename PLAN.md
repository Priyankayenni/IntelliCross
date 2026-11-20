# IntelliCross Enhancement Plan — Emergency Vehicle Focus

## Problem Analysis
Current system:
- ✓ Has mock mode generating Indian traffic patterns
- ✓ Has green wave preemption for emergency vehicles
- ✓ Has WebSocket telemetry → Dashboard visualization
- ✓ Has corridor management with 3 nodes (Connaught Place)
- ✗ EV detection is weak (heuristic-based, not simulation-backed)
- ✗ No route planning to hospital/destination
- ✗ No real-time traffic impact on route optimization
- ✗ No simulation videos for testing

## What We Need to Build

### 1. Simulation Test Harness
Create realistic emergency vehicle scenarios with video clips:
- Ambulance approaching intersection (from multiple angles)
- Traffic congestion dissolving for EV
- Green wave propagation visualization

### 2. Enhanced EV-Centric Pipeline
The entire system must prioritize emergency vehicles:
- Route planning from EV location → Hospital (with hospital POI)
- Real-time traffic impact on ETA calculation
- Dynamic rerouting around congestion
- Corridor clearance optimization

### 3. Hardware-Ready Signal Control
The backend must output clear GPIO-ready commands:
- Per-lane signal state (RED/YELLOW/GREEN)
- Preemption hold duration
- Fallback to normal cycle after EV passes

### 4. Dashboard for Emergency Response
Add:
- Hospital locator on map
- EV route to hospital with waypoints
- Live traffic impact overlay
- ETA with confidence interval
- Signal preemption timeline
