import { useEffect, useState } from 'react'
import { getNflTeamLogos } from '../libs/NFLapi'
import { teams as staticTeams } from '../data/teams'

export type LogoMap = Record<string, string> // keyed by our team `id`
export type LogoStatus = 'loading' | 'ready' | 'unavailable'

/**
 * Resolves each static team to a live crest image URL from the NFL API.
 * If the request fails, is rate-limited, or a team just isn't matched, that
 * team simply falls back to <TeamCrest>'s generated placeholder — nothing
 * in the UI depends on this succeeding.
 */
export function useNflLogos() {
  const [logos, setLogos] = useState<LogoMap>({})
  const [status, setStatus] = useState<LogoStatus>('loading')

  useEffect(() => {
    let cancelled = false

    getNflTeamLogos()
      .then((apiTeams) => {
        if (cancelled) return
        const map: LogoMap = {}
        for (const team of staticTeams) {
          const match = apiTeams.find((t) => {
            const codeMatch = t.code && t.code.toUpperCase() === team.abbr
            const nameMatch = t.name && team.name.toLowerCase().includes(t.name.toLowerCase())
            return codeMatch || nameMatch
          })
          if (match?.logo) map[team.id] = match.logo
        }
        setLogos(map)
        setStatus(Object.keys(map).length > 0 ? 'ready' : 'unavailable')
      })
      .catch(() => {
        if (!cancelled) setStatus('unavailable')
      })

    return () => {
      cancelled = true
    }
  }, [])

  return { logos, status }
}