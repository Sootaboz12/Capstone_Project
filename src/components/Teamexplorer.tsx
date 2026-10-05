import { useMemo, useState } from 'react'
import { teams } from '../data/teams'
import TeamCrest from './Teamcrest'

type Filter = 'ALL' | 'AFC' | 'NFC'

function TeamExplorer() {
  const [filter, setFilter] = useState<Filter>('ALL')
  const [selectedId, setSelectedId] = useState(teams[0].id)

  const visible = useMemo(
    () => (filter === 'ALL' ? teams : teams.filter((t) => t.conference === filter)),
    [filter],
  )

  const selected = teams.find((t) => t.id === selectedId) ?? teams[0]
  const s = selected.stats

  const meters: { label: string; value: number }[] = [
    { label: 'Offense rating', value: s.offenseRating },
    { label: 'Defense rating', value: s.defenseRating },
    { label: 'Win rate', value: Math.round((s.wins / (s.wins + s.losses || 1)) * 100) },
  ]

  return (
    <section className="teams" id="teams">
      <div className="teams__head">
        <div>
          <p className="section-kicker">Every franchise</p>
          <h2 className="section-title">Team stats explorer</h2>
        </div>
        <div className="teams__filters" role="group" aria-label="Filter by conference">
          {(['ALL', 'AFC', 'NFC'] as Filter[]).map((f) => (
            <button
              key={f}
              type="button"
              className={f === filter ? 'is-active' : ''}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="teams__layout">
        <div className="teams__grid">
          {visible.map((t) => (
            <button
              type="button"
              key={t.id}
              className={`teams__cell${t.id === selectedId ? ' is-selected' : ''}`}
              onClick={() => setSelectedId(t.id)}
              aria-pressed={t.id === selectedId}
            >
              <TeamCrest team={t} size="sm" />
              <span>{t.abbr}</span>
            </button>
          ))}
        </div>

        <aside className="teams__panel">
          <div className="teams__panel-head">
            <TeamCrest team={selected} size="lg" />
            <div>
              <p className="teams__panel-record">
                {selected.stats.wins}-{selected.stats.losses}
                {selected.stats.ties ? `-${selected.stats.ties}` : ''} · Streak {selected.stats.streak}
              </p>
              <h3>{selected.city} {selected.name}</h3>
              <p className="teams__panel-sub">
                {selected.conference} {selected.division} · Power rank #{selected.stats.powerRank}
              </p>
            </div>
          </div>

          <dl className="teams__meters">
            {meters.map((m) => (
              <div className="teams__meter" key={m.label}>
                <dt>{m.label}</dt>
                <dd>
                  <div className="teams__meter-track">
                    <span style={{ width: `${m.value}%` }} />
                  </div>
                  <strong>{m.value}</strong>
                </dd>
              </div>
            ))}
          </dl>

          <div className="teams__grid-stats">
            <div>
              <span>Points for</span>
              <strong>{selected.stats.pointsFor}</strong>
            </div>
            <div>
              <span>Points against</span>
              <strong>{selected.stats.pointsAgainst}</strong>
            </div>
            <div>
              <span>Turnover margin</span>
              <strong>{selected.stats.turnoverMargin > 0 ? '+' : ''}{selected.stats.turnoverMargin}</strong>
            </div>
            <div>
              <span>Home / Away</span>
              <strong>{selected.stats.homeRecord} / {selected.stats.awayRecord}</strong>
            </div>
          </div>

          <p className="teams__panel-note">
            Placeholder figures — connect a live stats feed to replace this panel.
          </p>
        </aside>
      </div>
    </section>
  )
}

export default TeamExplorer