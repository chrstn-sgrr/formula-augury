export type Impact = 'positive' | 'negative' | 'neutral'
export type ProbabilityKey = 'win' | 'podium' | 'points'

export interface RaceSummary {
  id: string
  season: number
  round: number
  name: string
  circuit: string
  location: string
  date: string
  mock: boolean
}

export interface Race {
  id: string
  season: number
  round: number
  name: string
  circuit: string
  location: string
  date: string
  format: 'standard' | 'sprint'
  conditions: 'dry' | 'wet'
  status: 'completed'
}

export interface TrainingWindow {
  seasons: number[]
  through_round: number
  through_date: string
}

export interface Assumptions {
  weather: string
  safety_car: boolean
  dnf: boolean
  pit_strategy: string
  pit_loss_seconds: number
  overtaking: string
}

export interface Model {
  version: string
  target: string
  training_window: TrainingWindow
  monte_carlo_runs: number
  seed: number
  assumptions: Assumptions
}

export interface Factor {
  name: string
  value: number
  unit: string
  impact: Impact
}

export interface Reasoning {
  sentence: string
  factors: Factor[]
}

export interface Probabilities {
  win: number
  podium: number
  points: number
}

export interface Driver {
  code: string
  name: string
  number: number
  team: string
  team_color: string
  grid: number
  predicted_position: number
  probabilities: Probabilities
  reasoning: Reasoning
}

export interface ActualResult {
  position: number | null
  status: 'finished' | 'dnf' | 'dsq'
}

export interface Evaluation {
  spearman: number
  baseline_spearman: number
  podium_hit_rate: number
  baseline_podium_hit_rate: number
  brier_win: number
  brier_podium: number
  brier_points: number
}

export interface Artifact {
  schema_version: string
  mock: boolean
  generated_at: string
  warnings: string[]
  race: Race
  model: Model
  drivers: Driver[]
  actual: Record<string, ActualResult>
  evaluation: Evaluation
}
