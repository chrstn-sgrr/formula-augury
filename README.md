# Formula Augury

Retrospective F1 race forecasts. Pick a completed race, see the predicted finishing order and win, podium, and points probabilities, click a driver for the reasoning, and compare the forecast with the actual result.


## Layout

- `api/` Go API. Serves artifacts and a race index. No Python in the request path.
- `web/` React and Vite UI. The dev and preview servers proxy `/api` to port `8080`.
- `data/artifacts/` forecast artifacts, one JSON file per race.
- `docs/artifact-schema.md` contract between the pipeline, API, and UI.
- `docs/design.md` product, model, race layer, and build phases.
- `scripts/validate_artifact.py` invariant checks for an artifact.

## Run locally

Terminal 1:

```sh
cd api
go run . -artifacts ../data/artifacts
```

Terminal 2:

```sh
cd web
npm install
npm run dev
```

Open `http://localhost:5173`.

The mock artifact shows a `Mock data` badge. It uses real 2026 driver and team names, but every prediction, result, and metric is invented.

## Build and preview

```sh
cd web
npm run build
npm run preview
```

## Checks

```sh
python scripts/validate_artifact.py data/artifacts/2026-07-barcelona.json
(cd api && go test ./...)
(cd web && npm run lint && npm run build)
```

## API

- `GET /healthz`
- `GET /api/races`
- `GET /api/races/{id}`
