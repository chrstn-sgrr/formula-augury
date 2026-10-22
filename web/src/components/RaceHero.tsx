import type { Artifact } from '../types'
import { formatDate } from '../format'

interface RaceHeroProps {
  artifact: Artifact
}

export function RaceHero({ artifact }: RaceHeroProps) {
  const { race, model } = artifact

  return (
    <section className="race-hero" aria-labelledby="race-title">
      <div className="hero-copy">
        <div className="eyebrow">
          <span>{race.season} season</span>
          <span className="eyebrow-sep" aria-hidden="true" />
          <span>Round {String(race.round).padStart(2, '0')}</span>
          <span className="eyebrow-sep" aria-hidden="true" />
          <span>{race.status}</span>
        </div>
        <h1 id="race-title">{race.name}</h1>
        <p className="hero-location">
          {race.circuit}
          <span aria-hidden="true">/</span>
          {race.location}
        </p>
        <div className="hero-meta">
          <MetaItem label="Race date" value={formatDate(race.date, 'long')} />
          <MetaItem label="Conditions" value={race.conditions} />
          <MetaItem label="Format" value={race.format} />
          <MetaItem label="Target" value={model.target.replaceAll('_', ' ')} />
        </div>
      </div>
      <div className="hero-round" aria-hidden="true">
        <span className="hero-round-label">Round</span>
        <span className="hero-round-value">{String(race.round).padStart(2, '0')}</span>
        <span className="hero-round-line" />
        <span className="hero-round-season">{race.season}</span>
      </div>
    </section>
  )
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <span className="meta-item">
      <span className="meta-label">{label}</span>
      <span className="meta-value">{value}</span>
    </span>
  )
}
