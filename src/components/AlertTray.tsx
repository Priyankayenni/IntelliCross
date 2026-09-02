import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Bell, BellRing, Check, Info, ShieldAlert, Volume2, VolumeX, X } from 'lucide-react';
import type { AlertItem, AlertSeverity } from '@/data';

type Props = {
  alerts: AlertItem[];
  barkQueue: AlertItem[];
  soundEnabled: boolean;
  onToggleSound: () => void;
  onAcknowledge: (id: string) => void;
  onDismissBark: (id: string) => void;
  onClearAll: () => void;
  onSelectVehicle: (vehicleId: string) => void;
};

const severityIcon: Record<AlertSeverity, JSX.Element> = {
  critical: <ShieldAlert size={16} />,
  warning: <AlertTriangle size={16} />,
  info: <Info size={16} />,
};

function timeAgo(ts: number): string {
  const sec = Math.floor((Date.now() - ts) / 1000);
  if (sec < 60) return `${sec}s ago`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  return `${Math.floor(sec / 3600)}h ago`;
}

export function AlertTray({ alerts, barkQueue, soundEnabled, onToggleSound, onAcknowledge, onDismissBark, onClearAll, onSelectVehicle }: Props) {
  const unack = alerts.filter((a) => !a.acknowledged);

  return (
    <>
      <AnimatePresence>
        {barkQueue.map((alert) => (
          <motion.div
            key={alert.id}
            className={`bark-notification ${alert.severity}`}
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          >
            <div className="bark-icon">{severityIcon[alert.severity]}</div>
            <div className="bark-content">
              <strong>{alert.message}</strong>
              <span>{alert.vehicleId} · {alert.location} · ETA {alert.eta} min</span>
            </div>
            <button onClick={() => { onDismissBark(alert.id); onSelectVehicle(alert.vehicleId); }}><Check size={16} /></button>
            <button onClick={() => onDismissBark(alert.id)}><X size={16} /></button>
          </motion.div>
        ))}
      </AnimatePresence>

      <div className="alert-tray">
        <div className="alert-tray-header">
          <div className="alert-tray-title">
            <BellRing size={18} />
            <h3>Alert Tray</h3>
            {unack.length > 0 && <span className="alert-count">{unack.length}</span>}
          </div>
          <div className="alert-tray-actions">
            <button className="sound-toggle" onClick={onToggleSound} title={soundEnabled ? 'Mute alerts' : 'Enable sound'}>
              {soundEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
            </button>
            <button className="clear-all" onClick={onClearAll}>Ack all</button>
          </div>
        </div>
        <div className="alert-list">
          {alerts.map((alert) => (
            <div key={alert.id} className={`alert-row ${alert.severity} ${alert.acknowledged ? 'acknowledged' : ''}`}>
              <div className="alert-row-icon">{severityIcon[alert.severity]}</div>
              <div className="alert-row-body">
                <div className="alert-row-msg">{alert.message}</div>
                <div className="alert-row-meta">
                  <span>{alert.vehicleId}</span>
                  <span>·</span>
                  <span>{alert.location}</span>
                  <span>·</span>
                  <span>Conf {Math.round(alert.confidence * 100)}%</span>
                  <span>·</span>
                  <span>→ {alert.nearestHospital}</span>
                  <span>·</span>
                  <span>ETA {alert.eta}m</span>
                </div>
                <div className="alert-row-time">{timeAgo(alert.timestamp)}</div>
              </div>
              {!alert.acknowledged && (
                <button className="ack-btn" onClick={() => onAcknowledge(alert.id)}>
                  <Check size={14} /> Ack
                </button>
              )}
            </div>
          ))}
          {alerts.length === 0 && <div className="alert-empty"><Bell size={24} /> No active alerts</div>}
        </div>
      </div>
    </>
  );
}
