import { useEffect, useState } from 'react'

interface PastGame {
  game_id: string
  week: number
  gameday: string
  away_team: string
  home_team: string
}

interface GameState {
  game_seconds_remaining: number
  half_seconds_remaining: number
  down: number
  ydstogo: number
  yardline_100: number
  score_differential: number
  posteam_timeouts_remaining: number
  defteam_timeouts_remaining: number
  posteam_is_home: boolean
}

interface PastPlay {
  play_id: number
  quarter: number
  clock: string
  away_score: number
  home_score: number
  state: GameState
}

const playLabels = {
  run: 'Run',
  pass: 'Pass',
  punt: 'Punt',
  field_goal: 'Field goal',
}
type Prediction = Partial<Record<keyof typeof playLabels, number>>

type Request<T> = { status: 'loading' } | { status: 'error' } | { status: 'success'; data: T }

function useReplayRequest<T>(url: string, state?: GameState): Request<T> {
  const [result, setResult] = useState<Request<T>>({ status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    const init: RequestInit = { signal: controller.signal }
    if (state) {
      init.method = 'POST'
      init.headers = { 'Content-Type': 'application/json' }
      init.body = JSON.stringify(state)
    }

    async function load() {
      try {
        const response = await fetch(url, init)
        if (!response.ok) throw new Error(`Request failed (${response.status})`)
        const data: T = await response.json()
        if (!controller.signal.aborted) setResult({ status: 'success', data })
      } catch {
        if (!controller.signal.aborted) setResult({ status: 'error' })
      }
    }

    void load()
    return () => controller.abort()
  }, [url, state])

  return result
}

function PlayPrediction({ state, offense }: { state: GameState; offense: string }) {
  const result = useReplayRequest<Prediction>('/predict', state)
  if (result.status === 'loading') return <p role="status">Calculating win probabilities…</p>
  if (result.status === 'error') return <p role="alert">Could not calculate win probabilities for this play.</p>

  const percent = new Intl.NumberFormat(undefined, { style: 'percent', maximumFractionDigits: 1 })
  return (
    <>
      <h4>{offense} win probability by next play call</h4>
      <dl className="replay__predictions">
        {(Object.keys(playLabels) as (keyof Prediction)[]).map((type) => {
          const probability = result.data[type]
          return probability !== undefined && (
            <div key={type}>
              <dt>{playLabels[type]}</dt>
              <dd>{percent.format(probability)}</dd>
            </div>
          )
        })}
      </dl>
    </>
  )
}

function GameReplay({ game }: { game: PastGame }) {
  const result = useReplayRequest<PastPlay[]>(`/past_games/${game.game_id}/plays`)
  const [index, setIndex] = useState(0)
  if (result.status === 'loading') return <p role="status">Loading recorded plays…</p>
  if (result.status === 'error') return <p role="alert">Could not load plays for this game.</p>
  const plays = result.data
  const play = plays[index]
  if (!play) return <p role="status">Play-by-play data is unavailable for this game. Recent games may still be processing.</p>

  const { state } = play
  const offense = state.posteam_is_home ? game.home_team : game.away_team
  const defense = state.posteam_is_home ? game.away_team : game.home_team
  const yardline = state.yardline_100 > 50
    ? `${offense} ${100 - state.yardline_100}`
    : state.yardline_100 < 50 ? `${defense} ${state.yardline_100}` : 'midfield'

  return (
    <div className="replay__play">
      <div className="replay__controls">
        <button type="button" className="btn btn--ghost" disabled={index === 0} onClick={() => setIndex(index - 1)}>
          Previous play
        </button>
        <span aria-live="polite">Play {index + 1} of {plays.length}</span>
        <button type="button" className="btn btn--ghost" disabled={index === plays.length - 1} onClick={() => setIndex(index + 1)}>
          Next play
        </button>
      </div>
      <div aria-live="polite" className="replay__situation">
        <h3>{game.away_team} {play.away_score} · {game.home_team} {play.home_score}</h3>
        <p>{play.quarter <= 4 ? `Q${play.quarter}` : `OT ${play.quarter - 4}`} · {play.clock}</p>
        <p>{offense} ball · {['', '1st', '2nd', '3rd', '4th'][state.down]} &amp; {state.ydstogo} · Ball on {yardline}</p>
      </div>
      <PlayPrediction key={play.play_id} state={state} offense={offense} />
    </div>
  )
}

function SeasonGames({ season }: { season: number }) {
  const result = useReplayRequest<PastGame[]>(`/past_games?season=${season}`)
  const [selectedWeek, setSelectedWeek] = useState<number>()
  const [gameId, setGameId] = useState('')
  if (result.status === 'loading') return <p role="status">Loading completed games…</p>
  if (result.status === 'error') return <p role="alert">Could not load completed games for this season.</p>
  if (!result.data.length) return <p role="status">No completed games are available for this season.</p>

  const weeks = [...new Set(result.data.map((game) => game.week))]
  const week = selectedWeek ?? weeks[0]
  const games = result.data.filter((game) => game.week === week)
  const game = games.find((item) => item.game_id === gameId)
  return (
    <>
      <div className="replay__filters">
        <label>
          Week
          <select value={week} onChange={(event) => {
            setSelectedWeek(Number(event.target.value))
            setGameId('')
          }}>
            {weeks.map((number) => <option key={number} value={number}>Week {number}</option>)}
          </select>
        </label>
        <label>
          Matchup
          <select value={gameId} onChange={(event) => setGameId(event.target.value)}>
            <option value="">Choose a game</option>
            {games.map((item) => (
              <option key={item.game_id} value={item.game_id}>
                {item.away_team} at {item.home_team} · {item.gameday}
              </option>
            ))}
          </select>
        </label>
      </div>
      {game && <GameReplay key={game.game_id} game={game} />}
    </>
  )
}

const now = new Date()
const latestSeason = now.getFullYear() - (now.getMonth() < 8 ? 1 : 0)
const seasons = Array.from({ length: latestSeason - 1999 + 1 }, (_, index) => latestSeason - index)

export default function PastGameReplay() {
  const [season, setSeason] = useState(latestSeason)

  return (
    <section className="replay" aria-labelledby="past-games-title" id="past-games">
      <h2 className="section-title" id="past-games-title">Past games</h2>
      <p>Replay a completed game and compare win probability estimates by play call.</p>
      <label>
        Season
        <select value={season} onChange={(event) => setSeason(Number(event.target.value))}>
          {seasons.map((year) => <option key={year} value={year}>{year}</option>)}
        </select>
      </label>
      <SeasonGames key={season} season={season} />
    </section>
  )
}
