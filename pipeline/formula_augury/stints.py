"""Race-derived stint targets.

This module is the only place that reads race laps. It never sees the actual
finishing order; that is kept in `dataset.py` and written separately.
"""

import pandas as pd

from .schema import DRY_COMPOUNDS


def stint_targets(race_laps: pd.DataFrame) -> pd.DataFrame:
    """One row per stint with at least one green, accurate racing lap.

    The target is the stint median lap time minus the race median. In, out,
    inaccurate, non-green and lap-1 laps are excluded from both medians. Lap 1
    is a standing start, not representative race pace.
    """
    laps = with_stint_ids(race_laps)
    green = green_laps(laps)
    if green.empty:
        raise ValueError("race has no green-flag laps to build stints from")

    race_median = float(green["lap_time_s"].median())
    stints = []
    for (driver, stint), valid in green.groupby(["driver", "stint"], sort=False):
        compounds = valid["compound"].dropna().unique()
        if len(compounds) != 1:
            raise ValueError(f"{driver} stint {stint} has mixed compounds: {compounds.tolist()}")

        all_laps = laps[(laps["driver"] == driver) & (laps["stint"] == stint)]
        stints.append(
            {
                "driver": driver,
                "team": valid["team"].iloc[0],
                "stint": int(stint),
                "compound": compounds[0],
                "stint_length": int(all_laps["lap_number"].max() - all_laps["lap_number"].min() + 1),
                "green_lap_count": len(valid),
                "tyre_age_mean": float(valid["tyre_life"].mean()),
                "mean_lap_number": float(valid["lap_number"].mean()),
                "stint_median_pace_delta": float(valid["lap_time_s"].median()) - race_median,
            }
        )

    return pd.DataFrame(stints)


def green_laps(laps: pd.DataFrame) -> pd.DataFrame:
    """Filter to clean dry running. Lap 1 is a standing start."""
    return laps[
        laps["is_accurate"].fillna(False).astype(bool)
        & laps["lap_time_s"].notna()
        & (laps["lap_time_s"] > 0)
        & (laps["track_status"].astype("string") == "1")
        & ~laps["is_pit_in"].fillna(False).astype(bool)
        & ~laps["is_pit_out"].fillna(False).astype(bool)
        & (laps["lap_number"] > 1)
        & laps["compound"].isin(DRY_COMPOUNDS)
    ].copy()


def with_stint_ids(laps: pd.DataFrame) -> pd.DataFrame:
    """Use FastF1 stint numbers, or derive them from pit exits and compounds."""
    if "stint" in laps and laps["stint"].notna().all():
        return laps

    laps = laps.sort_values(["driver", "lap_number"]).copy()
    new_tyre = laps.groupby("driver")["compound"].shift().ne(laps["compound"])
    starts = laps["is_pit_out"].fillna(False) | (new_tyre & laps["compound"].notna())
    laps["stint"] = starts.groupby(laps["driver"]).cumsum()
    return laps


def wet_race(race_laps: pd.DataFrame, weather: pd.DataFrame) -> bool:
    """Any rain sample or any wet-tyre running makes the race ineligible."""
    if weather is not None and not weather.empty and "rainfall" in weather:
        if weather["rainfall"].fillna(False).astype(bool).any():
            return True

    compounds = set(race_laps["compound"].dropna().astype(str).str.upper())
    return bool(compounds & {"INTERMEDIATE", "WET"})
