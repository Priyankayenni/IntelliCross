import { motion } from 'framer-motion';
import { ArrowUpRight, CheckCircle2, CircleAlert, Clock3, Radio, Zap } from 'lucide-react';
import type { Signal } from '@/data';

type Props = { signals: Signal[] };

export function TrafficSignalPanel({ signals }: Props) {
  const preempted = signals.filter((s) => s.preemption);

  return (
    <section className="signals-panel">
      <div className="section-heading">
        <div>
          <div className="eyebrow"><Radio size={13} /> LIVE COORDINATION</div>
          <h2>Traffic Signal Control</h2>
        </div>
        <button className="text-button">View all signals <ArrowUpRight size={15} /></button>
      </div>
      <div className="signals-grid">
        {signals.map((signal, index) => (
          <motion.div key={signal.id} className={`signal-card ${signal.state} ${signal.preemption ? 'preempted' : ''}`}
            animate={signal.state === 'green' ? { borderColor: ['var(--signal-green-border)', 'var(--signal-green-active)', 'var(--signal-green-border)'] } : {}}
            transition={{ duration: 2, repeat: Infinity }}>
            <div className="signal-head">
              <span>{signal.id}</span>
              {signal.preemption && <span className="preempt-badge"><Zap size={9} /> PREEMPT</span>}
              <span className={`signal-light ${signal.state}`} />
            </div>
            <div className="signal-count">{signal.countdown}<small>sec</small></div>
            <div className="signal-state">
              {signal.state === 'green' ? <CheckCircle2 size={13} /> : <CircleAlert size={13} />} {signal.state.toUpperCase()}
            </div>
            <div className="signal-label">CHECKPOINT {String(index + 1).padStart(2, '0')}</div>
          </motion.div>
        ))}
      </div>

      {preempted.length > 0 && (
        <div className="preemption-preview">
          <div className="preempt-icon"><Zap size={16} /></div>
          <div className="preempt-info">
            <label>SIGNAL PREEMPTION PREVIEW</label>
            <strong>{preempted.map((s) => s.id).join(', ')} turning green for emergency passage</strong>
            <div className="preempt-timeline">
              {preempted.map((s) => (
                <span key={s.id} className="preempt-step">
                  <span className="preempt-dot green" />
                  {s.id} {s.preemptionTime === 0 ? 'now' : `+${s.preemptionTime}s`}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="green-wave">
        <div className="wave-icon"><Clock3 size={18} /></div>
        <div>
          <label>GREEN WAVE STATUS</label>
          <strong>Optimal passage window detected</strong>
        </div>
        <div className="wave-probability">
          <strong>85%</strong>
          <span>PROBABILITY</span>
        </div>
        <span className="wave-live"><span /> ACTIVE</span>
      </div>
    </section>
  );
}
