/**
 * IntelliCross - VideoPanel Component
 * ===================================
 * Live traffic analytics visualization with real simulation video playback,
 * vision mode indicator, lane density overlay, and emergency detection.
 */

import React, { useMemo, useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

const VideoPanel = ({ 
  visionMode = 'mock', 
  detections = [], 
  densities = [0, 0, 0],
  emergencyLane = null,
  fps = 0,
  videoUrl = null
}) => {
  const videoRef = useRef(null);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [videoError, setVideoError] = useState(false);

  // Vehicle class color mapping
  const classColors = useMemo(() => ({
    car: 'bg-blue-500',
    bus: 'bg-orange-500',
    truck: 'bg-red-600',
    motorcycle: 'bg-yellow-400',
    autorickshaw: 'bg-amber-500',
    person: 'bg-purple-500',
    animal: 'bg-brown-500',
    ambulance: 'bg-red-500',
    firetruck: 'bg-red-700',
    police: 'bg-blue-700',
    default: 'bg-slate-500'
  }), []);
  
  const getColor = (className) => classColors[className?.toLowerCase()] || classColors.default;
  
  // Count detections by class
  const classCounts = useMemo(() => {
    const counts = {};
    detections.forEach(d => {
      const c = d.class_name || 'unknown';
      counts[c] = (counts[c] || 0) + 1;
    });
    return counts;
  }, [detections]);
  
  const totalDetections = Object.values(classCounts).reduce((a, b) => a + b, 0);

  // Handle video events with retry logic
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !videoUrl) return;

    const onLoaded = () => {
      setVideoLoaded(true);
      setVideoError(false);
    };
    const onError = () => {
      setVideoError(true);
      setVideoLoaded(false);
    };
    const onPlay = () => {};

    video.addEventListener('loadeddata', onLoaded);
    video.addEventListener('error', onError);
    video.addEventListener('play', onPlay);

    // Reset state on url change
    setVideoLoaded(false);
    setVideoError(false);

    return () => {
      video.removeEventListener('loadeddata', onLoaded);
      video.removeEventListener('error', onError);
      video.removeEventListener('play', onPlay);
    };
  }, [videoUrl]);
  
  return (
    <motion.div
      className="backdrop-blur-xl bg-slate-950/60 border border-slate-800/50 rounded-3xl overflow-hidden shadow-2xl"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      {/* Header */}
      <div className="p-4 sm:p-6 border-b border-slate-800/50">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-xl sm:text-2xl font-semibold text-white">Live Traffic Analytics</h2>
            <p className="text-sm text-slate-400 mt-1">
              {videoUrl ? '🎬 EV Simulation Video Feed' : 
               visionMode === 'live' ? 'YOLOv8 Real-Time Inference' : 'Simulated Indian Traffic Patterns'}
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-3">
            {/* Vision Mode Badge */}
            <span className={`px-3 py-1 rounded-full text-xs font-medium font-mono ${
              visionMode === 'live' 
                ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' 
                : visionMode === 'error'
                ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                : 'bg-slate-700/50 text-slate-400 border border-slate-600/50'
            }`}>
              {videoUrl ? 'SIMULATION' : visionMode.toUpperCase()}
            </span>
            
            {/* FPS Counter */}
            {fps > 0 && (
              <span className="px-3 py-1 bg-slate-800/60 border border-slate-700/50 rounded-full text-xs font-mono text-slate-300">
                {fps.toFixed(1)} FPS
              </span>
            )}
            
            {/* Detection Count */}
            <span className="px-3 py-1 bg-slate-800/60 border border-slate-700/50 rounded-full text-xs font-mono text-slate-300">
              {totalDetections} Objects
            </span>
          </div>
        </div>
      </div>
      
      {/* Video / Simulated Area */}
      <div className="relative h-72 sm:h-80 bg-slate-950">
        {/* Simulation Video */}
        {videoUrl && !videoError && (
          <video
            ref={videoRef}
            className="absolute inset-0 w-full h-full object-cover"
            src={videoUrl}
            autoPlay
            loop
            muted
            playsInline
          />
        )}

        {/* Overlay gradient at bottom for density bars */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent pointer-events-none z-10" />
        
        {/* Status overlays */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-20">
          <div className="text-center p-8">
            {!videoUrl && (
              <>
                <div className="w-64 h-36 sm:w-80 sm:h-48 mx-auto mb-4 bg-slate-900 rounded-xl border border-slate-800/50 relative overflow-hidden">
                  {/* Lane dividers */}
                  <div className="absolute inset-0 flex">
                    {[0, 1].map(i => (
                      <div key={i} className="flex-1 border-r border-slate-700/30" />
                    ))}
                    <div className="flex-1" />
                  </div>
                  
                  {/* Simulated vehicle boxes */}
                  <div className="absolute inset-0 p-2">
                    {detections.slice(0, 15).map((det, idx) => {
                      const bbox = det.bbox || [idx * 40, idx * 30, idx * 40 + 30, idx * 30 + 20];
                      const x = (bbox[0] % 320) / 640 * 100;
                      const y = (bbox[1] % 240) / 480 * 100;
                      const w = ((bbox[2] - bbox[0]) % 100) / 640 * 100;
                      const h = ((bbox[3] - bbox[1]) % 80) / 480 * 100;
                      
                      return (
                        <motion.div
                          key={idx}
                          className="absolute"
                          style={{ left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%` }}
                          initial={{ opacity: 0, scale: 0.5 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: idx * 0.05 }}
                        >
                          <div 
                            className={`w-full h-full rounded border-2 ${getColor(det.class_name)} opacity-80`}
                            style={{ boxShadow: '0 0 8px currentColor' }}
                          />
                          <div className={`absolute -top-5 left-0 text-[8px] font-medium px-1 rounded ${getColor(det.class_name)} text-white whitespace-nowrap`}>
                            {det.class_name} {Math.round((det.confidence || 0) * 100)}%
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                  
                  {/* Emergency indicator overlay */}
                  {emergencyLane !== null && (
                    <motion.div
                      className="absolute top-2 right-2 px-3 py-1 bg-red-500/90 text-white text-xs font-bold rounded-full flex items-center gap-1"
                      animate={{ opacity: [0.7, 1, 0.7] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    >
                      <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                      EV LANE {emergencyLane + 1}
                    </motion.div>
                  )}
                  
                  {/* Play button overlay */}
                  <div className="absolute inset-0 flex items-center justify-center bg-slate-950/40">
                    <div className="w-12 h-12 rounded-full bg-sky-500/80 flex items-center justify-center">
                      <svg className="w-6 h-6 text-white ml-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                      </svg>
                    </div>
                  </div>
                </div>
                
                {/* Mode indicator */}
                <p className="text-xs text-slate-500 font-mono">
                  🎮 Simulation Mode (Video available via /uploads)
                </p>
              </>
            )}
            
            {videoUrl && !videoLoaded && !videoError && (
              <div className="text-slate-400 text-sm">
                <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                Loading simulation video...
              </div>
            )}
            
            {videoError && (
              <div className="text-red-400 text-sm">
                ⚠️ Video load error. Using simulation mode.
              </div>
            )}
          </div>
        </div>
        
        {/* Density overlay bars at bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-slate-950/90 to-transparent z-30">
          <div className="flex items-end gap-2 h-16">
            {densities.map((density, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                <div className="w-full h-full bg-slate-800 rounded-t relative overflow-hidden" style={{ maxHeight: '100px' }}>
                  <motion.div
                    className="absolute bottom-0 left-0 right-0 rounded-t"
                    style={{ 
                      backgroundColor: density >= 80 ? '#ef4444' : density >= 60 ? '#f59e0b' : density >= 40 ? '#eab308' : '#10b981',
                      height: `${Math.min(100, density)}%`
                    }}
                    initial={{ height: 0 }}
                    animate={{ height: `${Math.min(100, density)}%` }}
                    transition={{ duration: 0.8, delay: idx * 0.1 }}
                  />
                  {emergencyLane === idx && (
                    <motion.div className="absolute top-1 left-1/2 -translate-x-1/2 text-[10px] font-bold text-white">
                      🚨
                    </motion.div>
                  )}
                </div>
                <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wide">
                  {['LEFT', 'CENTER', 'RIGHT'][idx]}
                </span>
                <span className="text-[10px] font-mono text-white">
                  {density.toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Video playback indicator */}
        {videoUrl && videoLoaded && (
          <div className="absolute top-2 left-2 z-30 flex items-center gap-2">
            <motion.span 
              className="w-2 h-2 rounded-full bg-emerald-500"
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
            <span className="text-xs text-emerald-400 font-mono bg-slate-950/70 px-2 py-0.5 rounded">
              ▶ PLAYING
            </span>
          </div>
        )}
      </div>
      
      {/* Detection Legend */}
      <div className="p-4 border-t border-slate-800/50">
        <p className="text-xs text-slate-500 mb-2">DETECTED CLASSES (Indian Road Taxonomy)</p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(classCounts).map(([cls, count]) => (
            <motion.span
              key={cls}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${getColor(cls)} text-white`}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-current opacity-50" />
              {cls} ×{count}
            </motion.span>
          ))}
          {Object.keys(classCounts).length === 0 && (
            <span className="text-xs text-slate-500">No detections in current frame</span>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default VideoPanel;
