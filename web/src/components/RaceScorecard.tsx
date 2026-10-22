import type { Evaluation, Model } from '../types'
import { formatPercent, formatSigned } from '../format'

interface RaceScorecardProps {
  evaluation: Evaluation
  model: Model
}

export function RaceScorecard({ evaluation, model }: RaceScorecardProps) {
  const rankDelta = evaluation.spearman - evaluation.baseline_spearman
  const podiumDelta = (evaluation.podium_hit_rate - evaluation.baseline_podium_hit_rate) * 100
  const assumptions = [
    model.assumptions.weather,
    model.assumptions.safety_car ? 'safety car' : 'no safety car',
    model.assumptions.dnf ? 'dnf' : 'no dnf',
    model.assumptions.pit_strategy.replaceAll('_', ' '),
    `${model.assumptions.pit_loss_seconds.toFixed(1)}s pit loss`,
  ]

  return (
    <section className="scorecard" aria-label="Forecast scorecard">
      <div className="scorecard-grid">
        <Metric
          label="Rank correlation"
          value={evaluation.spearman.toFixed(2)}
          detail={`Grid ${evaluation.baseline_spearman.toFixed(2)}`}
          delta={formatSigned(rankDelta, 2)}
          tone={rankDelta >= 0 ? 'positive' : 'negative'}
        />
        <Metric
          label="Podium hit rate"
          value={formatPercent(evaluation.podium_hit_rate)}
          detail={`Grid ${formatPercent(evaluation.baseline_podium_hit_rate)}`}
          delta={`${formatSigned(podiumDelta, 0)} pts`}
          tone={podiumDelta >= 0 ? 'positive' : 'negative'}
        />
        <Metric
          label="Win Brier"
          value={evaluation.brier_win.toFixed(2)}
          detail="Lower is better"
        />
        <Metric
          label="Monte Carlo"
          value={model.monte_carlo_runs.toLocaleString('en-US')}
          detail="Simulated races"
        />
      </div>
      <div className="assumption-strip">
        <span className="assumption-label">Race layer</span>
        {assumptions.map((assumption) => (
          <span className="assumption-chip" key={assumption}>
            {assumption}
          </span>
        ))}
        <span className="assumption-spacer" aria-hidden="true" />
        <span className="assumption-note">
          Trained through {model.training_window.through_date} / {model.training_window.seasons.join('-')}
        </span>
      </div>
    </section>
  )
}

interface MetricProps {
  label: string
  value: string
  detail: string
  delta?: string
  tone?: 'positive' | 'negative'
}

function Metric({ label, value, detail, delta, tone }: MetricProps) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <div className="metric-value-row">
        <span className="metric-value">{value}</span>
        {delta && <span className={`metric-delta${tone ? ` ${tone}` : ''}`}>{delta}</span>}
      </div>
      <span className="metric-detail">{detail}</span>
    </div>
  )
}
