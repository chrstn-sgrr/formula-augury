import { useEffect, useState } from 'react'
import { fetchRace, fetchRaces } from './api'
import { ForecastTable } from './components/ForecastTable'
import { RaceHero } from './components/RaceHero'
import { RaceScorecard } from './components/RaceScorecard'
import { formatTimestamp } from './format'
import type { Artifact, RaceSummary } from './types'
import './App.css'

function App() {
  const [races, setRaces] = useState<RaceSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [artifact, setArtifact] = useState<Artifact | null>(null)
  const [selectedDriver, setSelectedDriver] = useState<string | null>(null)
  const [loadingRaces, setLoadingRaces] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false

    fetchRaces()
      .then((data) => {
        if (cancelled) return
        setRaces(data)
        setSelectedId((current) => (current && data.some((race) => race.id === current) ? current : data[0]?.id ?? null))
        if (data.length === 0) {
          setArtifact(null)
          setSelectedDriver(null)
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Could not load races')
      })
      .finally(() => {
        if (!cancelled) setLoadingRaces(false)
      })

    return () => {
      cancelled = true
    }
  }, [reloadKey])

  useEffect(() => {
    if (!selectedId) return

    let cancelled = false
    fetchRace(selectedId)
      .then((data) => {
        if (!cancelled) setArtifact(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load race')
      })

    return () => {
      cancelled = true
    }
  }, [selectedId, reloadKey])

  const selectedSummary = races.find((race) => race.id === selectedId) ?? null
  const artifactReady = artifact !== null && artifact.race.id === selectedId
  const loading = loadingRaces || (selectedId !== null && !artifactReady && error === null)

  function selectRace(id: string) {
    if (id === selectedId) return
    setSelectedId(id)
    setArtifact(null)
    setSelectedDriver(null)
    setError(null)
  }

  function retry() {
    setError(null)
    if (races.length === 0) setLoadingRaces(true)
    setReloadKey((value) => value + 1)
  }

  return (
    <div className="app-shell">
      <div className="ambient" aria-hidden="true" />
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <BrandMark />
            <div className="brand-copy">
              <span className="brand-name">Formula Augury</span>
              <span className="brand-sub">Race forecast / retrospective</span>
            </div>
          </div>
          <div className="topbar-right">
            {artifact?.mock && <span className="badge badge-mock">Mock data</span>}
            <label className="race-picker">
              <span className="picker-label">Race</span>
              <span className="select-wrap">
                <select
                  value={selectedId ?? ''}
                  onChange={(event) => selectRace(event.target.value)}
                  disabled={loadingRaces || races.length === 0}
                  aria-label="Select race"
                >
                  {races.length === 0 && <option value="">No races</option>}
                  {races.map((race) => (
                    <option key={race.id} value={race.id}>
                      {race.season} R{String(race.round).padStart(2, '0')} / {race.name}
                    </option>
                  ))}
                </select>
                <span className="picker-chevron" aria-hidden="true">⌄</span>
              </span>
            </label>
          </div>
        </div>
      </header>

      <main className="page">
        {loading ? (
          <LoadingState raceName={selectedSummary?.name} />
        ) : error ? (
          <ErrorState message={error} onRetry={retry} />
        ) : artifact && artifactReady ? (
          <>
            <RaceHero artifact={artifact} />
            {artifact.mock && <MockNotice warnings={artifact.warnings} />}
            <RaceScorecard evaluation={artifact.evaluation} model={artifact.model} />
            <ForecastTable
              artifact={artifact}
              selectedDriver={selectedDriver}
              onSelect={setSelectedDriver}
            />
            <Footer artifact={artifact} />
          </>
        ) : (
          <EmptyState />
        )}
      </main>
    </div>
  )
}

function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 36 36" aria-hidden="true">
      <path d="M3.5 31 13.8 5h8.4L32.5 31h-7l-1.8-5.2H12.3L10.5 31h-7Z" fill="currentColor" />
      <path d="M14.3 19.6h7.4L18 9.8l-3.7 9.8Z" fill="var(--bg)" />
    </svg>
  )
}

function MockNotice({ warnings }: { warnings: string[] }) {
  return (
    <aside className="mock-notice" role="note">
      <span className="mock-notice-kicker">Mock artifact</span>
      <p>{warnings[0] ?? 'This artifact is placeholder data for UI development.'} Do not treat these numbers as a real forecast.</p>
    </aside>
  )
}

function LoadingState({ raceName }: { raceName?: string }) {
  return (
    <div className="state-panel" role="status" aria-live="polite">
      <div className="state-bars" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </div>
      <span className="state-kicker">Loading forecast</span>
      <h2>{raceName ?? 'Connecting to the race API'}</h2>
      <p>Reading the precomputed artifact and monte carlo output.</p>
    </div>
  )
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="state-panel" role="alert">
      <span className="state-kicker state-kicker-error">API error</span>
      <h2>Forecast data did not load.</h2>
      <p>{message}</p>
      <button type="button" className="state-button" onClick={onRetry}>
        Retry request
      </button>
      <p className="state-hint">
        Start the Go API with <code>{'cd api && go run . -artifacts ../data/artifacts'}</code>, then retry.
      </p>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="state-panel">
      <span className="state-kicker">No artifacts</span>
      <h2>No race forecast found.</h2>
      <p>
        Add a JSON artifact to <code>data/artifacts/</code> and reload.
      </p>
    </div>
  )
}

function Footer({ artifact }: { artifact: Artifact }) {
  return (
    <footer className="page-footer">
      <span>
        Artifact generated {formatTimestamp(artifact.generated_at)} / schema {artifact.schema_version}
      </span>
      <span>
        Model {artifact.model.version} / {artifact.model.monte_carlo_runs.toLocaleString('en-US')} runs / pre-race data only
      </span>
    </footer>
  )
}

export default App
