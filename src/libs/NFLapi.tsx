const BASE_URL = 'https://v1.american-football.api-sports.io'
const NFL_LEAGUE_ID = 1
const CACHE_KEY = 'spread:nfl-teams-cache:v1'
const CACHE_TTL_MS = 1000 * 60 * 60 * 24 // 24h — the free plan only allows 100 calls/day

// Vite inlines VITE_-prefixed env vars into the client bundle at build time,
// so this is never truly secret in a pure front-end app. Set VITE_NFL_API_KEY
// in a .env file to override; the value below is only a local fallback.
const API_KEY = (import.meta as any).env?.VITE_NFL_API_KEY || '0d74e087b31604b4eb00252c35cb7b8e'

export interface ApiTeam {
  id: number
  name: string
  code: string | null
  city: string | null
  logo: string | null
}

interface CachePayload {
  fetchedAt: number
  season: number
  teams: ApiTeam[]
}

function guessCurrentSeason(): number {
  const now = new Date()
  // NFL seasons are labelled by the year they kick off in (Sept–Feb), so
  // Jan/Feb of a given year still belongs to the previous label.
  return now.getMonth() >= 2 ? now.getFullYear() : now.getFullYear() - 1
}

function readCache(): CachePayload | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as CachePayload
    if (!Array.isArray(parsed.teams)) return null
    return parsed
  } catch {
    return null
  }
}

function writeCache(payload: CachePayload) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(payload))
  } catch {
    // storage unavailable/full — safe to skip, the fetched data is still returned
  }
}

async function fetchTeamsForSeason(season: number): Promise<ApiTeam[]> {
  const url = `${BASE_URL}/teams?league=${NFL_LEAGUE_ID}&season=${season}`
  const res = await fetch(url, {
    headers: { 'x-apisports-key': API_KEY },
  })
  if (!res.ok) throw new Error(`NFL API request failed: ${res.status}`)
  const data = await res.json()
  const list = Array.isArray(data?.response) ? data.response : []
  return list.map((t: any) => ({
    id: t.id,
    name: t.name ?? '',
    code: t.code ?? null,
    city: t.city ?? null,
    logo: t.logo ?? null,
  }))
}

/**
 * Fetches the NFL team list (mainly for logo URLs), preferring a cached
 * response so the framework doesn't burn through the free-tier daily quota
 * on every page load. Falls back through a couple of recent seasons in case
 * the current season isn't populated yet, and resolves to an empty array
 * (never throws) so callers can fall back to the local crest placeholder.
 */
export async function getNflTeamLogos(): Promise<ApiTeam[]> {
  const cached = readCache()
  if (cached && Date.now() - cached.fetchedAt < CACHE_TTL_MS && cached.teams.length > 0) {
    return cached.teams
  }

  const startSeason = guessCurrentSeason()
  const seasonsToTry = [startSeason, startSeason - 1]

  for (const season of seasonsToTry) {
    try {
      const fetched = await fetchTeamsForSeason(season)
      if (fetched.length > 0) {
        writeCache({ fetchedAt: Date.now(), season, teams: fetched })
        return fetched
      }
    } catch {
      // try the next season in the list
    }
  }

  // Serve a stale cache rather than nothing, if one exists.
  if (cached) return cached.teams
  return []
}