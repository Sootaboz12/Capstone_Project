import { useEffect, useMemo, useState } from 'react'
import { getTeam } from '../data/teams'
import TeamCrest from './Teamcrest'
import type { LogoMap } from '../hooks/useNFLlogos'

interface TrendingCarouselProps {
  logos: LogoMap
}

// Placeholder trending slate — five matchups getting the most searches today.
// Wire this to a real "trending" feed later.
const TRENDING = [
  { home: 'kc', away: 'buf', label: 'Sunday Night', split: 58, searches: '128K searches' },
  { home: 'phi', away: 'dal', label: 'NFC East rivalry', split: 52, searches: '96K searches' },
  { home: 'sf', away: 'sea', label: 'NFC West clash', split: 63, searches: '74K searches' },
  { home: 'det', away: 'gb', label: 'NFC North showdown', split: 55, searches: '61K searches' },
  { home: 'bal', away: 'cin', label: 'AFC North grudge match', split: 61, searches: '58K searches' },
]

const AUTOPLAY_MS = 4500

function TrendingCarousel({ logos }: TrendingCarouselProps) {
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)

  const slides = useMemo(
    () => TRENDING.map((g) => ({ ...g, homeTeam: getTeam(g.home)!, awayTeam: getTeam(g.away)! })),
    [],
  )

  useEffect(() => {
    if (paused) return
    const timer = window.setInterval(() => {
      setIndex((i) => (i + 1) % slides.length)
    }, AUTOPLAY_MS)
    return () => window.clearInterval(timer)
  }, [paused, slides.length])

  const goTo = (i: number) => setIndex((i + slides.length) % slides.length)
  const current = slides[index]

  return (
    <div
      className="trending"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <span className="trending__watermark" aria-hidden="true">
        TRENDING
      </span>

      <div className="trending__stage">
        <button
          type="button"
          className="trending__arrow trending__arrow--prev"
          aria-label="Previous matchup"
          onClick={() => goTo(index - 1)}
        >
          ‹
        </button>

        <article className="trending__card" key={index}>
          <p className="trending__label">{current.label} · {current.searches}</p>

          <div className="trending__matchup">
            <div className="trending__side">
              <TeamCrest team={current.awayTeam} size="lg" logoUrl={logos[current.awayTeam.id]} />
              <span>{current.awayTeam.city} {current.awayTeam.name}</span>
            </div>
            <span className="trending__at">@</span>
            <div className="trending__side">
              <TeamCrest team={current.homeTeam} size="lg" logoUrl={logos[current.homeTeam.id]} />
              <span>{current.homeTeam.city} {current.homeTeam.name}</span>
            </div>
          </div>

          <div className="trending__split">
            <div className="trending__bar">
              <span style={{ width: `${current.split}%` }} />
            </div>
            <p>
              {current.homeTeam.abbr} favored <strong>{current.split}%</strong> — see the full breakdown on the predictor page
            </p>
          </div>
        </article>

        <button
          type="button"
          className="trending__arrow trending__arrow--next"
          aria-label="Next matchup"
          onClick={() => goTo(index + 1)}
        >
          ›
        </button>
      </div>

      <div className="trending__meta">
        <div className="trending__dots" role="tablist" aria-label="Trending matchups">
          {slides.map((s, i) => (
            <button
              key={`${s.home}-${s.away}`}
              type="button"
              role="tab"
              aria-selected={i === index}
              aria-label={`Show matchup ${i + 1}`}
              className={i === index ? 'is-active' : ''}
              onClick={() => goTo(i)}
            />
          ))}
        </div>
        <span className="trending__count">0{index + 1} / 0{slides.length}</span>
      </div>
    </div>
  )
}

export default TrendingCarousel