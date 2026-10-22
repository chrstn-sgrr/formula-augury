import { Fragment } from 'react'
import type { CSSProperties } from 'react'
import type { Artifact } from '../types'
import { formatPercent, formatSigned } from '../format'
import { DriverDetail } from './DriverDetail'

interface ForecastTableProps {
  artifact: Artifact
  selectedDriver: string | null
  onSelect: (code: string | null) => void
}

export function ForecastTable({ artifact, selectedDriver, onSelect }: ForecastTableProps) {
  return (
    <section className="forecast-panel" aria-labelledby="forecast-title">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">Forecast / monte carlo output</span>
          <h2 id="forecast-title">Predicted classification</h2>
        </div>
        <p className="panel-hint">
          <span className="hint-desktop">Select a driver to inspect the model note.</span>
          <span className="hint-mobile">Swipe the table for probabilities.</span>
        </p>
      </div>
      <div className="table-scroll">
        <table className="forecast-table">
          <caption className="sr-only">Predicted finishing order for {artifact.race.name}</caption>
          <thead>
            <tr>
              <th className="col-pos">Pos</th>
              <th>Driver</th>
              <th className="col-grid numeric">Grid</th>
              <th className="col-prob numeric">Win</th>
              <th className="col-prob numeric">Podium</th>
              <th className="col-prob numeric">Points</th>
              <th className="col-actual numeric">Actual</th>
              <th className="col-toggle">
                <span className="sr-only">Reasoning</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {artifact.drivers.map((driver) => {
              const active = driver.code === selectedDriver
              const actual = artifact.actual[driver.code]
              const delta = actual?.position == null ? null : actual.position - driver.predicted_position
              const style = { '--team': driver.team_color } as CSSProperties
              const detailId = `driver-detail-${driver.code}`

              return (
                <Fragment key={driver.code}>
                  <tr
                    className={`driver-row${active ? ' is-active' : ''}`}
                    style={style}
                    onClick={() => onSelect(active ? null : driver.code)}
                  >
                    <td className="numeric">
                      <span className="pos-value">{String(driver.predicted_position).padStart(2, '0')}</span>
                    </td>
                    <td>
                      <div className="driver-cell-inner">
                        <span className="team-dot" aria-hidden="true" />
                        <div className="driver-text">
                          <div className="driver-primary">
                            <span className="driver-code">{driver.code}</span>
                            <span className="driver-name">{driver.name}</span>
                          </div>
                          <div className="driver-secondary">
                            <span className="driver-team">{driver.team}</span>
                            <span className="driver-sep" aria-hidden="true">/</span>
                            <span className="driver-number">#{driver.number}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="numeric">
                      <span className="grid-value">P{driver.grid}</span>
                    </td>
                    {(['win', 'podium', 'points'] as const).map((key) => (
                      <td className="numeric" key={key}>
                        <div className="prob-cell-inner">
                          <span className="prob-number">{formatPercent(driver.probabilities[key])}</span>
                          <span className="prob-track" aria-hidden="true">
                            <span
                              className="prob-fill"
                              style={{ width: `${Math.min(100, Math.max(0, driver.probabilities[key] * 100))}%` }}
                            />
                          </span>
                        </div>
                      </td>
                    ))}
                    <td className="numeric">
                      <div className="actual-cell-inner">
                        {actual?.status === 'finished' && actual.position !== null ? (
                          <>
                            <span className="actual-pos">P{actual.position}</span>
                            {delta !== null && delta !== 0 && (
                              <span
                                className={`actual-delta ${delta < 0 ? 'up' : 'down'}`}
                                title="Actual position minus forecast position"
                              >
                                {formatSigned(delta, 0)}
                              </span>
                            )}
                          </>
                        ) : (
                          <span className="actual-dnf">{actual?.status?.toUpperCase() ?? 'N/A'}</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="detail-toggle"
                        aria-expanded={active}
                        aria-controls={active ? detailId : undefined}
                        aria-label={`${active ? 'Hide' : 'Show'} model note for ${driver.name}`}
                        onClick={(event) => {
                          event.stopPropagation()
                          onSelect(active ? null : driver.code)
                        }}
                      >
                        <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
                          <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" />
                        </svg>
                      </button>
                    </td>
                  </tr>
                  {active && (
                    <tr className="detail-row" id={detailId}>
                      <td colSpan={8} style={style}>
                        <DriverDetail driver={driver} actual={actual} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </section>
  )
}
