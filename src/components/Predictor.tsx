import { useState } from 'react'
import type { CSSProperties } from 'react'
import { teams, getTeam } from '../data/teams'
import TeamCrest from './Teamcrest'

interface Result {
  teamAPct: number
  teamBPct: number
  upset: boolean
  factors: string[]
}

// Placeholder model: leans on the mock offense/defense ratings plus a little
// noise. Replace with a real prediction service call.
function runPlaceholderModel(aId: string, bId: string): Result {
  const a = getTeam(aId)!
  const b = getTeam(bId)!
  const aScore = a.stats.offenseRating - b.stats.defenseRating + a.stats.turnoverMargin
  const bScore = b.stats.offenseRating - a.stats.defenseRating + b.stats.turnoverMargin
  const diff = aScore - bScore
  const raw = 50 + diff * 0.9
  const teamAPct = Math.min(92, Math.max(8, Math.round(raw)))
  const teamBPct = 100 - teamAPct

  const underdogIsA = a.stats.powerRank > b.stats.powerRank
  const upset = (underdogIsA && teamAPct > 50) || (!underdogIsA && teamBPct > 50)

  const favorite = teamAPct >= teamBPct ? a : b
  const factors = [
    `${favorite.abbr} offense rated ${favorite.stats.offenseRating} vs. opposing defense`,
    `Turnover margin edge: ${favorite.stats.turnoverMargin > 0 ? '+' : ''}${favorite.stats.turnoverMargin}`,
    `Power rank #${favorite.stats.powerRank} entering the week`,
  ]

  return { teamAPct, teamBPct, upset, factors }
}

function Predictor() {
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
    // Placeholder "compute" delay so the reveal has somewhere to land.
    window.setTimeout(() => {
      setResult(runPlaceholderModel(teamAId, teamBId))
      setLoading(false)
    }, 650)
  }

  return (
    <section className="predictor" id="predictor">
      <p className="section-kicker">Head to head</p>
      <h2 className="section-title">Put two teams on the field</h2>
      <p className="predictor__sub">
        Pick any matchup, current season or hypothetical, and get a win
        probability built from each team's placeholder splits.
      </p>

      <div className="predictor__board">
        <div className="predictor__side">
          <TeamCrest team={teamA} size="lg" />
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
          <TeamCrest team={teamB} size="lg" />
          <label className="sr-only" htmlFor="teamB">Team B</label>
          <select id="teamB" value={teamBId} onChange={(e) => setTeamBId(e.target.value)}>
            {teams.map((t) => (
              <option key={t.id} value={t.id}>{t.city} {t.name}</option>
            ))}
          </select>
        </div>
      </div>

      {result && (
        <div className="predictor__result">
          {result.upset && <p className="predictor__upset">Upset alert</p>}

          <div className="predictor__split">
            <div
              className="predictor__split-bar"
              style={
                {
                  '--a': result.teamAPct,
                  '--colorA': teamA.colors.primary,
                  '--colorB': teamB.colors.primary,
                } as CSSProperties
              }
            >
              <span className="predictor__split-a">{teamA.abbr} {result.teamAPct}%</span>
              <span className="predictor__split-b">{teamB.abbr} {result.teamBPct}%</span>
            </div>
          </div>

          <ul className="predictor__factors">
            {result.factors.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          <p className="predictor__disclaimer">
            Built on placeholder ratings — for entertainment purposes only.
          </p>
        </div>
      )}
    </section>
  )
}

export default Predictor