import { motion } from 'framer-motion';
import { ArrowUpRight, Clock3, Lock, MapPin, MessageSquare, Navigation, Phone, Radio, Route as RouteIcon, Zap, AlertTriangle, Mail } from 'lucide-react';
import { getConfidenceLabel, getSuggestedAction, buildVehicleContactLinks, type Vehicle } from '@/data';

const labels = { ambulance: 'AMBULANCE', fire_truck: 'FIRE RESPONSE', police: 'POLICE RESPONSE', disaster: 'DISASTER RESPONSE' };
const icons = { ambulance: '✚', fire_truck: '♜', police: '★', disaster: '!' };

type Props = {
  vehicle: Vehicle;
  selected: boolean;
  onSelect: () => void;
  onLockRoute: () => void;
  onContact: (channel: string) => void;
};

export function VehicleCard({ vehicle, selected, onSelect, onLockRoute, onContact }: Props) {
  const conf = getConfidenceLabel(vehicle.confidence);
  const suggestion = getSuggestedAction(vehicle);
  const contacts = buildVehicleContactLinks(vehicle);

  return (
    <motion.article className={`vehicle-card ${selected ? 'selected' : ''}`} whileHover={{ y: -3 }}>
      <div className={`vehicle-band ${vehicle.type}`}>
        <div className="vehicle-title">
          <span className="vehicle-symbol">{icons[vehicle.type]}</span>
          <div>
            <div className="vehicle-id">{vehicle.id}</div>
            <div className="vehicle-type">{labels[vehicle.type]}</div>
          </div>
        </div>
        <div className="vehicle-badges">
          {vehicle.lockedRoute && <span className="lock-badge"><Lock size={9} /> LOCKED</span>}
          {vehicle.corridorId && <span className="corridor-badge">CORRIDOR</span>}
          <span className="live-pill"><Radio size={11} /> LIVE</span>
        </div>
      </div>
      <div className="vehicle-body">
        <div className="location-row">
          <div>
            <label>CURRENT LOCATION</label>
            <strong>{vehicle.location}</strong>
          </div>
          <ArrowUpRight size={18} className="muted-icon" />
        </div>
        <div className="destination-row">
          <Navigation size={15} />
          <span>Bound for <b>{vehicle.destination}</b></span>
        </div>
        <div className="metric-grid">
          <div><label><MapPin size={12} /> DISTANCE</label><strong>{vehicle.distance} <small>KM</small></strong></div>
          <div><label><Clock3 size={12} /> ETA</label><strong>{vehicle.eta} <small>MIN</small></strong></div>
          <div><label><Zap size={12} /> SPEED</label><strong>{vehicle.speed} <small>KM/H</small></strong></div>
        </div>
        <div className="confidence">
          <div>
            <label>DETECTION CONFIDENCE</label>
            <b className={conf.level}>{Math.round(vehicle.confidence * 100)}%</b>
          </div>
          <div className={`confidence-track ${conf.level}`}>
            <motion.div initial={{ width: 0 }} animate={{ width: `${vehicle.confidence * 100}%` }} />
          </div>
          {conf.level === 'low' && <div className="confidence-warn"><AlertTriangle size={11} /> {conf.label}</div>}
        </div>
        {vehicle.corridorId && (
          <div className="corridor-info">
            <span className="corridor-dist">{vehicle.distanceToSignal} km to nearest signal</span>
          </div>
        )}
        <div className="suggestion-box">{suggestion}</div>
        <div className="contact-row">
          <a href={contacts.call} className="contact-btn" title="Call driver"><Phone size={14} /></a>
          <a href={contacts.sms} className="contact-btn" title="SMS driver"><MessageSquare size={14} /></a>
          <a href={contacts.whatsapp} target="_blank" rel="noreferrer" className="contact-btn wa" title="WhatsApp driver"><MessageSquare size={14} /></a>
          <a href={contacts.email} className="contact-btn" title="Email driver"><Mail size={14} /></a>
        </div>
      </div>
      <div className="vehicle-footer">
        <button className="route-button" onClick={onSelect}><RouteIcon size={15} /> VIEW ROUTE <ArrowUpRight size={14} /></button>
        <button className={`lock-button ${vehicle.lockedRoute ? 'locked' : ''}`} onClick={onLockRoute}>
          <Lock size={14} /> {vehicle.lockedRoute ? 'Locked' : 'Lock'}
        </button>
      </div>
    </motion.article>
  );
}
