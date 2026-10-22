"""Assemble, validate and write the processed stint dataset."""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .features import pre_race_features
from .schema import RESULT_COLUMNS, STINT_COLUMNS, validate_results, validate_stints
from .source import EventData
from .stints import stint_targets, wet_race


class IneligibleEvent(ValueError):
    """The event is outside the v1 dry standard-weekend scope."""


def build_dataset(event: EventData) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the stint table and the separate actual-result table."""
    reason = ineligibility(event)
    if reason:
        raise IneligibleEvent(f"{event.meta.season} round {event.meta.round}: {reason}")

    # Pre-race features are built before race laps are touched for the target.
    features = pre_race_features(
        event.practice_laps,
        event.qualifying,
        event.qualifying_weather,
        event.meta,
    )
    targets = stint_targets(event.race_laps)

    stints = targets.merge(features, on="driver", how="left", validate="many_to_one")
    stints.insert(0, "season", event.meta.season)
    stints.insert(1, "round", event.meta.round)
    stints.insert(2, "event", event.meta.name)
    stints = stints[STINT_COLUMNS]

    results = event.results.copy()
    results.insert(0, "season", event.meta.season)
    results.insert(1, "round", event.meta.round)
    results.insert(2, "event", event.meta.name)
    results = results[RESULT_COLUMNS]

    validate_stints(stints)
    validate_results(results)
    return stints, results


def ineligibility(event: EventData) -> str | None:
    if event.meta.format != "standard":
        return "sprint weekend"
    if wet_race(event.race_laps, event.race_weather):
        return "wet race"
    return None


def write_dataset(
    stints: pd.DataFrame,
    results: pd.DataFrame,
    out_dir: Path,
    event: EventData,
    source: str,
) -> dict[str, Path]:
    """Write stints, results and a small manifest. Validates before writing."""
    validate_stints(stints)
    validate_results(results)

    out_dir.mkdir(parents=True, exist_ok=True)
    stints_path = out_dir / "stints.parquet"
    results_path = out_dir / "results.parquet"
    manifest_path = out_dir / "stints.meta.json"

    stints.to_parquet(stints_path, index=False)
    results.to_parquet(results_path, index=False)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "race": asdict(event.meta),
        "stint_rows": len(stints),
        "result_rows": len(results),
        "columns": list(stints.columns),
        "warnings": [
            "grid is the qualifying classification; penalty grid drops are not modelled",
            "long-run pace is the longest green FP2 run of at least four laps, uncorrected for fuel",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return {"stints": stints_path, "results": results_path, "manifest": manifest_path}
