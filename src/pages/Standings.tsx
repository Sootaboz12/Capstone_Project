import { useState } from 'react'
import TeamCrest from '../components/Teamcrest'
import { teams } from '../data/teams'

type ConferenceFilter = 'All' | 'AFC' | 'NFC'

const filters: ConferenceFilter[] = ['All', 'AFC', 'NFC']

const rankedTeams = [...teams].sort((teamA, teamB) =>
  teamB.stats.wins - teamA.stats.wins ||
  teamA.stats.losses - teamB.stats.losses ||
  teamA.abbr.localeCompare(teamB.abbr),
)

function Standings() {
  const [conference, setConference] = useState<ConferenceFilter>('All')
  const visibleTeams = rankedTeams.filter(
    (team) => conference === 'All' || team.conference === conference,
  )

  return (
    <section className="standings-page">
      <header className="standings__header">
        <div>
          <p className="section-kicker">League table</p>
          <h1 className="standings__title">Current standings</h1>
          <p className="standings__description">
            Every team, ranked by wins for the 2026 regular season.
          </p>
        </div>
        <div className="standings__season">2026 SEASON</div>
      </header>

      <div className="standings__controls">
        <div className="standings__filters" aria-label="Filter by conference">
          {filters.map((filter) => (
            <button
              type="button"
              key={filter}
              className={`standings__filter${conference === filter ? ' is-active' : ''}`}
              aria-pressed={conference === filter}
              onClick={() => setConference(filter)}
            >
              {filter}
            </button>
          ))}
        </div>
        <p className="standings__count">{visibleTeams.length} teams</p>
      </div>

      <div className="standings__table-wrap">
        <table className="standings__table">
          <caption className="sr-only">2026 NFL team standings ordered by wins</caption>
          <thead>
            <tr>
              <th scope="col">Rank</th>
              <th scope="col">Team</th>
              <th scope="col">Division</th>
              <th scope="col">W</th>
              <th scope="col">L</th>
              <th scope="col">T</th>
              <th scope="col">Win %</th>
            </tr>
          </thead>
          <tbody>
            {visibleTeams.map((team, index) => {
              const gamesPlayed = team.stats.wins + team.stats.losses + team.stats.ties
              const winPercentage = gamesPlayed
                ? ((team.stats.wins + team.stats.ties / 2) / gamesPlayed).toFixed(3)
                : '.000'

              return (
                <tr key={team.id} className={index === 0 ? 'is-leader' : undefined}>
                  <td className="standings__rank">{String(index + 1).padStart(2, '0')}</td>
                  <td className="standings__team">
                    <div className="standings__team-info">
                      <TeamCrest team={team} size="sm" />
                      <span>
                        <strong>{team.city} {team.name}</strong>
                        <small>{team.abbr}</small>
                      </span>
                    </div>
                  </td>
                  <td>{team.conference} {team.division}</td>
                  <td className="standings__wins">{team.stats.wins}</td>
                  <td>{team.stats.losses}</td>
                  <td>{team.stats.ties}</td>
                  <td>{winPercentage}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <p className="standings__disclaimer">
        Win totals are placeholder data and do not represent actual 2026 results.
        Ties in wins are ordered by fewer losses, then team abbreviation.
      </p>
    </section>
  )
}

export default Standings