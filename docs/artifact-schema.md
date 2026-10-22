# Artifact schema

Version 0.1.0. This is the contract between the Python pipeline, the Go API, and the React UI.

## File naming

`data/artifacts/{season}-{round:02d}-{slug}.json`

Example: `2026-07-barcelona.json`.

## Top-level object

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `schema_version` | string | yes | Semver. Current is `0.1.0`. |
| `mock` | boolean | yes | True means placeholder data. The UI must show a badge. |
| `generated_at` | string | yes | ISO 8601 UTC. |
| `warnings` | string[] | yes | Human-readable caveats. Empty array if none. |
| `race` | object | yes | See below. |
| `model` | object | yes | See below. |
| `drivers` | array | yes | Sorted by `predicted_position`. See below. |
| `actual` | object | yes | Keyed by driver code. See below. |
| `evaluation` | object | yes | See below. |

## race

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Stable slug, for example `2026-07-barcelona`. |
| `season` | integer | Season year. |
| `round` | integer | Championship round. |
| `name` | string | Event name. |
| `circuit` | string | Circuit name. |
| `location` | string | City and country. |
| `date` | string | Race day, `YYYY-MM-DD`. |
| `format` | string | `standard` or `sprint`. v1 supports `standard` only. |
| `conditions` | string | `dry` or `wet`. v1 supports `dry` only. |
| `status` | string | `completed`. v1 supports completed races only. |

## model

| Field | Type | Notes |
| --- | --- | --- |
| `version` | string | Model or pipeline version. |
| `target` | string | Regression target. v1 uses `stint_median_pace_delta`. |
| `training_window` | object | `seasons`, `through_round`, `through_date`. |
| `monte_carlo_runs` | integer | Number of simulated races. |
| `seed` | integer | Random seed for reproducibility. |
| `assumptions` | object | See below. |

`assumptions` contains:

| Field | Type | Notes |
| --- | --- | --- |
| `weather` | string | `dry` or `wet`. |
| `safety_car` | boolean | Whether a safety car is simulated. |
| `dnf` | boolean | Whether retirements are simulated. |
| `pit_strategy` | string | For example `one_stop_sampled`. |
| `pit_loss_seconds` | number | Fixed time lost in the pit lane. |
| `overtaking` | string | Overtaking model name. |

## drivers

Each entry:

| Field | Type | Notes |
| --- | --- | --- |
| `code` | string | Three-letter driver code, unique in the file. |
| `name` | string | Full name. |
| `number` | integer | Car number. |
| `team` | string | Constructor name. |
| `team_color` | string | `#RRGGBB`, used as a UI accent. |
| `grid` | integer | Starting position, 1 to N. Pit-lane starts are out of scope for v0.1. |
| `predicted_position` | integer | Predicted finishing position, 1 to N. |
| `probabilities` | object | `win`, `podium`, `points`, each from 0 to 1. |
| `reasoning` | object | `sentence` plus exactly three `factors`. |

Each factor:

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Factor name. |
| `value` | number | Numeric value. Negative pace and degradation values mean faster or better. |
| `unit` | string | `s/lap`, `grid`, or another unit. |
| `impact` | string | `positive`, `negative`, or `neutral`. |

## actual

An object keyed by driver code:

```json
"actual": {
  "HAM": { "position": 1, "status": "finished" },
  "BOT": { "position": 22, "status": "finished" }
}
```

`status` is `finished`, `dnf`, or `dsq`. `position` is an integer for classified drivers and `null` otherwise.

## evaluation

| Field | Type | Notes |
| --- | --- | --- |
| `spearman` | number | Rank correlation between predicted and actual order. |
| `baseline_spearman` | number | Same metric for grid order. |
| `podium_hit_rate` | number | Fraction of predicted podium drivers that finished on the podium. |
| `baseline_podium_hit_rate` | number | Same metric for grid order. |
| `brier_win` | number | Mean squared error of win probabilities. |
| `brier_podium` | number | Mean squared error of podium probabilities. |
| `brier_points` | number | Mean squared error of points probabilities. |

## Invariants

1. `drivers` contains N entries with unique `code` values.
2. `predicted_position` is a permutation of 1 to N, and the array is sorted by it.
3. `grid` is a permutation of 1 to N. Pit-lane starts are out of scope for v0.1.
4. `actual` has exactly the same keys as the driver codes.
5. `actual.position` is a permutation of 1 to N for classified drivers. It is `null` for others.
6. Every probability is between 0 and 1, and `win <= podium <= points` for each driver.
7. For every artifact, the win probabilities sum to 1, podium to 3, and points to 10 within 0.02.
8. Forecast fields must never be derived from `actual`. The actual result is stored separately for evaluation.
9. When `mock` is true, `warnings` includes a note that the data is not a real forecast.

## Mock artifacts

A mock artifact uses real driver and team names but invents every prediction, result, and metric. It exists to develop the API and UI before the model is ready. The UI must show the mock badge.

## Versioning

Patch for documentation or clarification. Minor for additive fields. Major for breaking changes. The pipeline and UI must reject an unknown major version.

## Future fields

- `qualifying` for the C module.
- `strategy` for the D module.
- `scenarios` for weather, safety car, and DNF toggles.
