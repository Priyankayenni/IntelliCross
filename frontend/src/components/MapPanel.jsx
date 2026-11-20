/**
 * IntelliCross - MapPanel Component
 * =================================
 * Interactive corridor map with Leaflet showing intersection nodes,
 * EV position, green wave propagation, and real-time traffic heatmap.
 */

import React, { useEffect, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { motion } from 'framer-motion';

// Custom marker icons using L.divIcon
const createNodeIcon = (nodeId, isEVNode, isActiveWave) => {
  const baseSize = isEVNode ? 28 : 24;
  const pulseSize = isActiveWave ? 40 : 0;
  
  return L.divIcon({
    html: `
      <div style="
        width: ${baseSize}px; 
        height: ${baseSize}px; 
        border-radius: 50%; 
        background: ${isEVNode ? '#0ea5e9' : isActiveWave ? '#10b981' : '#64748b'};
        border: 3px solid ${isEVNode ? '#38bdf8' : isActiveWave ? '#34d399' : '#475569'};
        box-shadow: 0 0 16px ${isEVNode ? 'rgba(56,189,248,0.8)' : isActiveWave ? 'rgba(16,185,129,0.8)' : 'rgba(100,116,139,0.5)'};
        display: flex; 
        align-items: center; 
        justify-content: center;
        font-size: 10px;
        font-weight: bold;
        color: #0f172a;
        font-family: monospace;
        position: relative;
        z-index: 10;
      ">
        ${isEVNode ? '🚨' : isActiveWave ? '✓' : ''}
      </div>
      ${pulseSize > 0 ? `
        <div style="
          position: absolute;
          top: 50%; left: 50%;
          transform: translate(-50%, -50%);
          width: ${pulseSize}px; height: ${pulseSize}px;
          border-radius: 50%;
          border: 2px solid ${isActiveWave ? '#10b981' : '#0ea5e9'};
          opacity: 0.4;
          animation: pulse 2s ease-out infinite;
        "></div>
      ` : ''}
      <style>
        @keyframes pulse {
          0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0.6; }
          100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
        }
      </style>
    `,
    className: '',
    iconSize: [baseSize, baseSize],
    iconAnchor: [baseSize / 2, baseSize / 2]
  });
};

const createEVIcon = () => L.divIcon({
  html: `
    <div style="
      width: 36px; height: 36px;
      border-radius: 50%;
      background: linear-gradient(135deg, #0ea5e9, #38bdf8);
      border: 3px solid #ffffff;
      box-shadow: 0 0 24px rgba(56,189,248,0.9);
      display: flex; align-items: center; justify-content: center;
      font-size: 16px;
      animation: evPulse 1.5s ease-in-out infinite;
    ">
      🚑
    </div>
    <style>
      @keyframes evPulse {
        0%, 100% { transform: scale(1); box-shadow: 0 0 24px rgba(56,189,248,0.9); }
        50% { transform: scale(1.1); box-shadow: 0 0 36px rgba(56,189,248,1); }
      }
    </style>
  `,
  className: '',
  iconSize: [36, 36],
  iconAnchor: [18, 18]
});

const createHospitalIcon = () => L.divIcon({
  html: `
    <div style="
      width: 28px; height: 28px;
      border-radius: 50%;
      background: linear-gradient(135deg, #ef4444, #dc2626);
      border: 2px solid #ffffff;
      box-shadow: 0 0 12px rgba(239,68,68,0.6);
      display: flex; align-items: center; justify-content: center;
      font-size: 14px;
    ">
      🏥
    </div>
  `,
  className: '',
  iconSize: [28, 28],
  iconAnchor: [14, 14]
});

const MapPanel = ({ 
  nodeStates = {}, 
  evState = {}, 
  greenWave = {},
  corridorData = {},
  heatScore = 0,
  hospitals = []
}) => {
  const mapRef = useRef(null);
  const nodes = useMemo(() => Object.values(nodeStates), [nodeStates]);
  
  // Compute map center from nodes
  const mapCenter = useMemo(() => {
    if (nodes.length === 0) return [28.6139, 77.2090]; // Default Delhi
    const avgLat = nodes.reduce((sum, n) => sum + (n.latitude || 0), 0) / nodes.length;
    const avgLon = nodes.reduce((sum, n) => sum + (n.longitude || 0), 0) / nodes.length;
    return [avgLat, avgLon];
  }, [nodes]);
  
  // Corridor polyline coordinates
  const corridorCoords = useMemo(() => 
    nodes
      .filter(n => n.latitude && n.longitude)
      .sort((a, b) => (a.distance_from_prev_m || 0) - (b.distance_from_prev_m || 0))
      .map(n => [n.latitude, n.longitude]),
  [nodes]);
  
  // EV position interpolation
  const evPosition = useMemo(() => {
    if (!evState.active || !evState.node_id || nodes.length < 2) return null;
    
    const currentNode = nodes.find(n => n.node_id === evState.node_id);
    if (!currentNode) return null;
    
    const nodeIndex = nodes.findIndex(n => n.node_id === evState.node_id);
    if (nodeIndex === -1 || nodeIndex === nodes.length - 1) {
      return [currentNode.latitude, currentNode.longitude];
    }
    
    const nextNode = nodes[nodeIndex + 1];
    const distToNext = currentNode.distance_from_prev_m || 0;
    const progress = 1 - (evState.distance_to_node_m || 0) / distToNext;
    
    // Linear interpolation
    const lat = currentNode.latitude + (nextNode.latitude - currentNode.latitude) * Math.max(0, Math.min(1, progress));
    const lon = currentNode.longitude + (nextNode.longitude - currentNode.longitude) * Math.max(0, Math.min(1, progress));
    
    return [lat, lon];
  }, [evState, nodes]);
  
  // Active green wave node
  const activeWaveNodeId = useMemo(() => {
    if (!greenWave?.node_schedules) return null;
    const now = Date.now() / 1000;
    const scheduleTime = greenWave.computed_at || now;
    
    for (const [nodeId, sched] of Object.entries(greenWave.node_schedules)) {
      const absoluteTrigger = scheduleTime + sched.trigger_at_sec;
      const absoluteEnd = absoluteTrigger + sched.hold_sec;
      if (now >= absoluteTrigger && now <= absoluteEnd) {
        return nodeId;
      }
    }
    return null;
  }, [greenWave]);
  
  // Heatmap color
  const heatColor = useMemo(() => {
    if (heatScore > 0.7) return '#ef4444';
    if (heatScore > 0.4) return '#f59e0b';
    return '#10b981';
  }, [heatScore]);
  
  return (
    <motion.div
      className="backdrop-blur-xl bg-slate-950/60 border border-slate-800/50 rounded-3xl overflow-hidden shadow-2xl"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      {/* Header */}
      <div className="p-4 sm:p-6 border-b border-slate-800/50">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-xl sm:text-2xl font-semibold text-white">Corridor Map</h2>
            <p className="text-sm text-slate-400 mt-1">
              {corridorData.name || 'Metropolitan Corridor'} • {nodes.length} Intersections
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-2">
            {/* Heatmap indicator */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/60 border border-slate-700/50 rounded-full">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: heatColor }} />
              <span className="text-xs font-mono text-slate-300">
                Congestion: {(heatScore * 100).toFixed(0)}%
              </span>
            </div>
            
            {/* Node count */}
            <span className="px-3 py-1.5 bg-slate-800/60 border border-slate-700/50 rounded-full text-xs font-mono text-slate-300">
              {nodes.length} Nodes
            </span>
          </div>
        </div>
      </div>
      
      {/* Map */}
      <div className="h-80 sm:h-96 relative">
        <MapContainer
          ref={mapRef}
          center={mapCenter}
          zoom={14}
          scrollWheelZoom={true}
          className="w-full h-full"
          style={{ zIndex: 1 }}
        >
          {/* Base Layer */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />
          
          {/* Heatmap overlay circle */}
          {nodes.length > 0 && heatScore > 0.2 && (
            <Circle
              center={mapCenter}
              radius={800}
              pathOptions={{
                stroke: false,
                fillColor: heatColor,
                fillOpacity: 0.15
              }}
            />
          )}
          
          {/* Corridor Polyline */}
          {corridorCoords.length >= 2 && (
            <Polyline
              positions={corridorCoords}
              pathOptions={{
                color: '#0ea5e9',
                weight: 3,
                opacity: 0.6,
                dashArray: '10, 10',
                lineCap: 'round',
                lineJoin: 'round'
              }}
            />
          )}
          
          {/* Green Wave propagation animation */}
          {greenWave?.node_schedules && corridorCoords.length >= 2 && (
            <motion.div
              className="absolute inset-0 pointer-events-none"
              style={{ zIndex: 2 }}
            >
              {Object.entries(greenWave.node_schedules).map(([nodeId, sched], idx) => {
                const node = nodes.find(n => n.node_id === nodeId);
                if (!node || !node.latitude) return null;
                
                const now = Date.now() / 1000;
                const scheduleTime = greenWave.computed_at || now;
                const absoluteTrigger = scheduleTime + sched.trigger_at_sec;
                const absoluteEnd = absoluteTrigger + sched.hold_sec;
                const isActive = now >= absoluteTrigger && now <= absoluteEnd;
                const isPending = now < absoluteTrigger;
                
                if (!isActive && !isPending) return null;
                
                return (
                  <Circle
                    key={nodeId}
                    center={[node.latitude, node.longitude]}
                    radius={isActive ? 120 : 80}
                    pathOptions={{
                      stroke: true,
                      color: isActive ? '#10b981' : '#0ea5e9',
                      weight: isActive ? 3 : 2,
                      opacity: isActive ? 0.8 : 0.4,
                      fill: false,
                      dashArray: isPending ? '5, 10' : undefined
                    }}
                  />
                );
              })}
            </motion.div>
          )}
          
          {/* Intersection Nodes */}
          {nodes.map((node) => {
            const isEVNode = evState.active && evState.node_id === node.node_id;
            const isActiveWave = activeWaveNodeId === node.node_id;
            const activeGreen = node.active_green_lane ?? 2;
            const densities = node.lane_densities || [0, 0, 0];
            const maxDensity = Math.max(...densities);
            
            return (
              <Marker
                key={node.node_id}
                position={[node.latitude, node.longitude]}
                icon={createNodeIcon(node.node_id, isEVNode, isActiveWave)}
                zIndexOffset={isEVNode ? 1000 : isActiveWave ? 500 : 0}
              >
                <Popup offset={[0, -16]}>
                  <div className="p-2 min-w-[200px] bg-slate-900 text-white rounded">
                    <div className="font-bold text-sky-400 mb-2">{node.name}</div>
                    <div className="text-xs text-slate-400 mb-2 font-mono">{node.node_id}</div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Active Signal</span>
                        <span className={`font-mono ${activeGreen === 0 ? 'text-red-400' : activeGreen === 1 ? 'text-emerald-400' : 'text-amber-400'}`}>
                          Lane {activeGreen + 1} GREEN
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Max Density</span>
                        <span className="font-mono text-white">{maxDensity.toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Lane Densities</span>
                        <span className="font-mono text-slate-300">
                          {densities.map((d, i) => `L${i+1}:${d.toFixed(0)}%`).join(' | ')}
                        </span>
                      </div>
                      {isActiveWave && (
                        <motion.div className="mt-2 p-1 bg-emerald-500/20 border border-emerald-500/30 rounded text-emerald-400 text-center text-xs font-medium"
                          animate={{ opacity: [0.7, 1, 0.7] }}
                          transition={{ duration: 1, repeat: Infinity }}
                        >
                          ✓ GREEN WAVE ACTIVE
                        </motion.div>
                      )}
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
          
{/* Hospital Markers */}
          {hospitals.map((hospital) => (
            <Marker
              key={hospital.id}
              position={[hospital.latitude, hospital.longitude]}
              icon={createHospitalIcon()}
              zIndexOffset={500}
            >
              <Popup offset={[0, -16]}>
                <div className="p-2 min-w-[200px] bg-slate-900 text-white rounded">
                  <div className="flex items-center gap-2 mb-2">
                    <span>🏥</span>
                    <span className="font-bold text-red-400">{hospital.name}</span>
                  </div>
                  <div className="text-xs text-slate-400 mb-2">{hospital.address}</div>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Capacity</span>
                      <span className="font-mono text-white">{hospital.capacity}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Emergency</span>
                      <span className={hospital.emergency_available ? 'text-emerald-400' : 'text-red-400'}>
                        {hospital.emergency_available ? 'Available' : 'Unavailable'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">From Corridor</span>
                      <span className="font-mono text-sky-400">{hospital.distance_from_corridor_km} km</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* EV Marker */}
          {evPosition && evState.active && (
            <Marker
              position={evPosition}
              icon={createEVIcon()}
              zIndexOffset={2000}
            >
              <Popup offset={[0, -16]}>
                <div className="p-2 min-w-[180px] bg-slate-900 text-white rounded">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-red-400">🚨</span>
                    <span className="font-bold text-red-400">EMERGENCY VEHICLE</span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Speed</span>
                      <span className="font-mono text-sky-400">{evState.speed_kmph?.toFixed(1) || '—'} km/h</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Lane</span>
                      <span className="font-mono text-white">Lane {evState.lane !== undefined ? evState.lane + 1 : '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Target Node</span>
                      <span className="font-mono text-white">{evState.node_id || '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Distance</span>
                      <span className="font-mono text-amber-400">{evState.distance_to_node_m?.toFixed(0) || '—'} m</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          )}
        </MapContainer>
        
        {/* Map Legend Overlay */}
        <div className="absolute bottom-4 right-4 z-10">
          <motion.div
            className="backdrop-blur-md bg-slate-950/90 border border-slate-700/50 rounded-xl p-3 text-xs"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-sky-400" />
              <span className="font-medium text-white">Corridor Path</span>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full border-2 border-emerald-400" />
              <span className="font-medium text-white">Green Wave Active</span>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full border-2 border-sky-400 border-dashed" />
              <span className="font-medium text-white">Green Wave Pending</span>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: heatColor }} />
              <span className="font-medium text-white">Congestion Heatmap</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500 flex items-center justify-center text-[10px]">🚑</span>
              <span className="font-medium text-white">Emergency Vehicle</span>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
};

export default MapPanel;