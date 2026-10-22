import pandas as pd
import pytest

from formula_augury.stints import green_laps, stint_targets, wet_race


def test_race_median_uses_only_green_clean_laps(event):
    green = green_laps(event.race_laps)
    assert len(green) == 18
    assert green["lap_time_s"].median() == pytest.approx(79.5)


def test_one_row_per_stint_with_green_laps(event):
    stints = stint_targets(event.race_laps)
    assert len(stints) == 4
    assert set(zip(stints["driver"], stints["stint"])) == {
        ("VER", 1),
        ("VER", 2),
        ("HAM", 1),
        ("HAM", 2),
    }


def test_stint_targets(event):
    stints = stint_targets(event.race_laps).set_index(["driver", "stint"])
    assert stints.loc[("VER", 1), "stint_median_pace_delta"] == pytest.approx(1.0)
    assert stints.loc[("VER", 2), "stint_median_pace_delta"] == pytest.approx(0.0)
    assert stints.loc[("HAM", 1), "stint_median_pace_delta"] == pytest.approx(0.8)
    assert stints.loc[("HAM", 2), "stint_median_pace_delta"] == pytest.approx(-0.1)


def test_stint_length_keeps_in_and_out_laps(event):
    stints = stint_targets(event.race_laps).set_index(["driver", "stint"])
    assert stints.loc[("VER", 1), "stint_length"] == 7
    assert stints.loc[("VER", 2), "stint_length"] == 7
    assert stints.loc[("HAM", 1), "stint_length"] == 6


def test_tyre_age_and_lap_number_use_clean_laps(event):
    stints = stint_targets(event.race_laps).set_index(["driver", "stint"])
    assert stints.loc[("VER", 1), "tyre_age_mean"] == pytest.approx(3.5)
    assert stints.loc[("VER", 1), "mean_lap_number"] == pytest.approx(3.5)
    assert stints.loc[("VER", 2), "tyre_age_mean"] == pytest.approx(4.5)


def test_stint_without_green_laps_is_dropped(event):
    stints = stint_targets(event.race_laps)
    assert not ((stints["driver"] == "VER") & (stints["stint"] == 3)).any()


def test_no_green_laps_raises(event):
    laps = event.race_laps.copy()
    laps["track_status"] = "4"
    with pytest.raises(ValueError, match="no green-flag laps"):
        stint_targets(laps)


def test_wet_race_from_rainfall(event):
    weather = event.race_weather.copy()
    weather.loc[1, "rainfall"] = True
    assert wet_race(event.race_laps, weather)


def test_wet_race_from_wet_tyres(event):
    laps = event.race_laps.copy()
    laps.loc[laps["compound"] == "SOFT", "compound"] = "INTERMEDIATE"
    weather = event.race_weather.assign(rainfall=False)
    assert wet_race(laps, weather)


def test_dry_race(event):
    assert not wet_race(event.race_laps, event.race_weather)


def test_without_stint_column_ids_are_derived(event):
    laps = event.race_laps.drop(columns="stint")
    stints = stint_targets(laps)
    assert len(stints) == 4
    assert set(zip(stints["driver"], stints["stint"])) == {
        ("VER", 1),
        ("VER", 2),
        ("HAM", 1),
        ("HAM", 2),
    }


def test_green_laps_reject_non_green_pit_and_inaccurate(event):
    green = green_laps(event.race_laps)
    assert 1 not in green["lap_number"].tolist()
    assert not green["is_pit_in"].any()
    assert not green["is_pit_out"].any()
    assert green["is_accurate"].all()
    assert (green["track_status"] == "1").all()
