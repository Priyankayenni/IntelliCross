import { useState } from 'react';
import { Mail, MessageSquare, Phone, Send, Users } from 'lucide-react';
import { buildContactLinks, buildVehicleContactLinks, hospitals, vehicles, type ContactChannel, type ContactLog } from '@/data';

type Props = {
  selectedVehicleId: string;
  onLogContact: (log: ContactLog) => void;
  contactLogs: ContactLog[];
};

export function ContactPanel({ selectedVehicleId, onLogContact, contactLogs }: Props) {
  const [target, setTarget] = useState<'vehicle' | 'hospital'>('hospital');
  const [selectedId, setSelectedId] = useState(hospitals[0].id);

  const vehicle = vehicles.find((v) => v.id === selectedVehicleId) ?? vehicles[0];
  const hospital = hospitals.find((h) => h.id === selectedId) ?? hospitals[0];

  const contacts = target === 'hospital' ? buildContactLinks(hospital, vehicle) : buildVehicleContactLinks(vehicle);
  const targetName = target === 'hospital' ? hospital.name : `${vehicle.id} (${vehicle.driverName})`;

  const handleContact = (channel: ContactChannel) => {
    const log: ContactLog = {
      id: `cl-${Date.now()}`,
      timestamp: Date.now(),
      channel,
      target: target === 'hospital' ? hospital.phone : vehicle.driverPhone,
      targetName,
      operatorId: 'AK',
      vehicleId: vehicle.id,
      status: 'sent',
    };
    onLogContact(log);
  };

  const channels: { key: ContactChannel; label: string; icon: JSX.Element; href: string }[] = [
    { key: 'call', label: 'Call', icon: <Phone size={16} />, href: contacts.call },
    { key: 'sms', label: 'SMS', icon: <MessageSquare size={16} />, href: contacts.sms },
    { key: 'whatsapp', label: 'WhatsApp', icon: <MessageSquare size={16} />, href: contacts.whatsapp },
    { key: 'email', label: 'Email', icon: <Mail size={16} />, href: contacts.email },
  ];

  return (
    <div className="contact-panel">
      <div className="contact-panel-header">
        <Users size={16} />
        <h3>Quick Contact</h3>
      </div>
      <div className="contact-target-switch">
        <button className={target === 'hospital' ? 'active' : ''} onClick={() => setTarget('hospital')}>Hospital</button>
        <button className={target === 'vehicle' ? 'active' : ''} onClick={() => setTarget('vehicle')}>Driver</button>
      </div>
      {target === 'hospital' && (
        <select className="contact-select" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
          {hospitals.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
        </select>
      )}
      {target === 'vehicle' && (
        <div className="contact-target-info">
          <strong>{vehicle.id}</strong>
          <span>{vehicle.driverName} · {vehicle.driverPhone}</span>
        </div>
      )}
      <div className="contact-channels">
        {channels.map((ch) => (
          <a key={ch.key} href={ch.href} target={ch.key === 'whatsapp' ? '_blank' : undefined} rel="noreferrer"
            className="contact-channel-btn" onClick={() => handleContact(ch.key)}>
            {ch.icon}
            <span>{ch.label}</span>
          </a>
        ))}
      </div>
      <div className="contact-log-section">
        <label>CONTACT LOG</label>
        {contactLogs.length === 0 ? (
          <div className="contact-log-empty">No contact attempts yet</div>
        ) : (
          contactLogs.slice(0, 8).map((log) => (
            <div key={log.id} className="contact-log-row">
              <span className={`log-channel ${log.channel}`}>{log.channel.toUpperCase()}</span>
              <span className="log-target">{log.targetName}</span>
              <span className="log-time">{new Date(log.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
