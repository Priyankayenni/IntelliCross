import { motion } from 'framer-motion';
import { Baby, Flame, Mail, MapPin, MessageSquare, Navigation, Phone, ShieldCheck } from 'lucide-react';
import { buildContactLinks, type Hospital, type Vehicle } from '@/data';

type Props = {
  hospital: Hospital;
  recommended: boolean;
  vehicle?: Vehicle;
  onAction: (action: string, hospital: Hospital) => void;
};

export function HospitalCard({ hospital, recommended, vehicle, onAction }: Props) {
  const icons: Record<string, JSX.Element> = { 'Trauma Center': <ShieldCheck size={14} />, 'Burn Unit': <Flame size={14} />, 'Pediatric Care': <Baby size={14} /> };
  const contacts = buildContactLinks(hospital, vehicle);

  return (
    <motion.article className={`hospital-card ${recommended ? 'recommended' : ''}`} whileHover={{ y: -3 }}>
      <div className="hospital-top">
        <div className="hospital-icon"><span>+</span></div>
        <div className="hospital-heading">
          <div className="hospital-name">{hospital.name}</div>
          <div className="hospital-city"><MapPin size={12} /> {hospital.city.toUpperCase()}</div>
        </div>
        {recommended && <span className="recommended-tag">TOP MATCH</span>}
      </div>
      <div className="hospital-stats">
        <div><label>DISTANCE</label><strong>{hospital.distance} <small>KM</small></strong></div>
        <div><label>ETA</label><strong>{hospital.eta} <small>MIN</small></strong></div>
        <div><label>BEDS OPEN</label><strong className="beds">{hospital.beds}</strong><small> / {hospital.totalBeds}</small></div>
      </div>
      <div className="specializations">
        <label>CAPABILITIES</label>
        <div>{hospital.specializations.map((item) => <span key={item}>{icons[item]} {item}</span>)}</div>
      </div>
      <div className="hospital-footer">
        <div className="phone"><Phone size={14} /> {hospital.phone}<small>Response time {hospital.responseTime} min</small></div>
        <div className="contact-grid">
          <a href={contacts.call} className="contact-action" title="Call hospital"><Phone size={15} /> Call</a>
          <a href={contacts.sms} className="contact-action" title="SMS hospital"><MessageSquare size={15} /> SMS</a>
          <a href={contacts.whatsapp} target="_blank" rel="noreferrer" className="contact-action wa" title="WhatsApp hospital"><MessageSquare size={15} /> WhatsApp</a>
          <a href={contacts.email} className="contact-action" title="Email hospital"><Mail size={15} /> Email</a>
        </div>
        <div className="hospital-actions">
          <button onClick={() => onAction('Navigate', hospital)}><Navigation size={14} /> Navigate</button>
          <button onClick={() => onAction('Alert Staff', hospital)} className="dark-action">Alert Staff</button>
        </div>
      </div>
    </motion.article>
  );
}
