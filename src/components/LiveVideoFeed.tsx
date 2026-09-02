import { useEffect, useRef, useState } from 'react';
import { Camera, Maximize2, Radio, Volume2, VolumeX, Video, VideoOff } from 'lucide-react';

type Props = {
  cameraId: string;
  cameraName: string;
  vehicleId: string;
};

export function LiveVideoFeed({ cameraId, cameraName, vehicleId }: Props) {
  const [isPlaying, setIsPlaying] = useState(true);
  const [muted, setMuted] = useState(true);
  const [time, setTime] = useState(new Date());
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  // Simulated scan line animation position
  const [scanY, setScanY] = useState(0);
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => setScanY((prev) => (prev + 2) % 100), 50);
    return () => clearInterval(interval);
  }, [isPlaying]);

  return (
    <div className="video-feed-panel">
      <div className="video-feed-header">
        <div className="video-feed-title">
          <Video size={16} />
          <h3>Live Roadway Feed</h3>
        </div>
        <div className="video-feed-controls">
          <button onClick={() => setMuted(!muted)} title={muted ? 'Unmute' : 'Mute'}>
            {muted ? <VolumeX size={15} /> : <Volume2 size={15} />}
          </button>
          <button onClick={() => setIsPlaying(!isPlaying)} title={isPlaying ? 'Pause' : 'Play'}>
            {isPlaying ? <VideoOff size={15} /> : <Video size={15} />}
          </button>
          <button title="Fullscreen"><Maximize2 size={15} /></button>
        </div>
      </div>
      <div className="video-feed-screen" ref={containerRef}>
        <div className={`video-feed-placeholder ${isPlaying ? 'playing' : 'paused'}`}>
          <div className="video-feed-grid" />
          {isPlaying && <div className="video-feed-scan" style={{ top: `${scanY}%` }} />}
          <div className="video-feed-overlay">
            <div className="video-feed-info">
              <span className="video-feed-cam"><Camera size={11} /> {cameraId}</span>
              <span className="video-feed-name">{cameraName}</span>
            </div>
            <div className="video-feed-rec">
              <span className="rec-dot" /> REC
            </div>
            <div className="video-feed-tracking">
              <div className="tracking-box">
                <span className="tracking-label">{vehicleId} · 98%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="video-feed-footer">
        <div className="video-feed-timestamp">{time.toLocaleTimeString('en-US', { hour12: false })}</div>
        <div className="video-feed-status">
          <Radio size={11} /> <span>STREAMING · 1080p · 30fps</span>
        </div>
      </div>
    </div>
  );
}
