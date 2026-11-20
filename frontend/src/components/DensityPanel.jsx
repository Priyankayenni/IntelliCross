const APPROACHES = ['N', 'E', 'S', 'W']

export default function DensityPanel({ density }) {
  const max = Math.max(1, ...APPROACHES.map((a) => density?.[a] ?? 0))

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="eyebrow">Approach density</span>
        <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>vehicles queued</span>
      </div>
      <div style={{ padding: '18px 16px', display: 'flex', gap: 18, alignItems: 'flex-end', height: 120 }}>
        {APPROACHES.map((a) => {
          const value = density?.[a] ?? 0
          const heightPct = (value / max) * 100
          return (
            <div key={a} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, height: '100%', justifyContent: 'flex-end' }}>
              <span className="mono" style={{ fontSize: 12, color: 'var(--text-primary)' }}>{value}</span>
              <div
                style={{
                  width: '100%',
                  height: `${Math.max(heightPct, 4)}%`,
                  background: 'linear-gradient(180deg, var(--telemetry-cyan), rgba(53,198,224,0.15))',
                  borderRadius: '2px 2px 0 0',
                  transition: 'height 0.4s ease',
                }}
              />
              <span className="mono eyebrow">{a}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
