import type { CSSProperties } from 'react'
import { useState } from 'react'
import type { Team } from '../data/teams'

interface TeamCrestProps {
  team: Team
  size?: 'sm' | 'md' | 'lg'
  logoUrl?: string
}

function TeamCrest({ team, size = 'md', logoUrl }: TeamCrestProps) {
  const [imgFailed, setImgFailed] = useState(false)
  const showImage = Boolean(logoUrl) && !imgFailed

  return (
    <div
      className={`crest crest--${size}`}
      style={
        {
          '--crest-primary': team.colors.primary,
          '--crest-secondary': team.colors.secondary,
        } as CSSProperties
      }
    >
      {showImage ? (
        <img
          src={logoUrl}
          alt={`${team.city} ${team.name} logo`}
          className="crest__image"
          loading="lazy"
          onError={() => setImgFailed(true)}
        />
      ) : (
        <>
          <svg viewBox="0 0 64 72" className="crest__shield" aria-hidden="true">
            <path
              d="M32 2 L60 12 V34 C60 52 48 64 32 70 C16 64 4 52 4 34 V12 Z"
              className="crest__fill"
            />
            <path
              d="M32 2 L60 12 V34 C60 52 48 64 32 70 C16 64 4 52 4 34 V12 Z"
              className="crest__outline"
              fill="none"
            />
          </svg>
          <span className="crest__abbr">{team.abbr}</span>
        </>
      )}
    </div>
  )
}

export default TeamCrest