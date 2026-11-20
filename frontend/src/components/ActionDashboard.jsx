/**
 * IntelliCross - ActionDashboard Component
 * ========================================
 * Real-time action plan with routing recommendations, signal states,
 * emergency status, and corridor-level intelligence.
 */

import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const ActionDashboard = ({ 
  routing = {}, 
  evState = {}, 
  greenWave = {},
  nodeStates = {},
  corridorData = {}
}) => {
  const direction = routing.recommended_direction || 'Straight';
  const speed = routing.recommended_speed_kmph || 40;
  const densities = routing.lane_densities || [0, 0, 0];
  const emergencyDetected = routing.emergency_detected || false;
  const emergencyLane = routing.emergency_lane;
  
  // Direction icon/color mapping
  const directionConfig = useMemo(() => ({
    Left: { icon: '←', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', label: 'VEER LEFT' },
    Right: { icon: '→', color: 'text-sky-400', bg: 'bg-sky-500/10', border: 'border-sky-500/30', label: 'VEER RIGHT' },
    Straight: { icon: '↑', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', label: 'PROCEED STRAIGHT' }
  }), []);
  
  const dirConfig = directionConfig[direction] || directionConfig.Straight;
  
  // Active green wave node
  const activeWaveNode = useMemo(() => {
    if (!greenWave?.node_schedules) return null;
    const now = Date.now() / 1000;
    const scheduleTime = greenWave.computed_at || now;
    
    for (const [nodeId, sched] of Object.entries(greenWave.node_schedules)) {
      const absoluteTrigger = scheduleTime + sched.trigger_at_sec;
      const absoluteEnd = absoluteTrigger + sched.hold_sec;
      if (now >= absoluteTrigger && now <= absoluteEnd) {
        return { nodeId, ...sched, remaining: absoluteEnd - now };
      }
    }
    return null;
  }, [greenWave]);
  
  // Next trigger
  const nextTrigger = useMemo(() => {
    if (!greenWave?.node_schedules) return null;
    const now = Date.now() / 1000;
    const scheduleTime = greenWave.computed_at || now;
    
    let soonest = null;
    let soonestTime = Infinity;
    
    for (const [nodeId, sched] of Object.entries(greenWave.node_schedules)) {
      const absoluteTrigger = scheduleTime + sched.trigger_at_sec;
      if (absoluteTrigger > now && absoluteTrigger < soonestTime) {
        soonestTime = absoluteTrigger;
        soonest = { nodeId, ...sched, triggerAt: absoluteTrigger };
      }
    }
    return soonest;
  }, [greenWave]);
  
  // Signal light component
  const SignalLight = ({ state, active, emergency }) => (
    <motion.div
      className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full transition-all duration-500 ${
        state === 'GREEN' 
          ? 'bg-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.9)]' 
          : state === 'YELLOW' 
          ? 'bg-yellow-400 shadow-[0_0_20px_rgba(250,204,21,0.9)]' 
          : 'bg-red-500 shadow-[0_0_20px_rgba(239,68,68,0.9)]'
      } ${active ? 'ring-2 ring-white/50 scale-110' : ''} ${emergency ? 'ring-2 ring-sky-400' : ''}`}
      animate={state === 'GREEN' && active ? { boxShadow: ['0 0 20px rgba(16,185,129,0.9)', '0 0 30px rgba(16,185,129,1)', '0 0 20px rgba(16,185,129,0.9)'] } : {}}
      transition={{ duration: 1.5, repeat: Infinity }}
    />
  );
  
  return (
    <motion.div
      className="backdrop-blur-xl bg-slate-950/60 border border-slate-800/50 rounded-3xl p-4 sm:p-6 shadow-2xl space-y-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.15 }}
    >
      {/* Emergency Status Banner */}
      <AnimatePresence mode="wait">
        {emergencyDetected && (
          <motion.div
            key="emergency"
            className="relative p-4 bg-red-500/10 border border-red-500/30 rounded-2xl overflow-hidden"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-red-500/5 via-transparent to-red-500/5"
              animate={{ x: ['-100%', '100%'] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
            />
            <div className="relative flex items-center gap-3">
              <motion.div
                className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center"
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </motion.div>
              <div className="flex-1">
                <p className="text-sm font-bold text-red-400 tracking-wide">EMERGENCY VEHICLE PRIORITY ACTIVE</p>
                <p className="text-xs text-slate-400 mt-0.5">
                  Ambulance detected in Lane {emergencyLane !== null ? emergencyLane + 1 : '?'} • 
                  Green wave pre-emption engaged • 
                  Corridor clearance in progress
                </p>
              </div>
              <motion.div
                className="px-3 py-1 bg-red-500 text-white text-xs font-bold rounded-full"
                animate={{ opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                EV OVERRIDE
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Normal Status */}
      {!emergencyDetected && (
        <motion.div
          className="p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-emerald-400">NORMAL OPERATION</p>
              <p className="text-xs text-slate-500">No emergency vehicles detected • Density-based routing active</p>
            </div>
          </div>
        </motion.div>
      )}
      
      {/* Primary Routing Directive */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">ROUTING DIRECTIVE</h3>
          <span className={`px-3 py-1 text-xs font-mono font-medium rounded-full border ${dirConfig.bg} ${dirConfig.color} ${dirConfig.border}`}>
            {dirConfig.label}
          </span>
        </div>
        
        <motion.div
          className={`p-5 rounded-2xl border ${dirConfig.bg} ${dirConfig.border} relative overflow-hidden`}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent" />
          <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
            <div className="flex items-center gap-4">
              <motion.span
                className={`text-5xl sm:text-7xl font-black ${dirConfig.color}`}
                animate={{ scale: [1, 1.02, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                {dirConfig.icon}
              </motion.span>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider">RECOMMENDED DIRECTION</p>
                <p className={`text-3xl sm:text-4xl font-black ${dirConfig.color}`}>{direction.toUpperCase()}</p>
              </div>
            </div>
            
            <div className="flex flex-col items-end sm:items-center gap-1">
              <p className="text-xs text-slate-500 uppercase tracking-wider">ADVISORY SPEED</p>
              <motion.p
                className="text-4xl sm:text-5xl font-black font-mono text-white"
                animate={{ textShadow: ['0 0 0', '0 0 20px rgba(255,255,255,0.3)', '0 0 0'] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                {speed}
              </motion.p>
              <p className="text-sm font-medium text-slate-400">km/h</p>
            </div>
          </div>
        </motion.div>
      </div>
      
      {/* Corridor Intelligence */}
      {Object.keys(corridorData).length > 0 && (
        <div className="space-y-4 pt-4 border-t border-slate-800/50">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19l-6-6 6-6m12 12l-6-6 6-6m-12 12h18" />
            </svg>
            CORRIDOR INTELLIGENCE
          </h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Green Wave Status */}
            <motion.div
              className={`p-4 rounded-2xl border transition-all duration-500 ${
                activeWaveNode 
                  ? 'bg-emerald-500/5 border-emerald-500/30' 
                  : 'bg-slate-900/40 border-slate-700/50'
              }`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">GREEN WAVE</span>
                <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
                  activeWaveNode 
                    ? 'bg-emerald-500/20 text-emerald-400' 
                    : 'bg-slate-700/50 text-slate-500'
                }`}>
                  {activeWaveNode ? 'ACTIVE' : 'STANDBY'}
                </span>
              </div>
              
              {activeWaveNode ? (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Active Node</span>
                    <span className="font-mono text-white">{activeWaveNode.nodeId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Hold Remaining</span>
                    <span className="font-mono text-emerald-400">{activeWaveNode.remaining.toFixed(0)}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Wave Speed</span>
                    <span className="font-mono text-sky-400">{greenWave.wave_speed_kmph?.toFixed(0) || 0} km/h</span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-500">Awaiting EV activation for predictive wave</p>
              )}
            </motion.div>
            
            {/* Next Trigger */}
            <motion.div
              className={`p-4 rounded-2xl border transition-all duration-500 ${
                nextTrigger 
                  ? 'bg-sky-500/5 border-sky-500/30' 
                  : 'bg-slate-900/40 border-slate-700/50'
              }`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">NEXT TRIGGER</span>
                <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-sky-500/20 text-sky-400">
                  SCHEDULED
                </span>
              </div>
              
              {nextTrigger ? (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Target Node</span>
                    <span className="font-mono text-white">{nextTrigger.nodeId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Triggers In</span>
                    <motion.span
                      className="font-mono text-sky-400"
                      animate={{ textShadow: ['0 0 0', '0 0 10px rgba(56,189,248,0.8)', '0 0 0'] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      {(nextTrigger.triggerAt - Date.now()/1000).toFixed(0)}s
                    </motion.span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Hold Duration</span>
                    <span className="font-mono text-white">{nextTrigger.hold_sec.toFixed(0)}s</span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-500">No pending triggers</p>
              )}
            </motion.div>
            
            {/* EV Tracking */}
            <motion.div
              className="p-4 rounded-2xl border bg-slate-900/40 border-slate-700/50 sm:col-span-2"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">EV TRACKING</span>
                <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
                  evState.active 
                    ? 'bg-red-500/20 text-red-400' 
                    : 'bg-slate-700/50 text-slate-500'
                }`}>
                  {evState.active ? 'TRACKING' : 'IDLE'}
                </span>
              </div>
              
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <div>
                  <p className="text-slate-500">Current Node</p>
                  <p className="font-mono text-white">{evState.node_id || '—'}</p>
                </div>
                <div>
                  <p className="text-slate-500">Lane</p>
                  <p className="font-mono text-white">Lane {evState.lane !== undefined ? evState.lane + 1 : '—'}</p>
                </div>
                <div>
                  <p className="text-slate-500">Speed</p>
                  <p className="font-mono text-sky-400">{evState.speed_kmph?.toFixed(1) || '—'} km/h</p>
                </div>
                <div>
                  <p className="text-slate-500">Distance to Node</p>
                  <p className="font-mono text-amber-400">{evState.distance_to_node_m?.toFixed(0) || '—'} m</p>
                </div>
              </div>
            </motion.div>
            
            {/* Corridor Stats */}
            <motion.div
              className="p-4 rounded-2xl border bg-slate-900/40 border-slate-700/50 sm:col-span-2"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
            >
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">CORRIDOR METRICS</span>
              <div className="grid grid-cols-3 gap-4 mt-3 text-sm">
                <div className="text-center p-3 bg-slate-800/50 rounded-xl">
                  <p className="text-2xl font-black text-sky-400 font-mono">
                    {corridorData.length_m ? (corridorData.length_m/1000).toFixed(1) : '—'}
                  </p>
                  <p className="text-xs text-slate-500">Length (km)</p>
                </div>
                <div className="text-center p-3 bg-slate-800/50 rounded-xl">
                  <p className="text-2xl font-black text-emerald-400 font-mono">
                    {greenWave.total_corridor_clearance_sec?.toFixed(0) || '—'}
                  </p>
                  <p className="text-xs text-slate-500">Clearance (s)</p>
                </div>
                <div className="text-center p-3 bg-slate-800/50 rounded-xl">
                  <p className="text-2xl font-black text-amber-400 font-mono">
                    {((greenWave.confidence || 0) * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-slate-500">Confidence</p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      )}
      
      {/* Intersection Signal States */}
      <div className="pt-4 border-t border-slate-800/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          INTERSECTION SIGNALS
        </h3>
        
        <div className="grid grid-cols-3 gap-3">
          {['LEFT', 'CENTER', 'RIGHT'].map((laneLabel, laneIdx) => {
            const density = densities[laneIdx] || 0;
            const isEMLane = emergencyLane === laneIdx;
            
            // Find active signal for this lane across nodes
            const activeSignals = Object.values(nodeStates).map(n => n.signal_states?.[laneIdx]).filter(Boolean);
            const hasGreen = activeSignals.includes('GREEN');
            const hasYellow = activeSignals.includes('YELLOW');
            const signalState = hasGreen ? 'GREEN' : hasYellow ? 'YELLOW' : 'RED';
            
            return (
              <motion.div
                key={laneIdx}
                className={`p-4 rounded-2xl border transition-all duration-500 relative overflow-hidden ${
                  isEMLane 
                    ? 'bg-red-500/5 border-red-500/30' 
                    : signalState === 'GREEN' 
                    ? 'bg-emerald-500/5 border-emerald-500/30' 
                    : 'bg-slate-900/40 border-slate-700/50'
                }`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + laneIdx * 0.05 }}
              >
                {isEMLane && (
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-red-500/5 via-transparent to-red-500/5"
                    animate={{ x: ['-100%', '100%'] }}
                    transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
                  />
                )}
                
                <div className="relative flex flex-col items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <SignalLight state={signalState} active={signalState === 'GREEN'} emergency={isEMLane} />
                    <span className={`text-xs font-bold uppercase tracking-wider ${signalState === 'GREEN' ? 'text-emerald-400' : signalState === 'YELLOW' ? 'text-yellow-400' : 'text-red-400'}`}>
                      {signalState}
                    </span>
                  </div>
                  
                  <p className="text-xs text-slate-500 uppercase tracking-wide">{laneLabel} LANE</p>
                  
                  {/* Density indicator */}
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ 
                        backgroundColor: density >= 80 ? '#ef4444' : density >= 60 ? '#f59e0b' : density >= 40 ? '#eab308' : '#10b981',
                        width: `${Math.min(100, density)}%`
                      }}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(100, density)}%` }}
                      transition={{ duration: 0.8, delay: 0.1 }}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between w-full text-xs">
                    <span className="text-slate-500">Density</span>
                    <span className="font-mono text-white">{density.toFixed(0)}%</span>
                  </div>
                  
                  {isEMLane && (
                    <motion.span
                      className="px-2 py-0.5 bg-red-500/20 text-red-400 text-[10px] font-bold rounded-full"
                      animate={{ opacity: [0.7, 1, 0.7] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    >
                      EV LANE
                    </motion.span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
};

export default ActionDashboard;