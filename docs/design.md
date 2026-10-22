# Design

The decisions locked before phase 0.

## Product

A retrospective race forecast for casual fans. Pick a completed race. See the predicted finishing order and win, podium, and points probabilities. Click a driver to read why. Compare the forecast with the actual result.

The angle is "inside the mind of an analyst." The app shows its reasoning and grades itself. It is not another telemetry viewer or a black-box predictor.

## v1 scope

- Race forecast only. Qualifying (C) and strategy what-if (D) come later.
- Dry, standard weekends only. Sprint weekends are excluded from the app and the backtest.
- Completed races only. No live timing.
- 2025 plus the 2026 races before the target race. Add 2022-2024 later.

## Data

FastF1 provides session results, lap timing, telemetry, tyres, weather, and pit stops.

For each target race, the forecast may use only data available after qualifying and before the race:

- qualifying order and gaps
- long-run pace from practice
- starting compound
- grid position
- track and weather

The actual result is stored separately and never used as a model input.

## Model

Target is stint median pace delta. One row per stint. The target is the stint's median green-flag lap time minus the race median.

Features:

- driver
- team
- track
- compound
- stint length
- mean tyre age
- mean lap number, as a fuel proxy
- qualifying gap
- long-run pace
- era, 2025 or 2026

Start with ridge regression. Add gradient boosting only if it beats the regression in the backtest. Use rolling-origin evaluation: train on races before the target, predict the target, move forward.

## Race layer

Turn predicted stint pace into a finishing order:

- start from the grid
- sample each driver's pace from the model's uncertainty
- one-stop strategy, with pit laps sampled from historical windows
- fixed pit loss per track
- simple overtaking rule

Run 10,000 simulated races and count win, podium, and points outcomes.

v1 assumes dry, no safety car, no DNF. The race layer takes a conditions object from day one so future toggles reuse the same code.

## Output

One JSON artifact per race, defined in `docs/artifact-schema.md`.

The forecast table is the first screen. One row per driver: predicted finish, win, podium, and points probability, team color accent. Click a row for a sentence and the top three factors.

## Architecture

- Python pipeline: FastF1, pandas, scikit-learn. Writes artifacts.
- Go API: serves precomputed artifacts. No Python in the request path.
- React and Vite: renders the table and reasoning panel.

Go is the only v1 API. Python runs as a batch job before the API serves the race.

## Success

Beat the grid-order baseline on held-out 2026 races.

Metrics:

- Spearman rank correlation against actual finishing order
- podium hit rate
- Brier score for win, podium, and points probabilities

Set numeric thresholds after the first backtest. If the model cannot beat grid order, it is decoration.

## Build order

1. Phase 0: artifact schema and a mock Barcelona artifact.
2. Phase 1: Go API and React table against the mock.
3. Phase 2: FastF1 pipeline for one race.
4. Phase 3: regression and rolling backtest.
5. Phase 4: race layer, Monte Carlo, reasoning panel.
6. Phase 5: all eligible 2026 races and UI polish.
7. Phase 6: qualifying, strategy, scenario toggles.

## Non-goals for v1

Live timing, wet races, safety cars, DNFs, qualifying prediction, strategy simulator, deployment, auth, database.
