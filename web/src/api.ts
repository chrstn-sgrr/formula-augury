import type { Artifact, RaceSummary } from './types'

async function getJSON<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`
    try {
      const body = (await response.json()) as { error?: string }
      if (body.error) message = body.error
    } catch {
      // Keep the status-based message when the body is not JSON.
    }
    throw new Error(message)
  }

  return (await response.json()) as T
}

export function fetchRaces(): Promise<RaceSummary[]> {
  return getJSON<RaceSummary[]>('/api/races')
}

export async function fetchRace(id: string): Promise<Artifact> {
  const artifact = await getJSON<Artifact>(`/api/races/${encodeURIComponent(id)}`)
  if (artifact.schema_version.split('.')[0] !== '0') {
    throw new Error(`Unsupported artifact schema ${artifact.schema_version}`)
  }
  return artifact
}
