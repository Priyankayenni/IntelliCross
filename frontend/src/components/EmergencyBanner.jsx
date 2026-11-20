export default function EmergencyBanner({ event }) {
  if (!event) {
    return (
      <div className="panel" style={{ padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ width: 9, height: 9, borderRadius: '50%', background: 'var(--signal-green)', display: 'inline-block' }} />
        <span className="mono" style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          No emergency vehicles detected — normal cycling active
        </span>
      </div>
    )
  }

  return (
    <div
      className="panel"
      style={{
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 16,
        borderColor: 'var(--signal-red)',
        background: 'linear-gradient(180deg, rgba(255,77,94,0.10), rgba(255,77,94,0.03))',
        animation: 'fade-in-up 0.25s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span
          style={{
            width: 10, height: 10, borderRadius: '50%', background: 'var(--signal-red)',
            display: 'inline-block', animation: 'pulse-ring 1.4s infinite',
          }}
        />
        <div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>
            {event.vehicle_class.replace('_', ' ').toUpperCase()} inbound on {event.approach}
          </div>
          <div className="mono" style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
            ETA {event.eta_seconds.toFixed(1)}s · {event.distance_m.toFixed(0)}m out · {(event.speed_mps * 3.6).toFixed(0)} km/h
          </div>
        </div>
      </div>
      <div className="mono eyebrow" style={{ color: 'var(--signal-red)' }}>Preemption active</div>
    </div>
  )
}
