import { useState } from 'react'
import { teams, getTeam } from '../data/teams'
import { getMatchupPrediction, type MatchupPrediction } from '../libs/Predictions'
import ComparisonBars from './Comparisonbars'
import GameFlowChart from './GameFlowChart'
import StatsTable from './Statstable'
import TeamCrest from './Teamcrest'
import WinDonut from './Windonut'

function getCurrentSeason(): number {
  const now = new Date()
  return now.getMonth() >= 2 ? now.getFullYear() : now.getFullYear() - 1
}

function Predictor() {
  const currentSeason = getCurrentSeason()
  const [teamAId, setTeamAId] = useState(teams[0].id)
  const [teamBId, setTeamBId] = useState(teams[1].id)
  const [homeTeamId, setHomeTeamId] = useState(teams[0].id)
  const [season, setSeason] = useState(currentSeason)
  const [result, setResult] = useState<MatchupPrediction | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const teamA = getTeam(teamAId)!
  const teamB = getTeam(teamBId)!
  const homeTeamOptions = teamAId === teamBId ? [teamA] : [teamA, teamB]
  const invalid = teamAId === teamBId

  const handleRun = async () => {
    if (invalid) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const prediction = await getMatchupPrediction(teamA.abbr, teamB.abbr, season, getTeam(homeTeamId)!.abbr)
      setResult(prediction)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not load the matchup prediction.')
    } finally {
      setLoading(false)
    }
  }

  const clearResult = () => {
    setResult(null)
    setError(null)
  }

  return (
    <section className="predictor-page" id="predictor">
      <p className="section-kicker">Head to head</p>
      <h1 className="section-title">Put two teams on the field</h1>
      <p className="section-sub">
        Compare real regular-season results and scoring to estimate each team&apos;s
        chance to win. Set the season and home team for your matchup.
      </p>

      <div className="predictor__board">
        <div className="predictor__side">
          <TeamCrest team={teamA} size="lg" />
          <label className="sr-only" htmlFor="teamA">Team A</label>
          <select
            id="teamA"
            value={teamAId}
            disabled={loading}
            onChange={(event) => {
              const nextTeamId = event.target.value
              setTeamAId(nextTeamId)
              setHomeTeamId((current) => current === teamBId ? current : nextTeamId)
              clearResult()
            }}
          >
            {teams.map((team) => (
              <option key={team.id} value={team.id}>{team.city} {team.name}</option>
            ))}
          </select>
        </div>

        <div className="predictor__center">
          <span className="predictor__vs">VS</span>
          <button
            type="button"
            className="btn btn--primary"
            onClick={handleRun}
            disabled={invalid || loading}
          >
            {loading ? 'Crunching…' : 'Run prediction'}
          </button>
          {invalid && <p className="predictor__warning">Choose two different teams</p>}
        </div>

        <div className="predictor__side">
          <TeamCrest team={teamB} size="lg" />
          <label className="sr-only" htmlFor="teamB">Team B</label>
          <select
            id="teamB"
            value={teamBId}
            disabled={loading}
            onChange={(event) => {
              const nextTeamId = event.target.value
              setTeamBId(nextTeamId)
              setHomeTeamId((current) => current === teamAId ? current : nextTeamId)
              clearResult()
            }}
          >
            {teams.map((team) => (
              <option key={team.id} value={team.id}>{team.city} {team.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="predictor-options">
        <label>
          Home team
          <select
            value={homeTeamId}
            disabled={loading}
            onChange={(event) => {
              setHomeTeamId(event.target.value)
              clearResult()
            }}
          >
            {homeTeamOptions.map((team) => (
              <option key={team.id} value={team.id}>{team.city} {team.name}</option>
            ))}
          </select>
        </label>
        <label>
          Season
          <select
            value={season}
            disabled={loading}
            onChange={(event) => {
              setSeason(Number(event.target.value))
              clearResult()
            }}
          >
            {Array.from({ length: 5 }, (_, index) => currentSeason - index).map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="predictor__error" role="alert">{error}</p>}

      {result && (
        <div className="predictor-results">
          <div className="predictor-results__grid">
            <div className="chart-card chart-card--featured">
              <h3>{result.season} estimated win chance</h3>
              <WinDonut
                teamA={teamA}
                teamB={teamB}
                pctA={result.probability_a}
                pctB={result.probability_b}
              />
              <p className="predictor-projection">
                Projected score: <strong>{teamA.abbr} {result.expected_points_a}</strong>
                {' '}&ndash;{' '}
                <strong>{result.expected_points_b} {teamB.abbr}</strong>
              </p>
              <p className="predictor-projection__context">
                {getTeam(homeTeamId)!.city} is home · based on {result.games_sampled} completed games
              </p>
              <p className="predictor-projection__context">
                Season home edge: {result.home_field_advantage > 0 ? '+' : ''}
                {result.home_field_advantage} pts · scoring-margin deviation: {result.margin_std_dev} pts
              </p>
            </div>

            <div className="chart-card">
              <h3>Season performance</h3>
              <ComparisonBars
                teamA={teamA}
                teamB={teamB}
                metrics={[
                  { label: 'Wins', a: result.team_a.wins, b: result.team_b.wins },
                  { label: 'Points scored / game', a: Number(result.team_a.points_for_per_game.toFixed(1)), b: Number(result.team_b.points_for_per_game.toFixed(1)) },
                  { label: 'Points allowed / game', a: Number(result.team_a.points_against_per_game.toFixed(1)), b: Number(result.team_b.points_against_per_game.toFixed(1)) },
                  { label: 'Win percentage', a: Number((result.team_a.win_pct * 100).toFixed(1)), b: Number((result.team_b.win_pct * 100).toFixed(1)), suffix: '%' },
                ]}
              />
            </div>

            <div className="chart-card">
              <h3>Projected game flow</h3>
              <GameFlowChart
                teamA={teamA}
                teamB={teamB}
                finalScoreA={result.expected_points_a}
                finalScoreB={result.expected_points_b}
              />
            </div>

            <div className="chart-card chart-card--wide">
              <h3>Season numbers</h3>
              <StatsTable
                teamA={teamA}
                teamB={teamB}
                statsA={result.team_a}
                statsB={result.team_b}
              />
            </div>
          </div>

          <p className="predictor__disclaimer">
            Estimates use the teams&apos; completed regular-season scoring averages,
            season home-field advantage, and observed scoring-margin variation.
            They are statistical estimates, not guarantees or live in-game odds.
          </p>
        </div>
      )}
    </section>
  )
}

export default Predictor
