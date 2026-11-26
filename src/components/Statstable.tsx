import type { Team } from '../data/teams'
import type { MatchupTeamStats } from '../libs/Predictions'

interface StatsTableProps {
  teamA: Team
  teamB: Team
  statsA: MatchupTeamStats
  statsB: MatchupTeamStats
}

function StatsTable({ teamA, teamB, statsA, statsB }: StatsTableProps) {
  const rows: { label: string; a: string; b: string }[] = [
    { label: 'Record', a: `${statsA.wins}-${statsA.losses}-${statsA.ties}`, b: `${statsB.wins}-${statsB.losses}-${statsB.ties}` },
    { label: 'Win percentage', a: `${(statsA.win_pct * 100).toFixed(1)}%`, b: `${(statsB.win_pct * 100).toFixed(1)}%` },
    { label: 'Points scored / game', a: statsA.points_for_per_game.toFixed(1), b: statsB.points_for_per_game.toFixed(1) },
    { label: 'Points allowed / game', a: statsA.points_against_per_game.toFixed(1), b: statsB.points_against_per_game.toFixed(1) },
    { label: 'Home record', a: `${statsA.home_wins}-${statsA.home_losses}-${statsA.home_ties}`, b: `${statsB.home_wins}-${statsB.home_losses}-${statsB.home_ties}` },
    { label: 'Away record', a: `${statsA.away_wins}-${statsA.away_losses}-${statsA.away_ties}`, b: `${statsB.away_wins}-${statsB.away_losses}-${statsB.away_ties}` },
  ]

  return (
    <div className="stats-table-wrap">
      <table className="stats-table">
        <thead>
          <tr>
            <th scope="col">Stat</th>
            <th scope="col">{teamA.abbr}</th>
            <th scope="col">{teamB.abbr}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th scope="row">{row.label}</th>
              <td>{row.a}</td>
              <td>{row.b}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default StatsTable