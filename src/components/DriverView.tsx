import { motion } from 'framer-motion';
import { ArrowRight, ArrowUpRight, Clock3, MapPin, MessageSquare, Navigation, Phone, Radio, Siren, Zap } from 'lucide-react';
import { buildContactLinks, getHospitalById, type Vehicle } from '@/data';

type Props = {
  vehicle: Vehicle;
  onShareETA: () => void;
  onRequestGreenWave: () => void;
};

export function DriverView({ vehicle, onShareETA, onRequestGreenWave }: Props) {
  const hospital = getHospitalById(vehicle.destinationHospitalId);
  const contacts = hospital ? buildContactLinks(hospital, vehicle) : null;
  const turnHints = [
    { dir: 'straight', label: 'Continue straight', distance: '800m', icon: <ArrowUpRight size={32} /> },
    { dir: 'right', label: 'Turn right at Signal 3', distance: '1.2 km', icon: <ArrowRight size={32} /> },
    { dir: 'straight', label: 'Continue to AIIMS', distance: '2.1 km', icon: <ArrowUpRight size={32} /> },
  ];

  return (
    <div className="driver-view">
      <motion.div className="driver-hero" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="driver-hero-top">
          <div className="driver-vehicle-icon"><Siren size={28} /></div>
          <div>
            <div className="driver-vehicle-id">{vehicle.id}</div>
            <div className="driver-vehicle-type">{vehicle.type.toUpperCase()} UNIT</div>
          </div>
          <div className="driver-live"><Radio size={12} /> LIVE</div>
        </div>
        <div className="driver-eta-display">
          <div className="driver-eta-main">
            <Clock3 size={28} />
            <strong>{vehicle.eta}</strong>
            <small>MIN</small>
          </div>
          <div className="driver-eta-sub">
            <span><MapPin size={14} /> {vehicle.distance} km to destination</span>
            <span><Zap size={14} /> {vehicle.speed} km/h</span>
          </div>
        </div>
        <div className="driver-destination">
          <Navigation size={18} />
          <div>
            <label>DESTINATION</label>
            <strong>{vehicle.destination}</strong>
          </div>
        </div>
      </motion.div>

      <div className="driver-turn-section">
        <label className="driver-section-label">NEXT TURNS</label>
        <div className="turn-list">
          {turnHints.map((hint, i) => (
            <motion.div key={i} className="turn-item" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}>
              <div className={`turn-arrow ${hint.dir}`}>{hint.icon}</div>
              <div className="turn-info">
                <strong>{hint.label}</strong>
                <span>{hint.distance}</span>
              </div>
              {i === 0 && <span className="turn-next">NOW</span>}
            </motion.div>
          ))}
        </div>
      </div>

      <div className="driver-actions">
        <label className="driver-section-label">QUICK ACTIONS</label>
        <div className="driver-action-grid">
          {contacts && <a href={contacts.call} className="driver-action-btn call"><Phone size={22} /><span>Call Hospital</span></a>}
          <button className="driver-action-btn" onClick={onShareETA}><MessageSquare size={22} /><span>Share ETA</span></button>
          <button className="driver-action-btn green-wave" onClick={onRequestGreenWave}><Zap size={22} /><span>Request Green Wave</span></button>
        </div>
      </div>

      {hospital && (
        <div className="driver-hospital-info">
          <label>HOSPITAL DETAILS</label>
          <div className="driver-hospital-row"><span>Beds available</span><strong>{hospital.beds}/{hospital.totalBeds}</strong></div>
          <div className="driver-hospital-row"><span>Response time</span><strong>{hospital.responseTime} min</strong></div>
          <div className="driver-hospital-row"><span>Specializations</span><strong>{hospital.specializations.join(', ')}</strong></div>
        </div>
      )}
    </div>
  );
}
