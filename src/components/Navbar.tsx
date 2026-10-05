import { useState } from 'react'
import { NavLink } from 'react-router-dom'

const LINKS = [
  { to: '/', label: 'Home' },
  { to: '/predictor', label: 'Predictor' },
  { to: '/about', label: 'About' },
]

function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <header className="navbar">
      <NavLink to="/" className="navbar__brand" onClick={() => setOpen(false)}>
        <svg viewBox="0 0 40 40" className="navbar__mark" aria-hidden="true">
          <ellipse cx="20" cy="20" rx="17" ry="12" className="navbar__mark-fill" />
          <path d="M6 20 H34 M14 15 V25 M20 13 V27 M26 15 V25" className="navbar__mark-lace" />
        </svg>
        <span className="navbar__wordmark">
          The Spread<span className="navbar__dot">.</span>
        </span>
      </NavLink>

      <button
        type="button"
        className="navbar__toggle"
        aria-label="Toggle navigation menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span />
        <span />
        <span />
      </button>

      <nav className={`navbar__links${open ? ' is-open' : ''}`}>
        {LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            onClick={() => setOpen(false)}
            className={({ isActive }) => (isActive ? 'is-active' : '')}
          >
            {link.label}
          </NavLink>
        ))}
        <NavLink to="/predictor" className="navbar__cta" onClick={() => setOpen(false)}>
          Run a matchup
        </NavLink>
      </nav>
    </header>
  )
}

export default Navbar