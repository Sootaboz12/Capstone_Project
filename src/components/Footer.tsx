import { Link } from 'react-router-dom'

function Footer() {
  return (
    <footer className="footer">
      <div className="footer__row">
        <span className="footer__brand">
          The Spread<span>.</span>
        </span>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/predictor">Predictor</Link>
          <Link to="/standings">Standings</Link>
          <Link to="/about">About</Link>
        </nav>
      </div>
      <p className="footer__fine">
        The matchup predictor uses mock team ratings. Past game replay shows model estimates.
      </p>
    </footer>
  )
}

export default Footer