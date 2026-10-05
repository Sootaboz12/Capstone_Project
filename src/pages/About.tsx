import { Link } from 'react-router-dom'

function About() {
  return (
    <section className="about">
      <p className="section-kicker">About</p>
      <h1 className="section-title">A simple home for game-day curiosity</h1>

      <p className="about__lede">
        The Spread pulls NFL team stats together in one place so you can see
        who's trending, browse every franchise, and line up any two teams to
        see who's favored — no spreadsheets required.
      </p>

      <div className="about__grid">
        <div className="about__card">
          <h2>Today's picks</h2>
          <p>The landing page surfaces the matchups people are searching for most, updated regularly.</p>
        </div>
        <div className="about__card">
          <h2>Every team, one tap away</h2>
          <p>Click any crest to see a team's hometown and a quick line on who they are.</p>
        </div>
        <div className="about__card">
          <h2>Head-to-head predictor</h2>
          <p>Pick two teams and get a win-probability wheel, a stat comparison, and the raw numbers behind it.</p>
        </div>
      </div>

      <p className="about__note">
        This is a framework — the stats and predictions you see are placeholder
        data standing in for a future live feed and model. Nothing here is
        betting advice.
      </p>

      <Link to="/predictor" className="btn btn--primary">Try the predictor</Link>
    </section>
  )
}

export default About