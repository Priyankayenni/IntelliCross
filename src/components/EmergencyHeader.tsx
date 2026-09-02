import { motion } from 'framer-motion';
import { Activity, Bell, ChevronDown, Menu, Monitor, Moon, Radio, ShieldCheck, Sun, User } from 'lucide-react';
import type { Role } from '@/data';

type Props = {
  alertCount: number;
  isLive: boolean;
  onAlerts: () => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  role: Role;
  onRoleChange: (role: Role) => void;
  modelStatus: string;
  latency: number;
};

export function EmergencyHeader({ alertCount, isLive, onAlerts, theme, onToggleTheme, role, onRoleChange, modelStatus, latency }: Props) {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <div className="brand-wrap">
          <button className="mobile-menu" aria-label="Open menu"><Menu size={21} /></button>
          <div className="brand-mark"><ShieldCheck size={22} strokeWidth={2.5} /></div>
          <div>
            <div className="brand-name">Intelli<span>Cross</span></div>
            <div className="brand-sub">EMERGENCY RESPONSE OS</div>
          </div>
        </div>
        <div className="header-center">
          <span className="header-context">Delhi NCR Command Center</span>
          <span className="header-divider" />
          <span className="status-pill"><Activity size={11} /> {modelStatus}</span>
          <span className="status-pill latency">{latency}ms</span>
        </div>
        <div className="header-actions">
          <div className="role-switcher">
            <button className={role === 'operator' ? 'active' : ''} onClick={() => onRoleChange('operator')}><Monitor size={14} /> Operator</button>
            <button className={role === 'driver' ? 'active' : ''} onClick={() => onRoleChange('driver')}><User size={14} /> Driver</button>
          </div>
          <button className="theme-toggle" onClick={onToggleTheme} aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <div className="live-status">
            <motion.span className="live-dot" animate={{ opacity: [1, 0.35, 1] }} transition={{ duration: 1.6, repeat: Infinity }} />
            <span>{isLive ? 'LIVE' : 'OFFLINE'}</span>
          </div>
          <button className="alert-button" onClick={onAlerts} aria-label="View alerts">
            <Bell size={19} />
            {alertCount > 0 && <span>{alertCount}</span>}
          </button>
          <div className="operator">
            <div className="operator-avatar">AK</div>
            <div className="operator-info">
              <strong>Arjun Kapoor</strong>
              <small>DISPATCH OPERATOR</small>
            </div>
            <ChevronDown size={15} />
          </div>
        </div>
      </div>
    </header>
  );
}
