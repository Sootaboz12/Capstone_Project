import { useState } from 'react'
import { teams } from '../data/teams'
import TeamCrest from './Teamcrest'
import type { LogoMap } from '../hooks/useNFLlogos'

interface TeamGridProps {
  logos: LogoMap
}

function TeamGrid({ logos }: TeamGridProps) {
  const [openId, setOpenId] = useState<string | null>(null)

  const handleToggle = (id: string) => {
    setOpenId((current) => (current === id ? null : id))
  }

  const openTeam = teams.find((t) => t.id === openId) ?? null

  return (
    <div className="team-grid">
      <div className="team-grid__cells">
        {teams.map((team) => (
          <button
            type="button"
            key={team.id}
            className={`team-grid__cell${team.id === openId ? ' is-open' : ''}`}
            onClick={() => handleToggle(team.id)}
            aria-expanded={team.id === openId}
          >
            <TeamCrest team={team} size="md" logoUrl={logos[team.id]} />
            <span>{team.abbr}</span>
          </button>
        ))}
      </div>

      <div className={`team-grid__cascade${openTeam ? ' is-open' : ''}`}>
        <div className="team-grid__cascade-inner">
          {openTeam && (
            <div className="team-grid__detail">
              <TeamCrest team={openTeam} size="lg" logoUrl={logos[openTeam.id]} />
              <div className="team-grid__detail-copy">
                <p className="team-grid__detail-kicker">
                  {openTeam.conference} {openTeam.division} · {openTeam.stadium}
                </p>
                <h3>{openTeam.city} {openTeam.name}</h3>
                <p className="team-grid__detail-home">Home: {openTeam.city}</p>
                <p className="team-grid__detail-blurb">{openTeam.blurb}</p>
              </div>
              <button
                type="button"
                className="team-grid__close"
                onClick={() => setOpenId(null)}
                aria-label="Close team details"
              >
                ×
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TeamGrid