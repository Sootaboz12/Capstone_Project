import type { Team } from '../data/teams'

interface StatsTableProps {
  teamA: Team
  teamB: Team
}

function StatsTable({ teamA, teamB }: StatsTableProps) {
  const rows: { label: string; a: string; b: string }[] = [
    { label: 'Record', a: `${teamA.stats.wins}-${teamA.stats.losses}`, b: `${teamB.stats.wins}-${teamB.stats.losses}` },
    { label: 'Streak', a: teamA.stats.streak, b: teamB.stats.streak },
    { label: 'Power rank', a: `#${teamA.stats.powerRank}`, b: `#${teamB.stats.powerRank}` },
    {
      label: 'Turnover margin',
      a: `${teamA.stats.turnoverMargin > 0 ? '+' : ''}${teamA.stats.turnoverMargin}`,
      b: `${teamB.stats.turnoverMargin > 0 ? '+' : ''}${teamB.stats.turnoverMargin}`,
    },
    { label: 'Home record', a: teamA.stats.homeRecord, b: teamB.stats.homeRecord },
    { label: 'Away record', a: teamA.stats.awayRecord, b: teamB.stats.awayRecord },
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