import { useEffect, useRef, useState } from 'react';
import { AlertTriangle, Camera, CheckCircle2, Clock3, Crosshair, Image as ImageIcon, Loader2, ScanLine, Sparkles, Upload, X, Zap } from 'lucide-react';
import { runMockDetection, getClassColor, type DetectionResult, type DetectionClass } from '@/detection';

type Props = { onClose: () => void; onDetect: (result: DetectionResult) => void };
type Phase = 'upload' | 'analyzing' | 'results';

const CLASS_LABELS: Record<DetectionClass, string> = {
  ambulance: 'Ambulance', fire_truck: 'Fire Truck', police: 'Police Vehicle', disaster: 'Disaster Response',
  car: 'Car', bus: 'Bus', truck: 'Truck', motorcycle: 'Motorcycle', auto_rickshaw: 'Auto Rickshaw',
  pedestrian: 'Pedestrian', animal: 'Animal',
};

export function DetectionPanel({ onClose, onDetect }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [phase, setPhase] = useState<Phase>('upload');
  const [imageUrl, setImageUrl] = useState<string>('');
  const [fileName, setFileName] = useState<string>('');
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => () => { if (imageUrl) URL.revokeObjectURL(imageUrl); }, [imageUrl]);

  const handleFile = (file: File) => {
    setFileName(file.name);
    const url = URL.createObjectURL(file);
    setImageUrl(url);
    setPhase('upload');
    setResult(null);
  };

  const runDetection = () => {
    setPhase('analyzing');
    window.setTimeout(() => {
      const det = runMockDetection();
      setResult(det);
      setPhase('results');
      onDetect(det);
    }, 1400);
  };

  const reset = () => { setPhase('upload'); setResult(null); setImageUrl(''); setFileName(''); };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="detection-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}><X size={18} /></button>
        <div className="eyebrow"><ScanLine size={14} /> AI VISION LAYER</div>
        <h2>Emergency vehicle detection</h2>
        <p>Upload a camera frame or roadside image to identify active response units using the YOLOv8 detection model.</p>

        {phase === 'upload' && (
          <div
            className={`upload-zone ${dragOver ? 'drag-over' : ''} ${imageUrl ? 'has-file' : ''}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
          >
            {imageUrl ? (
              <div className="upload-preview">
                <img src={imageUrl} alt="Upload preview" />
                <div className="upload-preview-info"><CheckCircle2 size={22} /><strong>{fileName}</strong><span>Ready for analysis</span></div>
              </div>
            ) : (
              <>
                <div className="upload-icon"><Upload size={22} /></div>
                <strong>Drop an image here or click to browse</strong>
                <span>PNG, JPG up to 50MB</span>
              </>
            )}
            <input ref={inputRef} type="file" accept="image/*" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
          </div>
        )}

        {phase === 'analyzing' && (
          <div className="analyzing-zone">
            {imageUrl && <div className="analyzing-image"><img src={imageUrl} alt="Analyzing" /><div className="scan-overlay" /></div>}
            <div className="analyzing-info">
              <Loader2 size={26} className="spin" />
              <strong>Running YOLOv8 inference...</strong>
              <span>Detecting emergency vehicles and traffic objects</span>
            </div>
          </div>
        )}

        {phase === 'results' && result && imageUrl && (
          <div className="detection-results">
            <div className="annotated-image-wrap">
              <img src={imageUrl} alt="Annotated" />
              {result.detections.map((det, i) => (
                <div
                  key={i}
                  className="bbox-overlay"
                  style={{
                    left: `${det.bbox.x * 100}%`,
                    top: `${det.bbox.y * 100}%`,
                    width: `${det.bbox.width * 100}%`,
                    height: `${det.bbox.height * 100}%`,
                    borderColor: getClassColor(det.class_name),
                  }}
                >
                  <span className="bbox-label" style={{ background: getClassColor(det.class_name) }}>
                    {CLASS_LABELS[det.class_name]} {Math.round(det.confidence * 100)}%
                  </span>
                </div>
              ))}
              <div className="annotated-badge"><Camera size={12} /> ANNOTATED</div>
            </div>

            <div className="result-summary">
              {result.emergency_detected ? (
                <div className="result-alert emergency">
                  <AlertTriangle size={20} />
                  <div><strong>Emergency vehicle detected</strong><span>Top match: {CLASS_LABELS[result.top_class!]} ({Math.round(result.top_confidence * 100)}% confidence)</span></div>
                </div>
              ) : (
                <div className="result-alert neutral">
                  <CheckCircle2 size={20} />
                  <div><strong>No emergency vehicles detected</strong><span>{result.detections.length} traffic objects found</span></div>
                </div>
              )}
              <div className="result-meta">
                <span><Clock3 size={13} /> {result.processing_time_ms}ms</span>
                <span><Zap size={13} /> {result.model_source}</span>
                <span><Crosshair size={13} /> {result.detections.length} objects</span>
              </div>
            </div>

            <div className="detection-list">
              <label>DETECTED OBJECTS</label>
              {result.detections.map((det, i) => (
                <div key={i} className={`detection-row ${det.is_emergency ? 'emergency' : ''}`}>
                  <span className="detection-color" style={{ background: getClassColor(det.class_name) }} />
                  <span className="detection-name">{CLASS_LABELS[det.class_name]}</span>
                  {det.is_emergency && <span className="emergency-tag">EMERGENCY</span>}
                  <span className="detection-confidence">{Math.round(det.confidence * 100)}%</span>
                  <div className="confidence-bar"><div style={{ width: `${det.confidence * 100}%`, background: getClassColor(det.class_name) }} /></div>
                </div>
              ))}
            </div>

            <div className="modal-actions">
              <button className="secondary-button" onClick={reset}><ImageIcon size={15} /> Try another image</button>
              <button className="primary-button" onClick={onClose}><Sparkles size={16} /> Add to live tracking</button>
            </div>
          </div>
        )}

        {phase === 'upload' && (
          <>
            <div className="detection-note"><Camera size={15} /> YOLOv8 inference is ready. Demo mode uses simulated detections when the model server is offline.</div>
            <div className="modal-actions">
              <button className="secondary-button" onClick={onClose}>Cancel</button>
              <button className="primary-button" disabled={!imageUrl} onClick={runDetection}><ScanLine size={16} /> Run detection</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
