import { useState } from 'react'
import { Link } from 'react-router-dom'
import LiveGamesCarousel from '../components/LiveGamesCarousel'
import PastGameReplay from '../components/PastGameReplay'
import TeamGrid from '../components/Teamgrid'
import { useNflLogos } from '../hooks/useNFLlogos'
import stadiumImage from '../app/assets/sunday-brief-stadium.webp'
import './SundayBrief.css'

const matchups = [
  { title: 'Bills vs. Dolphins', firstTeam: 'BUF', secondTeam: 'MIA', firstChance: 61 },
  { title: 'Ravens vs. Eagles', firstTeam: 'BAL', secondTeam: 'PHI', firstChance: 54 },
  { title: 'Bills vs. Ravens', firstTeam: 'BUF', secondTeam: 'BAL', firstChance: 46 },
]

function Landing() {
  const { logos } = useNflLogos()
  const [matchupIndex, setMatchupIndex] = useState(0)
  const { title, firstTeam, secondTeam, firstChance } = matchups[matchupIndex]
  const secondChance = 100 - firstChance

  return (
    <div className="sunday-brief" id="top">
      <header className="sunday-brief__masthead">
        <h1>The Sunday Brief</h1>
        <p>Explore NFL matchups</p>
      </header>

      <div className="sunday-brief__edition">
        <article className="sunday-brief__lead" aria-labelledby="featured-matchup">
          <img className="sunday-brief__stadium" src={stadiumImage} alt="" fetchPriority="high" />
          <div aria-live="polite" aria-atomic="true">
            <p className="sunday-brief__eyebrow">{matchupIndex === 0 ? 'Featured matchup' : 'Selected matchup'}</p>
            <h2 id="featured-matchup">{title}</h2>
            <div className="sunday-brief__chances">
              <span className="sr-only">Win chances</span>
              <span>{firstTeam} {firstChance}%</span>
              <span className="sunday-brief__bar" aria-hidden="true">
                <span style={{ width: `${firstChance}%` }} />
              </span>
              <span>{secondTeam} {secondChance}%</span>
            </div>
          </div>
          <p className="sunday-brief__eyebrow">Illustrative demo data</p>
        </article>

        <aside className="sunday-brief__sidebar" aria-labelledby="matchup-list">
          <h2 id="matchup-list">Explore a matchup</h2>
          <ul>
            {matchups.map((matchup, index) => (
              <li key={matchup.title}>
                <button
                  type="button"
                  aria-pressed={matchupIndex === index}
                  onClick={() => setMatchupIndex(index)}
                >
                  {matchup.title}<span aria-hidden="true">{matchupIndex === index ? '•' : '→'}</span>
                </button>
              </li>
            ))}
          </ul>
          <section className="sunday-brief__live" id="trending" aria-labelledby="live-games">
            <h3 id="live-games">Live games</h3>
            <LiveGamesCarousel />
          </section>
          <div className="sunday-brief__links">
            <Link to="/predictor">Predict a matchup <span aria-hidden="true">→</span></Link>
            <a href="#teams">Browse teams <span aria-hidden="true">↓</span></a>
          </div>
        </aside>
      </div>

      <section className="sunday-brief__teams" id="teams" aria-labelledby="team-directory">
        <h2 id="team-directory">Team directory</h2>
        <TeamGrid logos={logos} />
      </section>
    </div>
  )
}

export default Landing
