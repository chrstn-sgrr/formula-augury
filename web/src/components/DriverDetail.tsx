import type { ActualResult, Driver } from '../types'
import { formatFactorValue, formatPercent, formatSigned } from '../format'

const impactLabels = {
  positive: 'Gain',
  negative: 'Cost',
  neutral: 'Neutral',
} as const

interface DriverDetailProps {
  driver: Driver
  actual: ActualResult
}

export function DriverDetail({ driver, actual }: DriverDetailProps) {
  const delta = actual.position === null ? null : actual.position - driver.predicted_position
  const resultNote =
    delta === null
      ? 'No classified result'
      : delta < 0
        ? 'Finished ahead of the forecast'
        : delta > 0
          ? 'Finished behind the forecast'
          : 'Matched the forecast'

  return (
    <div className="driver-detail">
      <div className="detail-main">
        <div className="detail-kicker">
          <span className="detail-marker" aria-hidden="true" />
          Model note / {driver.code}
        </div>
        <p className="detail-sentence">{driver.reasoning.sentence}</p>
        <div className="factor-grid">
          {driver.reasoning.factors.map((factor) => (
            <div className={`factor-card ${factor.impact}`} key={factor.name}>
              <span className="factor-name">{factor.name}</span>
              <span className="factor-value">{formatFactorValue(factor)}</span>
              <span className="factor-impact">{impactLabels[factor.impact]}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="detail-side">
        <div>
          <span className="detail-side-label">Outcome probability</span>
          {(['win', 'podium', 'points'] as const).map((key) => (
            <div className="detail-prob" key={key}>
              <div className="detail-prob-row">
                <span>{key}</span>
                <strong>{formatPercent(driver.probabilities[key], 1)}</strong>
              </div>
              <span className="detail-prob-track" aria-hidden="true">
                <span style={{ width: `${driver.probabilities[key] * 100}%` }} />
              </span>
            </div>
          ))}
        </div>
        <div className="detail-result">
          <span className="detail-side-label">Actual result</span>
          <div className="detail-result-row">
            <strong>{actual.position === null ? actual.status.toUpperCase() : `P${actual.position}`}</strong>
            {delta !== null && delta !== 0 && (
              <span className={`detail-result-delta ${delta < 0 ? 'up' : 'down'}`}>{formatSigned(delta, 0)}</span>
            )}
            {delta === 0 && <span className="detail-result-delta flat">Flat</span>}
          </div>
          <span className="detail-result-note">{resultNote}</span>
        </div>
      </div>
    </div>
  )
}
