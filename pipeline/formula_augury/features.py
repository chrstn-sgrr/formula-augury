"""Pre-race features.

Only FP2, qualifying and qualifying weather enter this module. Race laps and
the actual result are never accepted here, which is what keeps the forecast
cutoff testable.
"""

import pandas as pd

from .schema import PRE_RACE_COLUMNS
from .source import EventMeta
from .stints import green_laps, with_stint_ids

MIN_LONG_RUN_LAPS = 4


def pre_race_features(
    practice_laps: pd.DataFrame,
    qualifying: pd.DataFrame,
    qualifying_weather: pd.DataFrame,
    meta: EventMeta,
) -> pd.DataFrame:
    quali = qualifying.copy()
    quali["position"] = pd.to_numeric(quali["position"], errors="coerce")
    quali = quali[quali["position"].notna() & (quali["position"] > 0)]
    if quali.empty:
        raise ValueError("qualifying has no classified drivers")

    pole = quali["best_time_s"].min()
    if pd.isna(pole):
        raise ValueError("qualifying has no lap times")

    features = pd.DataFrame(
        {
            "driver": quali["driver"],
            "grid": quali["position"].astype("Int64"),
            "quali_gap_s": quali["best_time_s"] - pole,
        }
    )
    features = features.merge(long_run_pace(practice_laps), on="driver", how="left")

    weather = qualifying_weather
    features["air_temp_c"] = _mean(weather, "air_temp_c")
    features["track_temp_c"] = _mean(weather, "track_temp_c")
    features["track"] = meta.circuit
    features["era"] = meta.season
    return features[PRE_RACE_COLUMNS]


def long_run_pace(practice_laps: pd.DataFrame, min_laps: int = MIN_LONG_RUN_LAPS) -> pd.DataFrame:
    """Median of each driver's longest clean run, as a gap to the field median.

    This is the v1 long-run definition: FP2, green and accurate laps only, one
    longest run of at least four laps. Fuel and tyre correction are not applied.
    """
    laps = with_stint_ids(practice_laps)
    clean = green_laps(laps)
    runs = (
        clean.groupby(["driver", "stint"])
        .agg(lap_count=("lap_time_s", "size"), median=("lap_time_s", "median"))
        .reset_index()
    )
    runs = runs[runs["lap_count"] >= min_laps]
    if runs.empty:
        return pd.DataFrame(columns=["driver", "practice_long_run_delta_s"])

    longest = runs.sort_values(["driver", "lap_count"], ascending=[True, False]).drop_duplicates("driver")
    field_median = float(longest["median"].median())
    return pd.DataFrame(
        {
            "driver": longest["driver"],
            "practice_long_run_delta_s": longest["median"] - field_median,
        }
    )


def _mean(weather: pd.DataFrame, column: str) -> float:
    if weather is None or weather.empty or column not in weather:
        return float("nan")
    return float(weather[column].mean())
