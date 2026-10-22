import pandas as pd
import pytest

from formula_augury.features import long_run_pace, pre_race_features


def test_long_run_delta_uses_longest_run(event):
    pace = long_run_pace(event.practice_laps).set_index("driver")
    assert pace.loc["VER", "practice_long_run_delta_s"] == pytest.approx(-0.425)
    assert pace.loc["HAM", "practice_long_run_delta_s"] == pytest.approx(0.425)


def test_short_runs_are_ignored(event):
    laps = event.practice_laps[event.practice_laps["driver"] == "HAM"].head(3)
    pace = long_run_pace(laps)
    assert pace.empty


def test_pre_race_features(event):
    features = pre_race_features(
        event.practice_laps,
        event.qualifying,
        event.qualifying_weather,
        event.meta,
    ).set_index("driver")

    assert features.loc["VER", "grid"] == 1
    assert features.loc["HAM", "grid"] == 2
    assert features.loc["VER", "quali_gap_s"] == pytest.approx(0.0)
    assert features.loc["HAM", "quali_gap_s"] == pytest.approx(0.3)
    assert features.loc["VER", "air_temp_c"] == pytest.approx(25.5)
    assert features.loc["VER", "track_temp_c"] == pytest.approx(41.0)
    assert features.loc["VER", "track"] == "Barcelona"
    assert features.loc["VER", "era"] == 2026


def test_qualifying_gap_is_relative_to_pole(event):
    quali = event.qualifying.copy()
    quali["best_time_s"] = [80.0, 79.0]
    features = pre_race_features(
        event.practice_laps, quali, event.qualifying_weather, event.meta
    ).set_index("driver")
    assert features.loc["VER", "quali_gap_s"] == pytest.approx(1.0)
    assert features.loc["HAM", "quali_gap_s"] == pytest.approx(0.0)


def test_missing_practice_run_stays_null(event):
    laps = event.practice_laps[event.practice_laps["driver"] == "VER"]
    features = pre_race_features(laps, event.qualifying, event.qualifying_weather, event.meta)
    ham = features.set_index("driver").loc["HAM"]
    assert pd.isna(ham["practice_long_run_delta_s"])
