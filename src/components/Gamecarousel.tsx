import { useRef } from 'react'
import type { CSSProperties } from 'react'
import { teams, getTeam } from '../data/teams'
import TeamCrest from './Teamcrest'

// Placeholder slate — pairs teams up and invents a kickoff slot + preview
// split. Wire this up to a real schedule + model output later.
const SLATE = [
  { home: 'kc', away: 'buf', day: 'Sun', time: '4:25 PM', split: 58, featured: true },
  { home: 'phi', away: 'dal', day: 'Sun', time: '8:20 PM', split: 52 },
  { home: 'sf', away: 'sea', day: 'Sun', time: '1:00 PM', split: 63 },
  { home: 'det', away: 'gb', day: 'Sun', time: '1:00 PM', split: 55 },
  { home: 'bal', away: 'cin', day: 'Sun', time: '1:00 PM', split: 61 },
  { home: 'mia', away: 'nyj', day: 'Mon', time: '8:15 PM', split: 57 },
].map((g) => ({ ...g, homeTeam: getTeam(g.home)!, awayTeam: getTeam(g.away)! }))

function GameCarousel() {
  const trackRef = useRef<HTMLDivElement>(null)

  const scrollByCard = (dir: 1 | -1) => {
    trackRef.current?.scrollBy({ left: dir * 320, behavior: 'smooth' })
  }

  return (
    <section className="slate" id="slate">
      <div className="slate__head">
        <div>
          <p className="section-kicker">This week</p>
          <h2 className="section-title">Slate at a glance</h2>
        </div>
        <div className="slate__arrows">
          <button type="button" aria-label="Scroll left" onClick={() => scrollByCard(-1)}>‹</button>
          <button type="button" aria-label="Scroll right" onClick={() => scrollByCard(1)}>›</button>
        </div>
      </div>

      <div className="slate__track" ref={trackRef}>
        {SLATE.map((g, i) => (
          <article
            className={`game-card${g.featured ? ' game-card--featured' : ''}`}
            key={`${g.home}-${g.away}-${i}`}
            style={
              {
                '--from': g.awayTeam.colors.primary,
                '--to': g.homeTeam.colors.primary,
              } as CSSProperties
            }
          >
            <div className="game-card__glow" aria-hidden="true" />
            <p className="game-card__slot">{g.day} · {g.time}</p>

            <div className="game-card__matchup">
              <div className="game-card__side">
                <TeamCrest team={g.awayTeam} size="md" />
                <span>{g.awayTeam.abbr}</span>
              </div>
              <span className="game-card__at">@</span>
              <div className="game-card__side">
                <TeamCrest team={g.homeTeam} size="md" />
                <span>{g.homeTeam.abbr}</span>
              </div>
            </div>

            <div className="game-card__split">
              <div className="game-card__bar">
                <span style={{ width: `${g.split}%` }} />
              </div>
              <p>
                {g.homeTeam.abbr} favored <strong>{g.split}%</strong>
              </p>
            </div>
          </article>
        ))}
        <div className="game-card game-card--more">
          <p>{teams.length - 12} more games this week</p>
          <span>Full slate placeholder</span>
        </div>
      </div>
    </section>
  )
}

export default GameCarousel