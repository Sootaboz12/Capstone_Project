import { teamLogos } from '../data/teams'

export type LogoMap = Record<string, string> // keyed by our team `id`
export type LogoStatus = 'loading' | 'ready' | 'unavailable'

export function useNflLogos() {
  return { logos: teamLogos as LogoMap, status: 'ready' as const }
}