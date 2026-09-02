import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle2, Eye, MapPin, MessageSquare, Navigation, Radio, ShieldAlert, Zap } from 'lucide-react';
import { timelineEvents, type TimelineEvent } from '@/data';

const eventIcons: Record<TimelineEvent['type'], JSX.Element> = {
  detection: <Eye size={14} />,
  route_assigned: <Navigation size={14} />,
  signal_preemption: <Zap size={14} />,
  hospital_alerted: <ShieldAlert size={14} />,
  contact_made: <MessageSquare size={14} />,
  arrival: <CheckCircle2 size={14} />,
  route_locked: <AlertTriangle size={14} />,
};

function timeAgo(ts: number): string {
  const sec = Math.floor((Date.now() - ts) / 1000);
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m`;
  return `${Math.floor(sec / 3600)}h`;
}

type Props = { vehicleId: string };

export function IncidentTimeline({ vehicleId }: Props) {
  const events = timelineEvents.filter((e) => e.vehicleId === vehicleId);

  return (
    <div className="timeline-panel">
      <div className="timeline-header">
        <Radio size={14} />
        <h3>Incident Timeline</h3>
        <span className="timeline-vehicle">{vehicleId}</span>
      </div>
      <div className="timeline-list">
        {events.map((event, i) => (
          <motion.div key={event.id} className="timeline-item" initial={{ opacity: 0, x: -15 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}>
            <div className="timeline-dot">{eventIcons[event.type]}</div>
            <div className="timeline-content">
              <div className="timeline-label">{event.label}</div>
              <div className="timeline-time">{timeAgo(event.timestamp)} ago</div>
            </div>
          </motion.div>
        ))}
        {events.length === 0 && <div className="timeline-empty">No events recorded</div>}
      </div>
    </div>
  );
}
