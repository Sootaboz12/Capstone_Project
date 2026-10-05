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
          <Link to="/about">About</Link>
        </nav>
      </div>
      <p className="footer__fine">
        Placeholder framework — statistics and predictions shown are mock
        data for demonstration only, not real sportsbook odds.
      </p>
    </footer>
  )
}

export default Footer