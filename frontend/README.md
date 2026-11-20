# IntelliCross dashboard

React + Vite command console for city operators. Connects to the
backend's `/ws/telemetry` WebSocket and renders live intersection
state, traffic density per approach, and the preemption event log.

## Quick start

```bash
npm install
npm run dev
```

Runs at http://localhost:5173 and expects the backend at
`ws://localhost:8000/ws/telemetry` by default. Override with:

```bash
# .env.local
VITE_WS_URL=ws://your-backend-host:8000/ws/telemetry
```

## What's in here

- `src/hooks/useTelemetry.js` — WebSocket connection with auto-reconnect/backoff
- `src/components/IntersectionView.jsx` — live SVG signal-head visualization per approach
- `src/components/EmergencyBanner.jsx` — alert strip when an emergency vehicle is inbound
- `src/components/DensityPanel.jsx` — per-approach queued-vehicle bar chart
- `src/components/EventLog.jsx` — running log of issued preemption commands
- `src/components/StatusStrip.jsx` — top bar: phase, mode, FPS, connection state

## Build

```bash
npm run build
```

Outputs static files to `dist/` — deploy behind any static host/CDN, pointed at your backend's WebSocket URL.
