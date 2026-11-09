import { useEffect, useMemo, useState } from 'react'
import TeamCrest from '../components/Teamcrest'
import { teams, type Team } from '../data/teams'

type ConferenceFilter = 'All' | 'AFC' | 'NFC'

interface Standing {
  team: string
  team_name: string
  team_conf: 'AFC' | 'NFC'
  team_division: string
  wins: number
  losses: number
  ties: number
  winning_percent: number
  pf: number
  pa: number
  home_record: string | null
  away_record: string | null
  streak: string | null
}

const filters: ConferenceFilter[] = ['All', 'AFC', 'NFC']

function isStanding(value: unknown): value is Standing {
  if (typeof value !== 'object' || value === null) return false

  const row = value as Record<string, unknown>
  return (
    typeof row.team === 'string' &&
    typeof row.team_name === 'string' &&
    (row.team_conf === 'AFC' || row.team_conf === 'NFC') &&
    typeof row.team_division === 'string' &&
    typeof row.wins === 'number' &&
    typeof row.losses === 'number' &&
    typeof row.ties === 'number' &&
    typeof row.winning_percent === 'number' &&
    typeof row.pf === 'number' &&
    typeof row.pa === 'number' &&
    (typeof row.home_record === 'string' || row.home_record === null) &&
    (typeof row.away_record === 'string' || row.away_record === null) &&
    (typeof row.streak === 'string' || row.streak === null)
  )
}

function getWinPercentage(standing: Standing) {
  const gamesPlayed = standing.wins + standing.losses + standing.ties
  return gamesPlayed
    ? (standing.wins + standing.ties / 2) / gamesPlayed
    : 0
}

function compareStandings(teamA: Standing, teamB: Standing) {
  return (
    getWinPercentage(teamB) - getWinPercentage(teamA) ||
    teamB.wins - teamA.wins ||
    teamA.losses - teamB.losses ||
    (teamB.pf - teamB.pa) - (teamA.pf - teamA.pa) ||
    teamB.pf - teamA.pf ||
    teamA.team.localeCompare(teamB.team)
  )
}

function findTeam(abbreviation: string): Team | undefined {
  return teams.find((team) => team.abbr === abbreviation)
}

function Standings() {
  const [conference, setConference] = useState<ConferenceFilter>('All')
  const [standings, setStandings] = useState<Standing[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadStandings() {
      try {
        const response = await fetch('/standings', { signal: controller.signal })
        if (!response.ok) {
          throw new Error(`Standings request failed (HTTP ${response.status}).`)
        }

        const payload: unknown = await response.json()
        if (!Array.isArray(payload)) {
          throw new Error('The standings API returned data in an unexpected format.')
        }

        const validStandings = payload.filter(isStanding)
        if (validStandings.length !== payload.length) {
          throw new Error('The standings API returned data in an unexpected format.')
        }

        setStandings(validStandings)
        setError(null)
      } catch (requestError) {
        if (controller.signal.aborted) return
        setError(
          requestError instanceof Error
            ? requestError.message
            : 'Could not load standings. Check that the API is running.',
        )
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }

    void loadStandings()
    return () => controller.abort()
  }, [])

  const visibleTeams = useMemo(
    () =>
      standings
        .filter((team) => conference === 'All' || team.team_conf === conference)
        .sort(compareStandings),
    [conference, standings],
  )

  return (
    <section className="standings-page">
      <header className="standings__header">
        <div>
          <p className="section-kicker">League table</p>
          <h1 className="standings__title">Current standings</h1>
          <p className="standings__description">
            Regular-season results, updated from the standings API.
          </p>
        </div>
        <div className="standings__season">CURRENT SEASON</div>
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
        <p className="standings__count" aria-live="polite">
          {loading ? 'Loading teams…' : `${visibleTeams.length} teams`}
        </p>
      </div>

      {error && <p className="standings__status" role="alert">{error}</p>}

      <div className="standings__table-wrap">
        <table className="standings__table">
          <caption className="sr-only">
            Current NFL regular-season standings ordered by win percentage
          </caption>
          <thead>
            <tr>
              <th scope="col">Rank</th>
              <th scope="col">Team</th>
              <th scope="col">Conference</th>
              <th scope="col">Division</th>
              <th scope="col">W</th>
              <th scope="col">L</th>
              <th scope="col">T</th>
              <th scope="col">Win %</th>
              <th scope="col">PF</th>
              <th scope="col">PA</th>
              <th scope="col">Diff</th>
              <th scope="col">Home</th>
              <th scope="col">Away</th>
              <th scope="col">Streak</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="standings__empty" colSpan={14}>Loading standings…</td></tr>
            ) : visibleTeams.length === 0 ? (
              <tr><td className="standings__empty" colSpan={14}>No standings available.</td></tr>
            ) : (
              visibleTeams.map((standing, index) => {
                const team = findTeam(standing.team)
                const pointDifferential = standing.pf - standing.pa

                return (
                  <tr key={standing.team} className={index === 0 ? 'is-leader' : undefined}>
                    <td className="standings__rank">{String(index + 1).padStart(2, '0')}</td>
                    <td className="standings__team">
                      <div className="standings__team-info">
                        {team && <TeamCrest team={team} size="sm" />}
                        <span>
                          <strong>{standing.team_name}</strong>
                          <small>{standing.team}</small>
                        </span>
                      </div>
                    </td>
                    <td>{standing.team_conf}</td>
                    <td>{standing.team_division}</td>
                    <td className="standings__wins">{standing.wins}</td>
                    <td>{standing.losses}</td>
                    <td>{standing.ties}</td>
                    <td>{standing.winning_percent.toFixed(3)}</td>
                    <td>{standing.pf}</td>
                    <td>{standing.pa}</td>
                    <td>{pointDifferential > 0 ? `+${pointDifferential}` : pointDifferential}</td>
                    <td>{standing.home_record ?? '—'}</td>
                    <td>{standing.away_record ?? '—'}</td>
                    <td>{standing.streak ?? '—'}</td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      <p className="standings__disclaimer">
        Teams are ordered by win percentage, then wins, fewer losses, point differential,
        and points scored. Head-to-head records are not available for official NFL tiebreakers.
      </p>
    </section>
  )
}

export default Standings
