/**
 * IntelliCross - Main Application Component
 * =========================================
 * Metropolitan-Scale Intelligent Traffic Orchestration Dashboard
 * 
 * Layout:
 * - Header (typographic hierarchy: IntelliCross largest)
 * - Top Row: VideoPanel (left) + ActionDashboard (right)
 * - Middle Row: CorridorTracker (full width)
 * - Bottom Row: MapPanel (full width)
 * 
 * Responsive breakpoints: 
 * - Mobile: stacked single column
 * - Tablet: 2-column grid for top row
 * - Desktop: balanced 2-column with full-width middle/bottom
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/Header';
import VideoPanel from './components/VideoPanel';
import ActionDashboard from './components/ActionDashboard';
import MapPanel from './components/MapPanel';
import CorridorTracker from './components/CorridorTracker';

// Dynamic API and WebSocket URLs for local development and cloud production
const API_BASE_URL = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/+$/, '')
  : (typeof window !== 'undefined' && window.location.hostname && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
      ? `${window.location.protocol}//${window.location.hostname}:8000`
      : 'http://localhost:8000');

const WS_BASE_URL = import.meta.env.VITE_WS_URL
  ? import.meta.env.VITE_WS_URL.replace(/\/+$/, '')
  : API_BASE_URL.replace(/^http(s?):/, 'ws$1:');

const App = () => {
  // WebSocket connection state
  const [ws, setWs] = useState(null);
  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  
  // Data state
  const [corridorData, setCorridorData] = useState({});
  const [evState, setEvState] = useState({});
  const [greenWave, setGreenWave] = useState({});
  const [nodeStates, setNodeStates] = useState({});
  const [routing, setRouting] = useState({});
  const [visionMode, setVisionMode] = useState('mock');
  const [visionHealthy, setVisionHealthy] = useState(true);
  const [fps, setFps] = useState(0);
  const [detections, setDetections] = useState([]);
  const [heatScore, setHeatScore] = useState(0);
  
  // UI state
  const [panelVisibility, setPanelVisibility] = useState({
    video: true,
    action: true,
    corridor: true,
    map: true
  });
  
  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    const wsUrl = `${WS_BASE_URL}/ws/traffic`;
    const websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      console.log('🔌 WebSocket connected');
      setConnected(true);
      setConnectionError(null);
      reconnectAttempts.current = 0;
    };
    
    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Update all state from comprehensive payload
        if (data.corridor) setCorridorData(data.corridor);
        if (data.ev_state) setEvState(data.ev_state);
        if (data.green_wave) setGreenWave(data.green_wave);
        if (data.nodes) setNodeStates(data.nodes);
        if (data.routing) setRouting(data.routing);
        if (data.vision_mode) setVisionMode(data.vision_mode);
        if (data.vision_healthy !== undefined) setVisionHealthy(data.vision_healthy);
        
        // Extract additional data
        if (data.routing?.lane_densities) {
          // Compute heat score from average density
          const avgDensity = data.routing.lane_densities.reduce((a, b) => a + b, 0) / 3;
          setHeatScore(avgDensity / 100);
        }
        
        // Detections for video panel (prefer actual live detections from vision engine)
        if (data.detections && data.detections.length > 0) {
          setDetections(data.detections);
        } else if (data.nodes) {
          const allDetections = [];
          Object.values(data.nodes).forEach(node => {
            if (node.vehicle_composition) {
              Object.entries(node.vehicle_composition).forEach(([cls, count]) => {
                for (let i = 0; i < Math.min(count, 3); i++) {
                  allDetections.push({ class_name: cls, confidence: 0.8 });
                }
              });
            }
          });
          setDetections(allDetections.slice(0, 20));
        }
        
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };
    
    websocket.onclose = () => {
      console.log('🔌 WebSocket disconnected');
      setConnected(false);
      
      // Exponential backoff reconnect
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current += 1;
      
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log(`🔄 Reconnecting... (attempt ${reconnectAttempts.current})`);
        connectWebSocket();
      }, delay);
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionError('Connection error - retrying...');
    };
    
    setWs(websocket);
  }, []);
  
  // Initialize connection
  useEffect(() => {
    connectWebSocket();
    
    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [connectWebSocket]);
  
  // Emergency lane for video panel
  const emergencyLane = routing.emergency_lane ?? (evState.active ? evState.lane : null);
  
  // Fetch simulation video URL and hospitals
  const [videoUrl, setVideoUrl] = useState(null);
  const [hospitals, setHospitals] = useState([]);
  
  useEffect(() => {
    // Fetch simulation video info
    fetch(`${API_BASE_URL}/simulation/video`)
      .then(r => r.json())
      .then(data => {
        if (data.status === 'available' && data.url) {
          const fullVideoUrl = data.url.startsWith('http') ? data.url : `${API_BASE_URL}${data.url}`;
          setVideoUrl(fullVideoUrl);
        }
      })
      .catch(err => console.warn('Video fetch failed:', err));
    
    // Fetch hospitals
    fetch(`${API_BASE_URL}/hospitals`)
      .then(r => r.json())
      .then(data => {
        if (data.hospitals) setHospitals(data.hospitals);
      })
      .catch(err => console.warn('Hospitals fetch failed:', err));
  }, []);
  
  // Compute average FPS for display
  const avgFps = videoUrl ? 20 : (visionMode === 'live' ? fps : 30);
  
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans antialiased">
      {/* Background ambient glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-sky-500/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-amber-500/3 rounded-full blur-3xl" />
      </div>
      
      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6 sm:space-y-8">
        {/* Header */}
        <Header />
        
        {/* Connection Status Bar */}
        <AnimatePresence mode="wait">
          {!connected && (
            <motion.div
              key="disconnected"
              className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-full text-sm text-red-400 font-medium backdrop-blur-sm"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                WebSocket Disconnected - Reconnecting...
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Top Row: Video Panel + Action Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" role="region" aria-label="Real-time Analytics">
          {/* Video Panel */}
          <AnimatePresence mode="wait">
            {panelVisibility.video && (
              <motion.div
                key="video"
                className="min-h-0"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
              >
<VideoPanel
                  visionMode={visionMode}
                  detections={detections}
                  densities={routing.lane_densities || [0, 0, 0]}
                  emergencyLane={emergencyLane}
                  fps={avgFps}
                  videoUrl={videoUrl}
                />
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Action Dashboard */}
          <AnimatePresence mode="wait">
            {panelVisibility.action && (
              <motion.div
                key="action"
                className="min-h-0"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4, delay: 0.05 }}
              >
                <ActionDashboard
                  routing={routing}
                  evState={evState}
                  greenWave={greenWave}
                  nodeStates={nodeStates}
                  corridorData={corridorData}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        {/* Middle Row: Corridor Tracker */}
        <AnimatePresence mode="wait">
          {panelVisibility.corridor && (
            <motion.div
              key="corridor"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4, delay: 0.1 }}
            >
              <CorridorTracker
                corridorData={corridorData}
                evState={evState}
                greenWave={greenWave}
                nodeStates={nodeStates}
              />
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Bottom Row: Map Panel */}
        <AnimatePresence mode="wait">
          {panelVisibility.map && (
            <motion.div
              key="map"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4, delay: 0.15 }}
            >
<MapPanel
                nodeStates={nodeStates}
                evState={evState}
                greenWave={greenWave}
                corridorData={corridorData}
                heatScore={heatScore}
                hospitals={hospitals}
              />
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Footer Status Bar */}
        <motion.footer
          className="pt-4 border-t border-slate-800/50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 text-sm">
            <div className="flex flex-wrap items-center gap-4">
              <span className="text-slate-500">IntelliCross v4.0</span>
              <span className="px-2 py-0.5 bg-slate-800/60 border border-slate-700/50 rounded font-mono text-slate-400">
                Metropolitan-Scale Orchestration
              </span>
              <span className={`px-2 py-0.5 rounded font-mono text-xs ${
                visionMode === 'live' 
                  ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                  : 'bg-slate-700/50 text-slate-400 border border-slate-600/50'
              }`}>
                {visionMode.toUpperCase()} MODE
              </span>
              {evState.active && (
                <span className="px-2 py-0.5 bg-red-500/20 text-red-400 border border-red-500/30 rounded font-mono text-xs animate-pulse">
                  EV ACTIVE
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-4 text-slate-500">
              <span className="font-mono">{new Date().toLocaleTimeString()}</span>
              <span className="flex items-center gap-1">
                <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                {connected ? 'LIVE' : 'OFFLINE'}
              </span>
            </div>
          </div>
        </motion.footer>
      </main>
      
      {/* Panel Visibility Controls (Debug) */}
      <div className="fixed bottom-4 left-4 z-40 flex gap-2" role="region" aria-label="Panel Controls">
        {[
          { id: 'video', label: 'Video' },
          { id: 'action', label: 'Action' },
          { id: 'corridor', label: 'Corridor' },
          { id: 'map', label: 'Map' }
        ].map(panel => (
          <button
            key={panel.id}
            onClick={() => setPanelVisibility(p => ({ ...p, [panel.id]: !p[panel.id] }))}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
              panelVisibility[panel.id]
                ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                : 'bg-slate-800/60 text-slate-500 border border-slate-700/50'
            }`}
            aria-pressed={panelVisibility[panel.id]}
          >
            {panel.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default App;