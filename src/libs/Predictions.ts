export interface MatchupTeamStats {
  team: string
  games: number
  wins: number
  losses: number
  ties: number
  points_for: number
  points_against: number
  points_for_per_game: number
  points_against_per_game: number
  win_pct: number
  home_wins: number
  home_losses: number
  home_ties: number
  away_wins: number
  away_losses: number
  away_ties: number
}

export interface MatchupPrediction {
  season: number
  games_sampled: number
  team_a: MatchupTeamStats
  team_b: MatchupTeamStats
  home_team: string
  probability_a: number
  probability_b: number
  expected_points_a: number
  expected_points_b: number
  expected_margin_a: number
  home_field_advantage: number
  margin_std_dev: number
}

interface ApiError {
  detail?: string
}

export async function getMatchupPrediction(
  teamA: string,
  teamB: string,
  season: number,
  homeTeam: string,
): Promise<MatchupPrediction> {
  const query = new URLSearchParams({
    team_a: teamA,
    team_b: teamB,
    season: String(season),
    home_team: homeTeam,
  })
  const response = await fetch(`/predict/matchup?${query}`)
  if (!response.ok) {
    let message = `Prediction request failed (${response.status}).`
    try {
      const error = await response.json() as ApiError
      if (typeof error.detail === 'string') message = error.detail
    } catch {
      // Keep the HTTP status message when the server does not return JSON.
    }
    throw new Error(message)
  }
  return response.json() as Promise<MatchupPrediction>
}
