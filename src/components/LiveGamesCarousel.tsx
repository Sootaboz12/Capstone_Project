import { useEffect, useState } from 'react'
import TeamCrest from './Teamcrest'
import { teams, type Team } from '../data/teams'

interface LiveTeam {
  abbreviation: string
  name: string
}

interface LiveGame {
  id: string
  name: string
  away_team: LiveTeam
  home_team: LiveTeam
}

const REFRESH_MS = 30_000
const AUTOPLAY_MS = 4_500
const ESPN_ABBR_ALIASES: Record<string, string> = { JAC: 'JAX', WSH: 'WAS' }

function isLiveTeam(value: unknown): value is LiveTeam {
  if (typeof value !== 'object' || value === null) return false

  const team = value as Record<string, unknown>
  return (
    typeof team.abbreviation === 'string' &&
    typeof team.name === 'string' &&
    team.name.length > 0
  )
}

function isLiveGame(value: unknown): value is LiveGame {
  if (typeof value !== 'object' || value === null) return false

  const game = value as Record<string, unknown>
  return (
    typeof game.id === 'string' &&
    game.id.length > 0 &&
    typeof game.name === 'string' &&
    game.name.length > 0 &&
    isLiveTeam(game.away_team) &&
    isLiveTeam(game.home_team)
  )
}

function findTeam(abbreviation: string): Team | undefined {
  const normalizedAbbreviation = ESPN_ABBR_ALIASES[abbreviation] ?? abbreviation
  return teams.find((team) => team.abbr === normalizedAbbreviation)
}

function LiveGamesCarousel() {
  const [games, setGames] = useState<LiveGame[]>([])
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadLiveGames() {
      try {
        const response = await fetch('/live_games', { signal: controller.signal })
        if (!response.ok) {
          throw new Error(`Live games request failed (HTTP ${response.status}).`)
        }

        const payload: unknown = await response.json()
        if (!Array.isArray(payload)) {
          throw new Error('The live games API returned data in an unexpected format.')
        }

        const validGames = payload.filter(isLiveGame)
        if (validGames.length !== payload.length) {
          throw new Error('The live games API returned data in an unexpected format.')
        }

        setGames(validGames)
        setIndex((currentIndex) => validGames.length ? currentIndex % validGames.length : 0)
        setError(null)
      } catch (requestError) {
        if (controller.signal.aborted) return
        setError(
          requestError instanceof Error
            ? requestError.message
            : 'Could not load live games. Check that the API is running.',
        )
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }

    void loadLiveGames()
    const timer = window.setInterval(() => void loadLiveGames(), REFRESH_MS)

    return () => {
      controller.abort()
      window.clearInterval(timer)
    }
  }, [])

  useEffect(() => {
    if (paused || games.length < 2) return
    const timer = window.setInterval(() => {
      setIndex((currentIndex) => (currentIndex + 1) % games.length)
    }, AUTOPLAY_MS)
    return () => window.clearInterval(timer)
  }, [games.length, paused])

  const goTo = (i: number) => setIndex((i + games.length) % games.length)
  const current = games[index]
  const awayTeam = current ? findTeam(current.away_team.abbreviation) : undefined
  const homeTeam = current ? findTeam(current.home_team.abbreviation) : undefined

  return (
    <div
      className="trending"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <span className="trending__watermark" aria-hidden="true">
        LIVE
      </span>

      <div className="trending__stage">
        {games.length > 1 && (
          <button
            type="button"
            className="trending__arrow trending__arrow--prev"
            aria-label="Previous live game"
            onClick={() => goTo(index - 1)}
          >
            ‹
          </button>
        )}

        {loading ? (
          <p className="trending__card" role="status">Loading live games…</p>
        ) : current ? (
          <article className="trending__card" key={current.id}>
            <p className="trending__label">
              <span className="trending__live-indicator" aria-hidden="true" />
              Live now
            </p>
            <div
              className="trending__matchup"
              role="group"
              aria-label={`${current.away_team.name} versus ${current.home_team.name}`}
            >
              <div className="trending__side">
                {awayTeam ? (
                  <TeamCrest team={awayTeam} size="lg" />
                ) : (
                  <span className="trending__team-abbr">{current.away_team.abbreviation}</span>
                )}
                <span>{current.away_team.name}</span>
              </div>
              <span className="trending__vs">VS</span>
              <div className="trending__side">
                {homeTeam ? (
                  <TeamCrest team={homeTeam} size="lg" />
                ) : (
                  <span className="trending__team-abbr">{current.home_team.abbreviation}</span>
                )}
                <span>{current.home_team.name}</span>
              </div>
            </div>
          </article>
        ) : (
          <p className="trending__card" role={error ? 'alert' : 'status'}>
            {error ? 'Live games are temporarily unavailable.' : 'No games are live right now.'}
          </p>
        )}

        {games.length > 1 && (
          <button
            type="button"
            className="trending__arrow trending__arrow--next"
            aria-label="Next live game"
            onClick={() => goTo(index + 1)}
          >
            ›
          </button>
        )}
      </div>

      {error && games.length > 0 && (
        <p className="trending__error" role="alert">
          Could not refresh live games: {error} Showing the most recently loaded games.
        </p>
      )}

      {games.length > 1 && (
        <div className="trending__meta">
          <div className="trending__dots" role="tablist" aria-label="Live games">
            {games.map((game, i) => (
              <button
                key={game.id}
                type="button"
                role="tab"
                aria-selected={i === index}
                aria-label={`Show live game ${i + 1}: ${game.name}`}
                className={i === index ? 'is-active' : ''}
                onClick={() => goTo(i)}
              />
            ))}
          </div>
          <span className="trending__count">{String(index + 1).padStart(2, '0')} / {String(games.length).padStart(2, '0')}</span>
        </div>
      )}
    </div>
  )
}

export default LiveGamesCarousel
