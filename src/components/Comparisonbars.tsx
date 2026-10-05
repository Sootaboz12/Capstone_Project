import type { Team } from '../data/teams'

export interface Metric {
  label: string
  a: number
  b: number
  suffix?: string
}

interface ComparisonBarsProps {
  teamA: Team
  teamB: Team
  metrics: Metric[]
}

function ComparisonBars({ teamA, teamB, metrics }: ComparisonBarsProps) {
  return (
    <div className="bars">
      {metrics.map((m) => {
        const max = Math.max(m.a, m.b, 1)
        const widthA = Math.max(6, Math.round((m.a / max) * 100))
        const widthB = Math.max(6, Math.round((m.b / max) * 100))
        return (
          <div className="bars__row" key={m.label}>
            <p className="bars__label">{m.label}</p>
            <div className="bars__track">
              <span className="bars__team">{teamA.abbr}</span>
              <div className="bars__bar">
                <span style={{ width: `${widthA}%`, background: teamA.colors.primary }} />
              </div>
              <span className="bars__value">{m.a}{m.suffix ?? ''}</span>
            </div>
            <div className="bars__track">
              <span className="bars__team">{teamB.abbr}</span>
              <div className="bars__bar">
                <span style={{ width: `${widthB}%`, background: teamB.colors.primary }} />
              </div>
              <span className="bars__value">{m.b}{m.suffix ?? ''}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default ComparisonBars