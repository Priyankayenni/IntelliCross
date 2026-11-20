import { useEffect, useRef, useState } from 'react'

export default function EventLog({ lastPreemption }) {
  const [log, setLog] = useState([])
  const seen = useRef(new Set())

  useEffect(() => {
    if (!lastPreemption) return
    const key = `${lastPreemption.issued_at}-${lastPreemption.triggered_by}`
    if (seen.current.has(key)) return
    seen.current.add(key)
    setLog((prev) => [
      { ...lastPreemption, receivedAt: new Date() },
      ...prev,
    ].slice(0, 12))
  }, [lastPreemption])

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1 }}>
      <div className="panel-header">
        <span className="eyebrow">Preemption log</span>
        <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>{log.length} events</span>
      </div>
      <div style={{ overflowY: 'auto', flex: 1 }}>
        {log.length === 0 && (
          <div className="mono" style={{ padding: 16, fontSize: 12, color: 'var(--text-dim)' }}>
            No preemption commands issued yet.
          </div>
        )}
        {log.map((entry, i) => (
          <div
            key={i}
            style={{
              padding: '10px 16px',
              borderBottom: '1px solid var(--line)',
              display: 'flex',
              justifyContent: 'space-between',
              gap: 10,
              animation: i === 0 ? 'fade-in-up 0.25s ease' : 'none',
            }}
          >
            <div>
              <div style={{ fontSize: 13 }}>{entry.target_phase.replace('_', ' ')}</div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {entry.reason.replaceAll('_', ' ')}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="mono" style={{ fontSize: 11, color: 'var(--telemetry-cyan)' }}>
                hold {entry.hold_seconds.toFixed(1)}s
              </div>
              <div className="mono" style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                {entry.receivedAt.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
