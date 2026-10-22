"""The actual result and race pace must never reach forecast features."""

from dataclasses import replace

import pandas as pd

from formula_augury.dataset import build_dataset
from formula_augury.schema import RESULT_COLUMNS, STINT_COLUMNS

RESULT_FIELDS = set(RESULT_COLUMNS) - {"season", "round", "event", "driver", "team"}
FEATURE_COLUMNS = [
    column for column in STINT_COLUMNS if column != "stint_median_pace_delta"
]


def test_changing_actual_result_does_not_change_stints(event):
    baseline, _ = build_dataset(event)
    flipped = event.results.copy()
    flipped["finish_position"] = [2, 1]
    changed, results = build_dataset(replace(event, results=flipped))

    pd.testing.assert_frame_equal(changed, baseline)
    assert results.set_index("driver").loc["VER", "finish_position"] == 2


def test_changing_lap_times_changes_only_the_target(event):
    baseline, _ = build_dataset(event)
    slower = event.race_laps.assign(lap_time_s=event.race_laps["lap_time_s"] * 1.05)
    changed, _ = build_dataset(replace(event, race_laps=slower))

    pd.testing.assert_frame_equal(changed[FEATURE_COLUMNS], baseline[FEATURE_COLUMNS])
    assert not changed["stint_median_pace_delta"].equals(baseline["stint_median_pace_delta"])


def test_stint_table_has_no_result_columns(event):
    stints, _ = build_dataset(event)
    assert not (set(stints.columns) & RESULT_FIELDS)
    assert not (set(stints.columns) & {"position", "status", "points", "classified"})
