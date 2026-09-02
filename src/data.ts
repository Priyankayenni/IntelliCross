export type VehicleType = 'ambulance' | 'fire_truck' | 'police' | 'disaster';
export type SignalState = 'green' | 'yellow' | 'red';
export type Role = 'operator' | 'driver';
export type ContactChannel = 'call' | 'email' | 'sms' | 'whatsapp';
export type AlertSeverity = 'critical' | 'warning' | 'info';

export type Vehicle = {
  id: string;
  type: VehicleType;
  location: string;
  destination: string;
  destinationHospitalId: string;
  distance: number;
  eta: number;
  speed: number;
  heading: number;
  confidence: number;
  position: [number, number];
  corridorId: string | null;
  distanceToSignal: number;
  lockedRoute: boolean;
  driverName: string;
  driverPhone: string;
  severity: number;
};

export type Hospital = {
  id: string;
  name: string;
  city: string;
  distance: number;
  eta: number;
  beds: number;
  totalBeds: number;
  responseTime: number;
  phone: string;
  email: string;
  position: [number, number];
  specializations: string[];
};

export type Signal = {
  id: string;
  state: SignalState;
  countdown: number;
  position: [number, number];
  preemption: boolean;
  preemptionTime: number | null;
};

export type Corridor = {
  id: string;
  name: string;
  cameraId: string;
  signalId: string;
  center: [number, number];
  radius: number;
  vehicleId: string | null;
};

export type AlertItem = {
  id: string;
  vehicleId: string;
  vehicleType: VehicleType;
  severity: AlertSeverity;
  message: string;
  location: string;
  heading: number;
  confidence: number;
  nearestHospital: string;
  eta: number;
  timestamp: number;
  acknowledged: boolean;
};

export type TimelineEvent = {
  id: string;
  vehicleId: string;
  type: 'detection' | 'route_assigned' | 'signal_preemption' | 'hospital_alerted' | 'contact_made' | 'arrival' | 'route_locked';
  label: string;
  timestamp: number;
};

export type ContactLog = {
  id: string;
  timestamp: number;
  channel: ContactChannel;
  target: string;
  targetName: string;
  operatorId: string;
  vehicleId: string | null;
  status: 'sent' | 'failed';
};

export type OperatorNote = {
  vehicleId: string;
  text: string;
  tags: string[];
  timestamp: number;
};

export const vehicles: Vehicle[] = [
  { id: 'AMB-2047', type: 'ambulance', location: 'Ring Road, Sector 5', destination: 'AIIMS New Delhi', destinationHospitalId: 'aiims', distance: 3.2, eta: 4, speed: 45, heading: 185, confidence: 0.98, position: [28.6329, 77.2195], corridorId: 'COR-01', distanceToSignal: 0.4, lockedRoute: false, driverName: 'Rajesh Kumar', driverPhone: '+91 98100 12345', severity: 5 },
  { id: 'FTR-0912', type: 'fire_truck', location: 'Moti Nagar Junction', destination: 'Safdarjung Hospital', destinationHospitalId: 'safdarjung', distance: 5.8, eta: 9, speed: 38, heading: 210, confidence: 0.72, lockedRoute: true, driverName: 'Sunil Sharma', driverPhone: '+91 98200 67890', position: [28.6575, 77.1412], corridorId: 'COR-02', distanceToSignal: 0.7, severity: 4 },
  { id: 'POL-7710', type: 'police', location: 'Connaught Place', destination: 'Lok Nayak Hospital', destinationHospitalId: 'aiims', distance: 7.1, eta: 12, speed: 32, heading: 175, confidence: 0.45, lockedRoute: false, driverName: 'Anil Verma', driverPhone: '+91 98300 11111', position: [28.6315, 77.2167], corridorId: null, distanceToSignal: 1.2, severity: 2 },
];

export const hospitals: Hospital[] = [
  { id: 'aiims', name: 'AIIMS New Delhi', city: 'Ansari Nagar', distance: 2.1, eta: 4, beds: 45, totalBeds: 800, responseTime: 3, phone: '+91 11 2658 8500', email: 'emergency@aiims.edu', position: [28.5672, 77.2100], specializations: ['Trauma Center', 'Burn Unit', 'Pediatric Care'] },
  { id: 'safdarjung', name: 'Safdarjung Hospital', city: 'Ring Road', distance: 3.8, eta: 7, beds: 82, totalBeds: 650, responseTime: 5, phone: '+91 11 2616 3072', email: 'emergency@safdarjung.nic.in', position: [28.5687, 77.2067], specializations: ['Trauma Center', 'Pediatric Care'] },
  { id: 'apollo', name: 'Indraprastha Apollo', city: 'Sarita Vihar', distance: 9.4, eta: 16, beds: 120, totalBeds: 710, responseTime: 4, phone: '+91 11 2692 5858', email: 'emergency@apollohospitals.com', position: [28.5407, 77.2837], specializations: ['Trauma Center', 'Burn Unit'] },
  { id: 'max', name: 'Max Super Speciality', city: 'Saket', distance: 11.2, eta: 19, beds: 67, totalBeds: 500, responseTime: 6, phone: '+91 11 2651 5050', email: 'emergency@maxhealthcare.in', position: [28.5273, 77.2137], specializations: ['Burn Unit', 'Pediatric Care'] },
];

export const signals: Signal[] = [
  { id: 'SIG-01', state: 'green', countdown: 42, position: [28.6329, 77.2195], preemption: true, preemptionTime: 0 },
  { id: 'SIG-02', state: 'green', countdown: 31, position: [28.6208, 77.2148], preemption: true, preemptionTime: 35 },
  { id: 'SIG-03', state: 'yellow', countdown: 18, position: [28.6062, 77.2121], preemption: false, preemptionTime: null },
  { id: 'SIG-04', state: 'red', countdown: 27, position: [28.5901, 77.2105], preemption: false, preemptionTime: null },
  { id: 'SIG-05', state: 'green', countdown: 56, position: [28.5754, 77.2092], preemption: false, preemptionTime: null },
];

export const corridors: Corridor[] = [
  { id: 'COR-01', name: 'Ring Road Sector 5 Camera', cameraId: 'CAM-014', signalId: 'SIG-01', center: [28.6329, 77.2195], radius: 1000, vehicleId: 'AMB-2047' },
  { id: 'COR-02', name: 'Moti Nagar Junction Camera', cameraId: 'CAM-022', signalId: 'SIG-03', center: [28.6575, 77.1412], radius: 1000, vehicleId: 'FTR-0912' },
  { id: 'COR-03', name: 'CP Outer Circle Camera', cameraId: 'CAM-007', signalId: 'SIG-02', center: [28.6315, 77.2167], radius: 1000, vehicleId: null },
];

export const timelineEvents: TimelineEvent[] = [
  { id: 'ev1', vehicleId: 'AMB-2047', type: 'detection', label: 'Ambulance detected at Ring Road Sector 5', timestamp: Date.now() - 240000 },
  { id: 'ev2', vehicleId: 'AMB-2047', type: 'route_assigned', label: 'Route computed to AIIMS New Delhi (3.2 km, ETA 4 min)', timestamp: Date.now() - 210000 },
  { id: 'ev3', vehicleId: 'AMB-2047', type: 'signal_preemption', label: 'Green wave initiated — SIG-01, SIG-02 set to green', timestamp: Date.now() - 180000 },
  { id: 'ev4', vehicleId: 'AMB-2047', type: 'hospital_alerted', label: 'AIIMS emergency department alerted', timestamp: Date.now() - 120000 },
  { id: 'ev5', vehicleId: 'AMB-2047', type: 'contact_made', label: 'Call placed to AIIMS emergency desk', timestamp: Date.now() - 60000 },
];

export const initialAlerts: AlertItem[] = [
  { id: 'al1', vehicleId: 'AMB-2047', vehicleType: 'ambulance', severity: 'critical', message: 'Ambulance entering monitored corridor', location: 'Ring Road, Sector 5', heading: 185, confidence: 0.98, nearestHospital: 'AIIMS New Delhi', eta: 4, timestamp: Date.now() - 240000, acknowledged: false },
  { id: 'al2', vehicleId: 'FTR-0912', vehicleType: 'fire_truck', severity: 'warning', message: 'Fire truck detected — low confidence', location: 'Moti Nagar Junction', heading: 210, confidence: 0.72, nearestHospital: 'Safdarjung Hospital', eta: 9, timestamp: Date.now() - 180000, acknowledged: false },
  { id: 'al3', vehicleId: 'POL-7710', vehicleType: 'police', severity: 'info', message: 'Police vehicle detected — verify manually', location: 'Connaught Place', heading: 175, confidence: 0.45, nearestHospital: 'AIIMS New Delhi', eta: 12, timestamp: Date.now() - 90000, acknowledged: true },
];

export const CORRIDOR_RADIUS_M = 1000;
export const CONFIDENCE_THRESHOLD_LONG = 0.35;
export const CONFIDENCE_THRESHOLD_SHORT = 0.5;

export const route: [number, number][] = [
  [28.6329, 77.2195], [28.6258, 77.2182], [28.6208, 77.2148], [28.6142, 77.2140], [28.6062, 77.2121], [28.5989, 77.2113], [28.5901, 77.2105], [28.5802, 77.2099], [28.5672, 77.2100]
];

export function getVehicleById(id: string): Vehicle | undefined { return vehicles.find((v) => v.id === id); }
export function getHospitalById(id: string): Hospital | undefined { return hospitals.find((h) => h.id === id); }
export function getSignalById(id: string): Signal | undefined { return signals.find((s) => s.id === id); }

export function rankHospitals(vehicle: Vehicle, list: Hospital[]): Hospital[] {
  const typeMatch: Record<VehicleType, string[]> = {
    ambulance: ['Trauma Center', 'Pediatric Care'],
    fire_truck: ['Burn Unit', 'Trauma Center'],
    police: ['Trauma Center'],
    disaster: ['Trauma Center', 'Burn Unit'],
  };
  const preferred = typeMatch[vehicle.type] ?? [];
  return [...list].sort((a, b) => {
    let scoreA = a.distance + a.eta * 0.5 - a.beds * 0.01 - a.responseTime * 0.3;
    let scoreB = b.distance + b.eta * 0.5 - b.beds * 0.01 - b.responseTime * 0.3;
    const matchA = a.specializations.filter((s) => preferred.includes(s)).length;
    const matchB = b.specializations.filter((s) => preferred.includes(s)).length;
    scoreA -= matchA * 0.5;
    scoreB -= matchB * 0.5;
    return scoreA - scoreB;
  });
}

export function getConfidenceLabel(confidence: number): { label: string; level: 'high' | 'medium' | 'low' } {
  if (confidence >= 0.75) return { label: 'High confidence', level: 'high' };
  if (confidence >= 0.5) return { label: 'Medium confidence', level: 'medium' };
  return { label: 'Low confidence — verify manually', level: 'low' };
}

export function getSuggestedAction(vehicle: Vehicle): string {
  if (vehicle.confidence < 0.5) return 'Verify detection manually before routing';
  if (!vehicle.lockedRoute) return `Confirm route to ${vehicle.destination}`;
  if (vehicle.distanceToSignal < 0.5) return `Alert hospital — vehicle approaching Signal ${vehicle.corridorId?.replace('COR', 'SIG') ?? ''}`;
  return `Divert via Signal 3 for fastest route`;
}

export function buildContactLinks(hospital: Hospital, vehicle?: Vehicle) {
  const phone = hospital.phone.replace(/\s/g, '');
  const smsBody = vehicle
    ? `Emergency: ${vehicle.id} (${vehicle.type}) en route to ${hospital.name}. ETA ${vehicle.eta} min. Please prepare emergency bay.`
    : `Emergency response — please prepare for incoming patient.`;
  const emailSubject = vehicle ? `EMERGENCY: ${vehicle.id} en route to ${hospital.name}` : 'Emergency alert';
  const emailBody = vehicle
    ? `Emergency vehicle ${vehicle.id} (${vehicle.type}) is en route to ${hospital.name}.\n\nETA: ${vehicle.eta} minutes\nDistance: ${vehicle.distance} km\nCurrent location: ${vehicle.location}\n\nPlease prepare the emergency department for arrival.`
    : 'Please prepare for incoming emergency patient.';
  const waMessage = vehicle
    ? `🚨 EMERGENCY ALERT: ${vehicle.id} (${vehicle.type}) is en route to ${hospital.name}. ETA ${vehicle.eta} min. Please prepare emergency bay.`
    : '🚨 Emergency alert — please prepare for incoming patient.';
  return {
    call: `tel:${phone}`,
    email: `mailto:${hospital.email}?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`,
    sms: `sms:${phone}?body=${encodeURIComponent(smsBody)}`,
    whatsapp: `https://wa.me/${phone.replace('+', '')}?text=${encodeURIComponent(waMessage)}`,
  };
}

export function buildVehicleContactLinks(vehicle: Vehicle) {
  const phone = vehicle.driverPhone.replace(/\s/g, '');
  const smsBody = `IntelliCross: Your route to ${vehicle.destination} is confirmed. ETA ${vehicle.eta} min. Green wave active on corridor.`;
  const emailSubject = `Route update: ${vehicle.id}`;
  const emailBody = `Driver ${vehicle.driverName}, your route to ${vehicle.destination} has been confirmed.\n\nETA: ${vehicle.eta} minutes\nDistance: ${vehicle.distance} km\n\nGreen wave coordination is active. Please proceed safely.`;
  const waMessage = `🚑 IntelliCross: Route to ${vehicle.destination} confirmed. ETA ${vehicle.eta} min. Green wave active. Drive safe.`;
  return {
    call: `tel:${phone}`,
    email: `mailto:driver@intellicross.app?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`,
    sms: `sms:${phone}?body=${encodeURIComponent(smsBody)}`,
    whatsapp: `https://wa.me/${phone.replace('+', '')}?text=${encodeURIComponent(waMessage)}`,
  };
}
