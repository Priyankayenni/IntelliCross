/**
 * IntelliCross - CorridorTracker Component
 * ========================================
 * Premium glassmorphic vertical timeline visualizing EV progression
 * through the metropolitan corridor with predictive green wave scheduling.
 * 
 * Features:
 * - Pulsing EV marker physically moving down corridor timeline
 * - Real-time ETA countdowns per intersection
 * - Green wave trigger schedule visualization
 * - Signal state indicators with animated transitions
 * - Density bars with Indian traffic composition hints
 * - Fully responsive, dark-mode, glassmorphism design
 */

import React, { useEffect, useRef, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const CorridorTracker = ({ 
  corridorData, 
  evState, 
  greenWave, 
  nodeStates 
}) => {
  // Animation refs and state
  const [evProgress, setEvProgress] = useState(0); // 0-1 along corridor
  const [nodeETAs, setNodeETAs] = useState({});
  const [triggerStatus, setTriggerStatus] = useState({});
  const timelineRef = useRef(null);
  
  // Node order from corridor data
  const nodeOrder = useMemo(() => corridorData?.node_order || [], [corridorData]);
  
  // Compute EV progress from WebSocket data
  useEffect(() => {
    if (!evState?.active || !corridorData) return;
    
    let progress = 0;
    if (evState.position_ratio !== null && evState.position_ratio !== undefined) {
      progress = evState.position_ratio;
    } else if (evState.node_id && nodeOrder.length > 0) {
      // Calculate from node position and distance
      const nodeIndex = nodeOrder.indexOf(evState.node_id);
      if (nodeIndex >= 0) {
        const nodesBefore = nodeOrder.slice(0, nodeIndex);
        const distBefore = nodesBefore.reduce((sum, nid) => {
          const node = nodeStates?.[nid];
          return sum + (node?.distance_from_prev_m || 0);
        }, 0);
        
        const totalLength = corridorData.length_m || 1;
        const currentNode = nodeStates?.[evState.node_id];
        const distToNode = currentNode?.distance_from_prev_m || 0;
        const remainingInNode = distToNode - (evState.distance_to_node_m || 0);
        
        progress = Math.min(1, Math.max(0, (distBefore + remainingInNode) / totalLength));
      }
    }
    
    setEvProgress(progress);
  }, [evState, corridorData, nodeStates, nodeOrder]);
  
  // Compute ETAs and trigger status from green wave schedule
  useEffect(() => {
    if (!greenWave?.node_schedules || !nodeStates) return;
    
    const etas = {};
    const triggers = {};
    const now = Date.now() / 1000;
    const scheduleTime = greenWave.computed_at || now;
    
    Object.entries(greenWave.node_schedules).forEach(([nodeId, sched]) => {
      const triggerAt = sched.trigger_at_sec;
      const holdSec = sched.hold_sec;
      const absoluteTriggerTime = scheduleTime + triggerAt;
      const timeToTrigger = absoluteTriggerTime - now;
      
      etas[nodeId] = Math.max(0, timeToTrigger);
      triggers[nodeId] = {
        triggered: timeToTrigger <= 1.0, // Within 1 sec tolerance
        triggering: timeToTrigger > 0 && timeToTrigger <= 5.0, // About to trigger
        timeToTrigger: Math.max(0, timeToTrigger),
        holdDuration: holdSec
      };
    });
    
    setNodeETAs(etas);
    setTriggerStatus(triggers);
  }, [greenWave, nodeStates]);
  
  // Get node display data
  const getNodeDisplayData = (nodeId) => {
    const node = nodeStates?.[nodeId];
    const schedule = greenWave?.node_schedules?.[nodeId];
    const eta = nodeETAs[nodeId] || 0;
    const trigger = triggerStatus[nodeId] || {};
    const isCurrentEVNode = evState?.node_id === nodeId;
    const isEVLane = (lane) => evState?.lane === lane;
    
    return { node, schedule, eta, trigger, isCurrentEVNode, isEVLane };
  };
  
  // Format time display
  const formatTime = (seconds) => {
    if (seconds <= 0) return 'NOW';
    if (seconds < 60) return `${Math.ceil(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.ceil(seconds % 60);
    return `${mins}m ${secs}s`;
  };
  
  // Density bar color
  const getDensityColor = (density) => {
    if (density >= 80) return 'bg-red-500';
    if (density >= 60) return 'bg-amber-500';
    if (density >= 40) return 'bg-yellow-500';
    return 'bg-emerald-500';
  };
  
  // Signal state indicator
  const SignalIndicator = ({ state, lane, isEVLane, animated }) => {
    const colors = {
      RED: 'bg-red-500',
      YELLOW: 'bg-yellow-400',
      GREEN: 'bg-emerald-500',
      FLASHING_AMBER: 'bg-amber-400'
    };
    
    const glows = {
      RED: 'shadow-[0_0_12px_rgba(239,68,68,0.8)]',
      YELLOW: 'shadow-[0_0_12px_rgba(250,204,21,0.8)]',
      GREEN: 'shadow-[0_0_16px_rgba(16,185,129,0.9)]',
      FLASHING_AMBER: 'shadow-[0_0_12px_rgba(250,204,21,0.6)]'
    };
    
    return (
      <motion.div
        className={`w-3 h-3 rounded-full transition-all duration-500 ${colors[state] || 'bg-slate-600'} ${glows[state] || ''} ${isEVLane ? 'ring-2 ring-sky-400/50' : ''}`}
        animate={animated && state === 'GREEN' ? { scale: [1, 1.15, 1] } : {}}
        transition={{ duration: 1.5, repeat: Infinity }}
        title={`Lane ${lane + 1}: ${state}`}
      />
    );
  };
  
  // Lane density mini-bar
  const LaneDensityBar = ({ density, lane, isEVLane }) => (
    <div className="flex items-center gap-1.5" title={`Lane ${lane + 1}: ${density}%`}>
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          className={`${getDensityColor(density)} h-full rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, density)}%` }}
          transition={{ duration: 0.8, delay: lane * 0.1 }}
        />
      </div>
      {isEVLane && (
        <motion.span 
          className="text-xs font-bold text-sky-400" 
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          ◀ EV
        </motion.span>
      )}
    </div>
  );
  
  return (
    <motion.section
      className="backdrop-blur-xl bg-slate-950/60 border border-slate-800/50 rounded-3xl p-6 shadow-2xl"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800/50">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Corridor Tracker</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            {corridorData?.name || 'Metropolitan Corridor'} • {corridorData?.length_m ? `${(corridorData.length_m/1000).toFixed(1)} km` : ''}
          </p>
        </div>
        
        {/* EV Status Badge */}
        <motion.div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
            evState?.active 
              ? 'bg-red-500/20 text-red-400 border border-red-500/30' 
              : 'bg-slate-700/50 text-slate-400 border border-slate-600/50'
          }`}
          animate={evState?.active ? { boxShadow: ['0 0 0', '0 0 20px rgba(239,68,68,0.3)', '0 0 0'] } : {}}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          <span className={`w-2 h-2 rounded-full ${evState?.active ? 'bg-red-500' : 'bg-slate-500'}`} />
          {evState?.active ? 'EV ACTIVE' : 'STANDBY'}
        </motion.div>
      </div>
      
      {/* Corridor Timeline */}
      <div className="relative" ref={timelineRef}>
        {/* Vertical timeline track */}
        <div className="absolute left-10 top-0 bottom-0 w-1 bg-gradient-to-b from-slate-700 via-slate-600 to-slate-700 rounded-full" />
        
        {/* EV Progress Marker - moves along timeline */}
        <AnimatePresence mode="wait">
          <motion.div
            key={evProgress}
            className="absolute left-10 top-0 w-1 h-1 -translate-x-1/2 -translate-y-1/2 pointer-events-none"
            style={{ top: `${evProgress * 100}%` }}
            animate={{ 
              scale: [1, 1.3, 1],
              boxShadow: [
                '0 0 0 rgba(56,189,248,0)',
                '0 0 30px rgba(56,189,248,0.9)',
                '0 0 0 rgba(56,189,248,0)'
              ]
            }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          >
            <div className="w-full h-full bg-sky-400 rounded-full relative">
              {/* Pulse rings */}
              <motion.div
                className="absolute inset-0 bg-sky-400 rounded-full opacity-30"
                animate={{ scale: [1, 3], opacity: [0.4, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeOut' }}
              />
              <motion.div
                className="absolute inset-0 bg-sky-400 rounded-full opacity-20"
                animate={{ scale: [1, 2.5], opacity: [0.3, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeOut', delay: 1 }}
              />
            </div>
            
            {/* EV Label */}
            <motion.div
              className="absolute left-full ml-3 top-1/2 -translate-y-1/2 whitespace-nowrap text-xs font-medium text-sky-300 bg-slate-950/90 px-2 py-1 rounded border border-sky-400/30"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
            >
              EV • {evState?.speed_kmph ? `${evState.speed_kmph} km/h` : ''}
            </motion.div>
          </motion.div>
        </AnimatePresence>
        
        {/* Intersection Nodes */}
        <div className="space-y-8 pl-4">
          {nodeOrder.map((nodeId, index) => {
            const { node, schedule, eta, trigger, isCurrentEVNode, isEVLane } = getNodeDisplayData(nodeId);
            if (!node) return null;
            
            const isLast = index === nodeOrder.length - 1;
            const signalStates = node.signal_states || ['RED', 'RED', 'GREEN'];
            const densities = node.lane_densities || [0, 0, 0];
            const activeGreen = node.active_green_lane ?? 2;
            
            return (
              <motion.div
                key={nodeId}
                className="relative flex items-start gap-6 group"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1, duration: 0.4 }}
              >
                {/* Timeline connector & node marker */}
                <div className="relative flex-shrink-0 w-20 flex flex-col items-center">
                  {/* Node circle on timeline */}
                  <motion.div
                    className={`relative z-10 w-5 h-5 rounded-full border-3 flex items-center justify-center ${
                      trigger.triggered 
                        ? 'bg-emerald-500 border-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.8)]'
                        : trigger.triggering
                        ? 'bg-sky-400 border-sky-300 shadow-[0_0_20px_rgba(56,189,248,0.8)] animate-pulse'
                        : isCurrentEVNode
                        ? 'bg-sky-400 border-sky-300 shadow-[0_0_16px_rgba(56,189,248,0.6)]'
                        : 'bg-slate-700 border-slate-500'
                    }`}
                    animate={trigger.triggering ? { scale: [1, 1.2, 1] } : {}}
                    transition={{ duration: 0.8, repeat: Infinity }}
                  >
                    {trigger.triggered && (
                      <motion.span className="text-[10px] font-black text-slate-950">✓</motion.span>
                    )}
                  </motion.div>
                  
                  {/* Distance label */}
                  <div className="mt-1 text-[10px] text-slate-500 text-center w-20">
                    {index === 0 ? 'START' : `${Math.round(node.distance_from_prev_m)}m`}
                  </div>
                  
                  {/* Connector line to next node */}
                  {!isLast && (
                    <div className="flex-1 w-1 bg-slate-700 mt-1 relative" />
                  )}
                </div>
                
                {/* Node Content Card */}
                <motion.div
                  className={`flex-1 min-w-0 backdrop-blur-md bg-slate-900/40 border rounded-2xl p-4 transition-all duration-500 ${
                    trigger.triggered 
                      ? 'border-emerald-500/50 bg-emerald-500/5 shadow-[0_0_30px_rgba(16,185,129,0.15)]'
                      : trigger.triggering
                      ? 'border-sky-400/50 bg-sky-500/5 shadow-[0_0_30px_rgba(56,189,248,0.15)]'
                      : isCurrentEVNode
                      ? 'border-sky-400/40 bg-sky-500/5'
                      : 'border-slate-700/50'
                  }`}
                  animate={{
                    boxShadow: trigger.triggered 
                      ? '0 0 40px rgba(16,185,129,0.3)' 
                      : trigger.triggering 
                      ? '0 0 40px rgba(56,189,248,0.3)' 
                      : 'none'
                  }}
                >
                  {/* Node Header */}
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-white truncate">{node.name}</h3>
                        <span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-400 rounded font-mono">
                          {nodeId}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5 truncate">
                        Lat: {node.latitude?.toFixed(4)}, Lon: {node.longitude?.toFixed(4)}
                      </p>
                    </div>
                    
                    {/* ETA / Countdown */}
                    <div className="flex flex-col items-end gap-1">
                      {trigger.triggered && (
                        <motion.span 
                          className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/30"
                          animate={{ opacity: [0.7, 1, 0.7] }}
                          transition={{ duration: 1, repeat: Infinity }}
                        >
                          GREEN WAVE ACTIVE
                        </motion.span>
                      )}
                      {trigger.triggering && !trigger.triggered && (
                        <motion.span 
                          className="text-xs font-bold text-sky-400 bg-sky-500/10 px-2 py-1 rounded border border-sky-400/30"
                          animate={{ opacity: [0.5, 1, 0.5] }}
                          transition={{ duration: 0.8, repeat: Infinity }}
                        >
                          TRIGGERING IN {formatTime(trigger.timeToTrigger)}
                        </motion.span>
                      )}
                      {eta > 0 && !trigger.triggered && !trigger.triggering && (
                        <div className="text-right">
                          <p className="text-xs text-slate-500">ETA TO GREEN</p>
                          <p className="font-mono text-lg font-bold text-sky-300">{formatTime(eta)}</p>
                        </div>
                      )}
                      {schedule && eta <= 0 && !trigger.triggered && (
                        <p className="text-xs text-slate-500">Scheduled: {formatTime(schedule.trigger_at_sec)}s</p>
                      )}
                    </div>
                  </div>
                  
                  {/* Signal States */}
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-xs text-slate-500 font-medium w-20">SIGNALS</span>
                    <div className="flex items-center gap-2">
                      {signalStates.map((state, laneIdx) => (
                        <SignalIndicator 
                          key={laneIdx}
                          state={state}
                          lane={laneIdx}
                          isEVLane={isEVLane(laneIdx)}
                          animated={trigger.triggered && isEVLane(laneIdx)}
                        />
                      ))}
                    </div>
                    <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                      activeGreen === 0 ? 'bg-red-500/20 text-red-400' :
                      activeGreen === 1 ? 'bg-emerald-500/20 text-emerald-400' :
                      'bg-amber-500/20 text-amber-400'
                    }`}>
                      Lane {activeGreen + 1} GREEN
                    </span>
                  </div>
                  
                  {/* Lane Densities */}
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs text-slate-500 font-medium w-20">DENSITY</span>
                      <span className="text-xs text-slate-400">Per logical lane (Indian road model)</span>
                    </div>
                    <div className="flex items-center gap-2 ml-20">
                      {densities.map((density, laneIdx) => (
                        <LaneDensityBar 
                          key={laneIdx}
                          density={density}
                          lane={laneIdx}
                          isEVLane={isEVLane(laneIdx)}
                        />
                      ))}
                    </div>
                  </div>
                  
                  {/* Green Wave Schedule Details */}
                  {schedule && (
                    <motion.div
                      className="mt-3 pt-3 border-t border-slate-700/50"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                    >
                      <div className="flex items-center gap-2 text-xs mb-2">
                        <span className="px-2 py-0.5 bg-sky-500/10 text-sky-400 rounded font-mono">
                          GREEN WAVE SCHEDULE
                        </span>
                        <span className="text-slate-500">
                          Trigger at {formatTime(schedule.trigger_at_sec)} • Hold {schedule.hold_sec.toFixed(0)}s
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-sky-400" />
                          Wave Speed: {greenWave?.wave_speed_kmph?.toFixed(0) || 0} km/h
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-emerald-400" />
                          Confidence: {(greenWave?.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              </motion.div>
            );
          })}
        </div>
      </div>
      
      {/* Corridor Summary Footer */}
      <motion.div
        className="mt-6 pt-4 border-t border-slate-800/50 grid grid-cols-3 gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        <div className="text-center p-3 bg-slate-900/40 rounded-xl border border-slate-700/50">
          <p className="text-2xl font-black text-sky-400 font-mono">
            {greenWave?.total_corridor_clearance_sec?.toFixed(0) || '--'}s
          </p>
          <p className="text-xs text-slate-500 mt-0.5">Total Clearance</p>
        </div>
        <div className="text-center p-3 bg-slate-900/40 rounded-xl border border-slate-700/50">
          <p className="text-2xl font-black text-emerald-400 font-mono">
            {greenWave?.wave_speed_kmph?.toFixed(0) || '--'}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">Wave Speed (km/h)</p>
        </div>
        <div className="text-center p-3 bg-slate-900/40 rounded-xl border border-slate-700/50">
          <p className="text-2xl font-black text-amber-400 font-mono">
            {((greenWave?.confidence || 0) * 100).toFixed(0)}%
          </p>
          <p className="text-xs text-slate-500 mt-0.5">Prediction Confidence</p>
        </div>
      </motion.div>
    </motion.section>
  );
};

export default CorridorTracker;