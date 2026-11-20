const APPROACH_POS = {
  N: { x: 210, y: 40, rot: 0 },
  S: { x: 210, y: 340, rot: 180 },
  E: { x: 380, y: 190, rot: 90 },
  W: { x: 40, y: 190, rot: -90 },
}

function isGreen(approach, phase) {
  if (phase === 'NS_GREEN') return approach === 'N' || approach === 'S'
  if (phase === 'EW_GREEN') return approach === 'E' || approach === 'W'
  return false
}

function SignalHead({ approach, density, active, emergencyApproach }) {
  const pos = APPROACH_POS[approach]
  const isEmergencyHere = emergencyApproach === approach
  return (
    <g transform={`translate(${pos.x}, ${pos.y})`}>
      <rect x="-16" y="-22" width="32" height="44" rx="4" fill="#0d1117" stroke="#2a323f" strokeWidth="1.5" />
      <circle cx="0" cy="-11" r="7" fill={active ? 'var(--signal-green)' : '#1c2430'} opacity={active ? 1 : 0.5}>
        {active && (
          <animate attributeName="opacity" values="1;0.65;1" dur="1.8s" repeatCount="indefinite" />
        )}
      </circle>
      <circle cx="0" cy="11" r="7" fill={!active ? 'var(--signal-red)' : '#1c2430'} opacity={!active ? 1 : 0.4} />
      <text x="0" y="34" textAnchor="middle" className="mono" fontSize="11" fill="var(--text-muted)">{approach}</text>
      <text x="0" y="47" textAnchor="middle" className="mono" fontSize="10" fill="var(--text-dim)">{density ?? 0}</text>
      {isEmergencyHere && (
        <circle cx="0" cy="-11" r="14" fill="none" stroke="var(--signal-red)" strokeWidth="2">
          <animate attributeName="r" values="10;18;10" dur="1.1s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.9;0;0.9" dur="1.1s" repeatCount="indefinite" />
        </circle>
      )}
    </g>
  )
}

export default function IntersectionView({ status }) {
  const phase = status?.current_phase ?? 'NS_GREEN'
  const density = status?.normal_traffic_density ?? {}
  const emergencyApproach = status?.active_emergency?.approach ?? null
  const preempting = Boolean(status?.active_emergency)

  return (
    <svg viewBox="0 0 420 380" width="100%" height="100%" role="img" aria-label="Intersection signal state">
      {/* Roads */}
      <rect x="170" y="0" width="80" height="380" fill="#171c25" />
      <rect x="0" y="150" width="420" height="80" fill="#171c25" />
      <rect x="170" y="150" width="80" height="80" fill="#1c222c" />

      {/* Lane markings */}
      <line x1="210" y1="0" x2="210" y2="150" stroke="#2c3541" strokeWidth="2" strokeDasharray="10 8" />
      <line x1="210" y1="230" x2="210" y2="380" stroke="#2c3541" strokeWidth="2" strokeDasharray="10 8" />
      <line x1="0" y1="190" x2="170" y2="190" stroke="#2c3541" strokeWidth="2" strokeDasharray="10 8" />
      <line x1="250" y1="190" x2="420" y2="190" stroke="#2c3541" strokeWidth="2" strokeDasharray="10 8" />

      {preempting && (
        <rect x="171" y="151" width="78" height="78" fill="none" stroke="var(--signal-red)" strokeWidth="2" opacity="0.7">
          <animate attributeName="opacity" values="0.8;0.2;0.8" dur="1.2s" repeatCount="indefinite" />
        </rect>
      )}

      {['N', 'S', 'E', 'W'].map((a) => (
        <SignalHead
          key={a}
          approach={a}
          density={density[a]}
          active={isGreen(a, phase)}
          emergencyApproach={emergencyApproach}
        />
      ))}
    </svg>
  )
}
