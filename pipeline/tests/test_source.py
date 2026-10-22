import pandas as pd
import pytest

from formula_augury.source import (
    _normalise_laps,
    _normalise_qualifying,
    _normalise_results,
    _result_status,
)


def test_lap_normalisation():
    laps = pd.DataFrame(
        {
            "Driver": ["VER"],
            "Team": ["Red Bull"],
            "LapNumber": [2],
            "LapTime": pd.to_timedelta([80.0], unit="s"),
            "Compound": ["MEDIUM"],
            "TyreLife": [2],
            "Stint": [1],
            "PitInTime": [pd.NaT],
            "PitOutTime": [pd.NaT],
            "IsAccurate": [True],
            "TrackStatus": ["1"],
        }
    )
    out = _normalise_laps(laps)
    assert out.loc[0, "lap_time_s"] == pytest.approx(80.0)
    assert out.loc[0, "track_status"] == "1"
    assert not out.loc[0, "is_pit_in"]


def test_qualifying_normalisation_uses_best_segment():
    results = pd.DataFrame(
        {
            "Abbreviation": ["VER"],
            "TeamName": ["Red Bull"],
            "Position": [1],
            "Q1": pd.to_timedelta([79.5], unit="s"),
            "Q2": pd.to_timedelta([79.0], unit="s"),
            "Q3": pd.Series([pd.NaT], dtype="timedelta64[ns]"),
        }
    )
    out = _normalise_qualifying(results)
    assert out.loc[0, "best_time_s"] == pytest.approx(79.0)


def test_result_normalisation():
    results = pd.DataFrame(
        {
            "Abbreviation": ["VER"],
            "TeamName": ["Red Bull"],
            "Position": [1],
            "Status": ["Finished"],
            "Points": [25.0],
            "Classified": [True],
        }
    )
    out = _normalise_results(results)
    assert out.loc[0, "finish_position"] == 1
    assert out.loc[0, "status"] == "finished"


def test_result_status_mapping():
    assert _result_status("Finished") == "finished"
    assert _result_status("+1 Lap") == "finished"
    assert _result_status("DNF") == "dnf"
    assert _result_status("Disqualified") == "dsq"
