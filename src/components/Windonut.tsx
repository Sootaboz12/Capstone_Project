import type { CSSProperties } from 'react'
import type { Team } from '../data/teams'

interface WinDonutProps {
  teamA: Team
  teamB: Team
  pctA: number
  pctB: number
}

function WinDonut({ teamA, teamB, pctA, pctB }: WinDonutProps) {
  const favorite = pctA >= pctB ? teamA : teamB
  const favoritePct = Math.max(pctA, pctB)

  return (
    <div className="win-donut-block">
      <div
        className="win-donut"
        style={
          {
            '--colorA': teamA.colors.primary,
            '--colorB': teamB.colors.primary,
            '--pctA': pctA,
          } as CSSProperties
        }
        role="img"
        aria-label={`${favorite.city} ${favorite.name} favored at ${favoritePct}%`}
      >
        <div className="win-donut__center">
          <span className="win-donut__pct">{favoritePct}%</span>
          <span className="win-donut__who">{favorite.abbr} to win</span>
        </div>
      </div>

      <ul className="win-donut__legend">
        <li>
          <span className="win-donut__swatch" style={{ background: teamA.colors.primary }} />
          {teamA.abbr} <strong>{pctA}%</strong>
        </li>
        <li>
          <span className="win-donut__swatch" style={{ background: teamB.colors.primary }} />
          {teamB.abbr} <strong>{pctB}%</strong>
        </li>
      </ul>
    </div>
  )
}

export default WinDonut