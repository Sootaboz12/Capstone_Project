import { useState } from 'react'
import { teams, getTeam } from '../data/teams'
import TeamCrest from '../components/Teamcrest'
import WinDonut from '../components/Windonut'
import ComparisonBars from '../components/Comparisonbars'
import StatsTable from '../components/Statstable'
import { useNflLogos } from '../hooks/useNFLlogos'

interface Result {
  pctA: number
  pctB: number
  upset: boolean
}

// Placeholder model: leans on the mock offense/defense ratings. Replace with
// a real prediction service call once one exists.
function runPlaceholderModel(aId: string, bId: string): Result {
  const a = getTeam(aId)!
  const b = getTeam(bId)!
  const aScore = a.stats.offenseRating - b.stats.defenseRating + a.stats.turnoverMargin
  const bScore = b.stats.offenseRating - a.stats.defenseRating + b.stats.turnoverMargin
  const diff = aScore - bScore
  const raw = 50 + diff * 0.9
  const pctA = Math.min(92, Math.max(8, Math.round(raw)))
  const pctB = 100 - pctA

  const underdogIsA = a.stats.powerRank > b.stats.powerRank
  const upset = (underdogIsA && pctA > 50) || (!underdogIsA && pctB > 50)

  return { pctA, pctB, upset }
}

function MatchupPredictor() {
  const { logos } = useNflLogos()
  const [teamAId, setTeamAId] = useState(teams[0].id)
  const [teamBId, setTeamBId] = useState(teams[1].id)
  const [result, setResult] = useState<Result | null>(null)
  const [loading, setLoading] = useState(false)

  const teamA = getTeam(teamAId)!
  const teamB = getTeam(teamBId)!
  const invalid = teamAId === teamBId

  const handleRun = () => {
    if (invalid) return
    setLoading(true)
    setResult(null)
    window.setTimeout(() => {
      setResult(runPlaceholderModel(teamAId, teamBId))
      setLoading(false)
    }, 600)
  }

  return (
    <section className="predictor-page">
      <p className="section-kicker">Head to head</p>
      <h1 className="section-title">Put two teams on the field</h1>
      <p className="section-sub">
        Pick any matchup and get a win probability, a points breakdown, and
        the raw numbers behind it — built from each team's placeholder splits.
      </p>

      <div className="predictor__board">
        <div className="predictor__side">
          <TeamCrest team={teamA} size="lg" logoUrl={logos[teamA.id]} />
          <label className="sr-only" htmlFor="teamA">Team A</label>
          <select id="teamA" value={teamAId} onChange={(e) => setTeamAId(e.target.value)}>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>{t.city} {t.name}</option>
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
          <TeamCrest team={teamB} size="lg" logoUrl={logos[teamB.id]} />
          <label className="sr-only" htmlFor="teamB">Team B</label>
          <select id="teamB" value={teamBId} onChange={(e) => setTeamBId(e.target.value)}>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>{t.city} {t.name}</option>
            ))}
          </select>
        </div>
      </div>

      {result && (
        <div className="predictor-results">
          {result.upset && <p className="predictor__upset">Upset alert</p>}

          <div className="predictor-results__grid">
            <div className="chart-card chart-card--featured">
              <h3>Win chance</h3>
              <WinDonut teamA={teamA} teamB={teamB} pctA={result.pctA} pctB={result.pctB} />
            </div>

            <div className="chart-card">
              <h3>Team comparison</h3>
              <ComparisonBars
                teamA={teamA}
                teamB={teamB}
                metrics={[
                  { label: 'Offense rating', a: teamA.stats.offenseRating, b: teamB.stats.offenseRating },
                  { label: 'Defense rating', a: teamA.stats.defenseRating, b: teamB.stats.defenseRating },
                  { label: 'Points for', a: teamA.stats.pointsFor, b: teamB.stats.pointsFor },
                  { label: 'Points against', a: teamA.stats.pointsAgainst, b: teamB.stats.pointsAgainst },
                ]}
              />
            </div>

            <div className="chart-card chart-card--wide">
              <h3>Season numbers</h3>
              <StatsTable teamA={teamA} teamB={teamB} />
            </div>
          </div>

          <p className="predictor__disclaimer">
            Built on placeholder ratings — for entertainment purposes only.
          </p>
        </div>
      )}
    </section>
  )
}

export default MatchupPredictor