import type { Team } from '../data/teams'

interface GameFlowChartProps {
  teamA: Team
  teamB: Team
  finalScoreA: number
  finalScoreB: number
}

interface MinuteScore {
  minute: number
  points: number
}

const CHART_WIDTH = 420
const CHART_HEIGHT = 250
const PLOT_LEFT = 44
const PLOT_RIGHT = 12
const PLOT_TOP = 14
const PLOT_BOTTOM = 38
const MINUTES = 60

function buildMinuteScores(finalScore: number, phase: number): MinuteScore[] {
  const pace = Array.from({ length: MINUTES }, (_, minute) => (
    1
    + 0.2 * Math.sin((minute / MINUTES) * Math.PI * 4 + phase)
    + 0.08 * Math.sin((minute / MINUTES) * Math.PI * 8 + phase)
  ))
  const totalPace = pace.reduce((total, value) => total + value, 0)
  let accumulatedPace = 0

  return [
    { minute: 0, points: 0 },
    ...pace.map((value, index) => {
      accumulatedPace += value
      return {
        minute: index + 1,
        points: Math.round((finalScore * accumulatedPace / totalPace) * 10) / 10,
      }
    }),
  ]
}

function GameFlowChart({ teamA, teamB, finalScoreA, finalScoreB }: GameFlowChartProps) {
  const scoresA = buildMinuteScores(finalScoreA, 0)
  const scoresB = buildMinuteScores(finalScoreB, 1.4)
  const highestScore = Math.max(finalScoreA, finalScoreB)
  const axisMaximum = Math.max(28, Math.ceil(highestScore / 7) * 7)
  const plotWidth = CHART_WIDTH - PLOT_LEFT - PLOT_RIGHT
  const plotHeight = CHART_HEIGHT - PLOT_TOP - PLOT_BOTTOM
  const yPosition = (points: number) => PLOT_TOP + ((axisMaximum - points) / axisMaximum) * plotHeight
  const pathFor = (scores: MinuteScore[]) => scores
    .map(({ minute, points }) => {
      const x = PLOT_LEFT + (minute / MINUTES) * plotWidth
      return `${x.toFixed(1)},${yPosition(points).toFixed(1)}`
    })
    .join(' ')
  const yTicks = Array.from({ length: axisMaximum / 7 + 1 }, (_, index) => index * 7)
  const xTicks = [0, 15, 30, 45, 60]

  return (
    <figure className="game-flow">
      <svg
        className="game-flow__svg"
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        role="img"
        aria-label={`Illustrative projected score by minute: ${teamA.name} ${finalScoreA} points, ${teamB.name} ${finalScoreB} points`}
      >
        {yTicks.map((tick) => {
          const y = yPosition(tick)
          return (
            <g key={tick}>
              <line
                className="game-flow__grid"
                x1={PLOT_LEFT}
                x2={CHART_WIDTH - PLOT_RIGHT}
                y1={y}
                y2={y}
              />
              <text className="game-flow__tick" x={PLOT_LEFT - 8} y={y + 4} textAnchor="end">
                {tick}
              </text>
            </g>
          )
        })}
        {xTicks.map((tick) => {
          const x = PLOT_LEFT + (tick / MINUTES) * plotWidth
          return (
            <text className="game-flow__tick" key={tick} x={x} y={CHART_HEIGHT - 14} textAnchor="middle">
              {tick}
            </text>
          )
        })}
        <text className="game-flow__axis-label" x={PLOT_LEFT} y={CHART_HEIGHT - 1}>
          Game minute
        </text>
        <polyline
          className="game-flow__line"
          points={pathFor(scoresA)}
          stroke={teamA.colors.primary}
        />
        <polyline
          className="game-flow__line"
          points={pathFor(scoresB)}
          stroke={teamB.colors.primary}
        />
      </svg>
      <figcaption className="game-flow__caption">
        <span><i style={{ backgroundColor: teamA.colors.primary }} />{teamA.abbr}</span>
        <span><i style={{ backgroundColor: teamB.colors.primary }} />{teamB.abbr}</span>
        <span className="game-flow__units">Projected points</span>
      </figcaption>
      <p className="game-flow__note">
        Illustrative scoring pace; the final values match the projected score.
      </p>
    </figure>
  )
}

export default GameFlowChart
