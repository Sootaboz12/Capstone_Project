import { Link } from 'react-router-dom'
import TrendingCarousel from '../components/TrendingCarousel'
import TeamGrid from '../components/Teamgrid'
import { useNflLogos } from '../hooks/useNFLlogos'

function Landing() {
  const { logos } = useNflLogos()

  return (
    <>
      <section className="intro" id="top">
        <span className="intro__ghost" aria-hidden="true">SPREAD</span>
        <div className="intro__frame">
          <p className="intro__kicker">Week 4 · Odds refresh every Tuesday</p>
          <h1 className="intro__headline">
            Today's most <em>searched</em> matchups, ranked by the crowd.
          </h1>
          <p className="intro__sub">
            See what everyone's talking about before kickoff, then dig into
            any team's numbers or line up your own head-to-head.
          </p>
          <div className="intro__actions">
            <Link to="/predictor" className="btn btn--primary">Predict a matchup</Link>
            <a href="#teams" className="btn btn--ghost">Browse team stats</a>
          </div>
        </div>
      </section>

      <section className="section" id="trending">
        <p className="section-kicker">Trending today</p>
        <h2 className="section-title">Games everyone's picking</h2>
        <TrendingCarousel logos={logos} />
      </section>

      <section className="section" id="teams">
        <p className="section-kicker">Every franchise</p>
        <h2 className="section-title">Tap a team to see who they are</h2>
        <p className="section-sub">
          Crests, hometowns, and a quick line on each team's identity.
        </p>
        <TeamGrid logos={logos} />
      </section>
    </>
  )
}

export default Landing