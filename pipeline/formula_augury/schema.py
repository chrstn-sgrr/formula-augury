"""Column contracts for the processed dataset.

The stint table holds only pre-race driver features, stint context and the
race-derived target. The actual result lives in a separate table so it can
never be joined into a forecast by accident.
"""

import math

import pandas as pd

DRY_COMPOUNDS = {"SOFT", "MEDIUM", "HARD"}
RESULT_STATUSES = {"finished", "dnf", "dsq"}

PRE_RACE_COLUMNS = [
    "driver",
    "grid",
    "quali_gap_s",
    "practice_long_run_delta_s",
    "air_temp_c",
    "track_temp_c",
    "track",
    "era",
]

STINT_COLUMNS = [
    "season",
    "round",
    "event",
    "driver",
    "team",
    "stint",
    "compound",
    "stint_length",
    "green_lap_count",
    "tyre_age_mean",
    "mean_lap_number",
    "grid",
    "quali_gap_s",
    "practice_long_run_delta_s",
    "air_temp_c",
    "track_temp_c",
    "track",
    "era",
    "stint_median_pace_delta",
]

RESULT_COLUMNS = [
    "season",
    "round",
    "event",
    "driver",
    "team",
    "finish_position",
    "status",
    "points",
    "classified",
]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_stints(stints: pd.DataFrame):
    """Check the stint table invariants before it is written."""
    _require(list(stints.columns) == STINT_COLUMNS, "stint columns do not match the schema")
    _require(not stints.empty, "stint table is empty")

    keys = ["season", "round", "driver", "stint"]
    _require(not stints[keys].isna().any().any(), "stint key contains nulls")
    _require(not stints.duplicated(keys).any(), "duplicate stint key")
    _require(stints["compound"].isin(DRY_COMPOUNDS).all(), "non-dry compound in stint table")
    _require(stints["stint_median_pace_delta"].map(math.isfinite).all(), "target is not finite")
    _require((stints["stint_length"] >= 1).all(), "stint_length must be positive")
    _require((stints["green_lap_count"] >= 1).all(), "green_lap_count must be positive")
    _require(stints["tyre_age_mean"].notna().all(), "tyre_age_mean is missing")
    _require((stints["tyre_age_mean"] >= 1).all(), "tyre_age_mean must be at least 1")
    _require((stints["mean_lap_number"] > 1).all(), "mean_lap_number must be after lap 1")
    _require(stints["grid"].notna().all(), "grid is missing")
    _require((stints["grid"] >= 1).all(), "grid must be positive")
    _require(stints["quali_gap_s"].notna().all(), "quali_gap_s is missing")
    _require((stints["quali_gap_s"] >= -1e-6).all(), "quali_gap_s must not be negative")
    _require((stints["era"] == stints["season"]).all(), "era must equal season")


def validate_results(results: pd.DataFrame):
    """Check the separate actual-result table."""
    _require(list(results.columns) == RESULT_COLUMNS, "result columns do not match the schema")
    _require(not results.empty, "result table is empty")
    _require(
        not results.duplicated(["season", "round", "driver"]).any(),
        "duplicate result driver",
    )
    _require(results["status"].isin(RESULT_STATUSES).all(), "invalid result status")
    positions = results["finish_position"].dropna()
    _require((positions >= 1).all(), "finish_position must be positive")
    _require((results["points"].fillna(0) >= 0).all(), "points must not be negative")
