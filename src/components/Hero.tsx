import { useEffect, useState } from 'react'

interface HeroProps {
  onNav: (id: string) => void
}

// Placeholder headline probability — the one animated "scoreboard" moment on
// the page. In the real app this would resolve to this week's marquee matchup.
const DEMO_TARGET = 73

function Hero({ onNav }: HeroProps) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    const duration = 1400
    const start = performance.now()
    let frame: number
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(eased * DEMO_TARGET))
      if (progress < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [])

  return (
    <section className="hero" id="top">
      <div className="hero__yardlines" aria-hidden="true" />

      <div className="hero__content">
        <p className="hero__kicker">Week 4 · Odds refresh every Tuesday</p>
        <h1 className="hero__headline">
          Every Sunday
          <br />
          comes down to a number.
        </h1>
        <p className="hero__sub">
          Pull real team splits, line up any two franchises, and get a
          straightforward win probability — no jargon, just the number and
          why we landed on it.
        </p>

        <div className="hero__actions">
          <button type="button" className="btn btn--primary" onClick={() => onNav('predictor')}>
            Predict a matchup
          </button>
          <button type="button" className="btn btn--ghost" onClick={() => onNav('teams')}>
            Browse team stats
          </button>
        </div>
      </div>

      <div className="hero__scoreboard" role="img" aria-label="Sample win probability of 73 percent">
        <span className="hero__scoreboard-label">Sample matchup edge</span>
        <span className="hero__scoreboard-number">{value}%</span>
        <span className="hero__scoreboard-caption">favorite to cover, current line</span>
      </div>
    </section>
  )
}

export default Hero