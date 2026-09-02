import { useEffect } from 'react';
import { Circle, MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { Corridor, Hospital, Signal, Vehicle } from '@/data';

type Props = {
  vehicle: Vehicle;
  hospital: Hospital;
  signals: Signal[];
  corridors: Corridor[];
  route: [number, number][];
  theme: 'dark' | 'light';
};

function Recenter({ position }: { position: [number, number] }) {
  const map = useMap();
  useEffect(() => { map.flyTo(position, 13, { duration: 0.8 }); }, [map, position]);
  return null;
}

const icon = (html: string, size: [number, number], anchor: [number, number]) =>
  L.divIcon({ html, className: 'custom-map-icon', iconSize: size, iconAnchor: anchor });

export function RealTimeMap({ vehicle, hospital, signals, corridors, route, theme }: Props) {
  const tileUrl = theme === 'dark'
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  const tileAttribution = theme === 'dark'
    ? '&copy; OpenStreetMap contributors &copy; CARTO'
    : '&copy; OpenStreetMap contributors';

  return (
    <div className="map-shell">
      <MapContainer center={vehicle.position} zoom={13} zoomControl={true} scrollWheelZoom={true}>
        <TileLayer attribution={tileAttribution} url={tileUrl} />
        <Recenter position={vehicle.position} />
        {corridors.map((corridor) => (
          <Circle key={corridor.id} center={corridor.center} radius={corridor.radius}
            pathOptions={{ color: '#f59e0b', fillColor: '#f59e0b', fillOpacity: 0.04, weight: 1, dashArray: '4 4' }} />
        ))}
        <Circle center={vehicle.position} radius={220}
          pathOptions={{ color: '#dc2626', fillColor: '#ef4444', fillOpacity: 0.12, weight: 1 }} />
        <Marker position={vehicle.position} icon={icon('<div class="map-vehicle"><span>+</span></div>', [42, 42], [21, 21])}>
          <Popup><b>{vehicle.id}</b><br />Live response vehicle<br />Confidence: {Math.round(vehicle.confidence * 100)}%</Popup>
        </Marker>
        <Marker position={hospital.position} icon={icon('<div class="map-hospital">+</div>', [34, 34], [17, 17])}>
          <Popup><b>{hospital.name}</b><br />Destination hospital<br />Beds: {hospital.beds}/{hospital.totalBeds}</Popup>
        </Marker>
        {signals.map((signal) => (
          <Marker key={signal.id} position={signal.position} icon={icon(`<div class="map-signal ${signal.state}"></div>`, [26, 26], [13, 13])}>
            <Popup><b>{signal.id}</b><br />{signal.state.toUpperCase()} · {signal.countdown}s{signal.preemption ? '<br />Preemption: ACTIVE' : ''}</Popup>
          </Marker>
        ))}
        <Polyline positions={route} pathOptions={{ color: '#16a34a', weight: 5, opacity: 0.85, dashArray: '8 8' }} />
      </MapContainer>
      <div className="map-legend">
        <span><i className="legend-dot red" /> Live unit</span>
        <span><i className="legend-dot blue" /> Hospital</span>
        <span><i className="legend-dot amber" /> Corridor</span>
        <span><i className="legend-line" /> Route</span>
      </div>
      <div className="map-label"><span className="map-live-dot" /> LIVE MAP FEED</div>
    </div>
  );
}
