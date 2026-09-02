export type DetectionClass =
  | 'ambulance' | 'fire_truck' | 'police' | 'disaster'
  | 'car' | 'bus' | 'truck' | 'motorcycle' | 'auto_rickshaw' | 'pedestrian' | 'animal';

export type BoundingBox = { x: number; y: number; width: number; height: number };

export type Detection = {
  class_name: DetectionClass;
  confidence: number;
  bbox: BoundingBox;
  is_emergency: boolean;
};

export type DetectionResult = {
  detections: Detection[];
  top_class: DetectionClass | null;
  top_confidence: number;
  emergency_detected: boolean;
  model_source: 'web_trained_v1' | 'base_model';
  processing_time_ms: number;
};

const EMERGENCY_CLASSES: DetectionClass[] = ['ambulance', 'fire_truck', 'police', 'disaster'];

const SAMPLE_DETECTIONS: Omit<Detection, 'bbox'>[] = [
  { class_name: 'ambulance', confidence: 0.94, is_emergency: true },
  { class_name: 'car', confidence: 0.71, is_emergency: false },
  { class_name: 'motorcycle', confidence: 0.58, is_emergency: false },
  { class_name: 'pedestrian', confidence: 0.82, is_emergency: false },
  { class_name: 'fire_truck', confidence: 0.88, is_emergency: true },
  { class_name: 'truck', confidence: 0.64, is_emergency: false },
  { class_name: 'police', confidence: 0.79, is_emergency: true },
  { class_name: 'bus', confidence: 0.67, is_emergency: false },
  { class_name: 'auto_rickshaw', confidence: 0.55, is_emergency: false },
];

const CLASS_COLORS: Record<DetectionClass, string> = {
  ambulance: '#DC2626',
  fire_truck: '#EA580C',
  police: '#0284C7',
  disaster: '#7C3AED',
  car: '#6B7280',
  bus: '#6B7280',
  truck: '#6B7280',
  motorcycle: '#6B7280',
  auto_rickshaw: '#6B7280',
  pedestrian: '#6B7280',
  animal: '#6B7280',
};

export function getClassColor(className: DetectionClass): string {
  return CLASS_COLORS[className] ?? '#6B7280';
}

export function isEmergencyClass(className: DetectionClass): boolean {
  return EMERGENCY_CLASSES.includes(className);
}

function seededRandom(seed: number): () => number {
  let value = seed;
  return () => {
    value = (value * 9301 + 49297) % 233280;
    return value / 233280;
  };
}

function generateBbox(rand: () => number): BoundingBox {
  const width = 0.12 + rand() * 0.22;
  const height = 0.15 + rand() * 0.25;
  const x = rand() * (1 - width);
  const y = rand() * (1 - height);
  return { x, y, width, height };
}

export function runMockDetection(seed: number = Date.now() % 10000): DetectionResult {
  const rand = seededRandom(seed);
  const count = 2 + Math.floor(rand() * 4);
  const shuffled = [...SAMPLE_DETECTIONS].sort(() => rand() - 0.5);
  const selected = shuffled.slice(0, count);

  const detections: Detection[] = selected.map((det) => ({
    ...det,
    confidence: Math.max(0.4, det.confidence + (rand() - 0.5) * 0.1),
    bbox: generateBbox(rand),
  }));

  detections.sort((a, b) => b.confidence - a.confidence);

  const emergency = detections.find((d) => d.is_emergency);
  const top = detections[0];

  return {
    detections,
    top_class: top?.class_name ?? null,
    top_confidence: top?.confidence ?? 0,
    emergency_detected: !!emergency,
    model_source: 'web_trained_v1',
    processing_time_ms: 40 + Math.floor(rand() * 80),
  };
}
