export default function StatusStrip({ status, connected }) {
  const items = [
    { label: 'Intersection', value: status?.intersection_id ?? '—' },
    { label: 'Mode', value: status?.mode ?? '—' },
    { label: 'Phase', value: status?.current_phase?.replace('_', ' ') ?? '—' },
    { label: 'Time in phase', value: status ? `${status.time_in_phase.toFixed(1)}s` : '—' },
    { label: 'Detection FPS', value: status ? status.avg_detection_fps.toFixed(1) : '—' },
  ]

  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 20px',
        borderBottom: '1px solid var(--line)',
        background: 'var(--bg-panel)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <span className="mono" style={{ fontSize: 16, fontWeight: 700, letterSpacing: '0.02em' }}>
          IntelliCross
        </span>
        <span className="eyebrow">command console</span>
      </div>

      <div style={{ display: 'flex', gap: 28 }}>
        {items.map((item) => (
          <div key={item.label} style={{ textAlign: 'right' }}>
            <div className="eyebrow" style={{ fontSize: 10 }}>{item.label}</div>
            <div className="mono" style={{ fontSize: 13, marginTop: 2 }}>{item.value}</div>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              width: 8, height: 8, borderRadius: '50%',
              background: connected ? 'var(--signal-green)' : 'var(--signal-red)',
            }}
          />
          <span className="mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {connected ? 'LIVE' : 'RECONNECTING'}
          </span>
        </div>
      </div>
    </header>
  )
}
