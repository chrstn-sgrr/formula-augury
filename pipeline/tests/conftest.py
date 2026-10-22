import pandas as pd
import pytest

from formula_augury.source import EventData, EventMeta


def lap(
    driver,
    team,
    lap_number,
    lap_time_s,
    compound,
    tyre_life,
    stint,
    *,
    pit_in=False,
    pit_out=False,
    accurate=True,
    track_status="1",
):
    return {
        "driver": driver,
        "team": team,
        "lap_number": lap_number,
        "lap_time_s": lap_time_s,
        "compound": compound,
        "tyre_life": tyre_life,
        "stint": stint,
        "is_pit_in": pit_in,
        "is_pit_out": pit_out,
        "is_accurate": accurate,
        "track_status": track_status,
    }


def make_event(*, format="standard", rainfall=False, wet_compound=False):
    practice = pd.DataFrame(
        [
            lap("VER", "Red Bull", 2, 78.0, "MEDIUM", 1, 1),
            lap("VER", "Red Bull", 3, 78.1, "MEDIUM", 2, 1),
            lap("VER", "Red Bull", 4, 78.0, "MEDIUM", 3, 1),
            lap("VER", "Red Bull", 5, 78.2, "MEDIUM", 4, 1),
            lap("VER", "Red Bull", 6, 78.1, "MEDIUM", 5, 1),
            lap("HAM", "Mercedes", 2, 78.9, "MEDIUM", 1, 1),
            lap("HAM", "Mercedes", 3, 79.0, "MEDIUM", 2, 1),
            lap("HAM", "Mercedes", 4, 78.8, "MEDIUM", 3, 1),
            lap("HAM", "Mercedes", 5, 79.1, "MEDIUM", 4, 1),
        ]
    )

    qualifying = pd.DataFrame(
        [
            {"driver": "VER", "team": "Red Bull", "position": 1, "best_time_s": 78.0},
            {"driver": "HAM", "team": "Mercedes", "position": 2, "best_time_s": 78.3},
        ]
    )

    qualifying_weather = pd.DataFrame(
        {
            "air_temp_c": [25.0, 26.0],
            "track_temp_c": [40.0, 42.0],
            "rainfall": [False, False],
        }
    )

    race = pd.DataFrame(
        [
            # VER stint 1: lap 1 standing start, lap 6 safety car, lap 7 pit in
            lap("VER", "Red Bull", 1, 95.0, "MEDIUM", 1, 1),
            lap("VER", "Red Bull", 2, 80.0, "MEDIUM", 2, 1),
            lap("VER", "Red Bull", 3, 80.5, "MEDIUM", 3, 1),
            lap("VER", "Red Bull", 4, 81.0, "MEDIUM", 4, 1),
            lap("VER", "Red Bull", 5, 80.5, "MEDIUM", 5, 1),
            lap("VER", "Red Bull", 6, 120.0, "MEDIUM", 6, 1, track_status="4"),
            lap("VER", "Red Bull", 7, 90.0, "MEDIUM", 7, 1, pit_in=True),
            # VER stint 2: lap 8 pit out, green laps 9-14
            lap("VER", "Red Bull", 8, 82.0, "HARD", 1, 2, pit_out=True),
            lap("VER", "Red Bull", 9, 79.0, "HARD", 2, 2),
            lap("VER", "Red Bull", 10, 79.5, "HARD", 3, 2),
            lap("VER", "Red Bull", 11, 79.0, "HARD", 4, 2),
            lap("VER", "Red Bull", 12, 79.5, "HARD", 5, 2),
            lap("VER", "Red Bull", 13, 80.0, "HARD", 6, 2),
            lap("VER", "Red Bull", 14, 79.5, "HARD", 7, 2),
            # VER stint 3: safety car then pit in, no green laps, must be dropped
            lap("VER", "Red Bull", 15, 100.0, "SOFT", 1, 3, track_status="4"),
            lap("VER", "Red Bull", 16, 90.0, "SOFT", 2, 3, pit_in=True),
            # HAM stint 1: lap 4 inaccurate, lap 6 pit in
            lap("HAM", "Mercedes", 1, 96.0, "MEDIUM", 1, 1),
            lap("HAM", "Mercedes", 2, 80.2, "MEDIUM", 2, 1),
            lap("HAM", "Mercedes", 3, 80.3, "MEDIUM", 3, 1),
            lap("HAM", "Mercedes", 4, 70.0, "MEDIUM", 4, 1, accurate=False),
            lap("HAM", "Mercedes", 5, 80.4, "MEDIUM", 5, 1),
            lap("HAM", "Mercedes", 6, 90.0, "MEDIUM", 6, 1, pit_in=True),
            # HAM stint 2: lap 7 pit out, green laps 8-12
            lap("HAM", "Mercedes", 7, 83.0, "HARD", 1, 2, pit_out=True),
            lap("HAM", "Mercedes", 8, 79.2, "HARD", 2, 2),
            lap("HAM", "Mercedes", 9, 79.4, "HARD", 3, 2),
            lap("HAM", "Mercedes", 10, 79.3, "HARD", 4, 2),
            lap("HAM", "Mercedes", 11, 79.5, "HARD", 5, 2),
            lap("HAM", "Mercedes", 12, 79.4, "HARD", 6, 2),
        ]
    )
    if wet_compound:
        race.loc[race["compound"] == "SOFT", "compound"] = "INTERMEDIATE"

    race_weather = pd.DataFrame(
        {
            "air_temp_c": [28.0, 29.0],
            "track_temp_c": [45.0, 46.0],
            "rainfall": [rainfall, rainfall],
        }
    )

    results = pd.DataFrame(
        [
            {
                "driver": "VER",
                "team": "Red Bull",
                "finish_position": 1,
                "status": "finished",
                "points": 25.0,
                "classified": True,
            },
            {
                "driver": "HAM",
                "team": "Mercedes",
                "finish_position": 2,
                "status": "finished",
                "points": 18.0,
                "classified": True,
            },
        ]
    )

    meta = EventMeta(
        season=2026,
        round=7,
        name="Barcelona Grand Prix",
        circuit="Barcelona",
        location="Barcelona",
        date="2026-06-14",
        format=format,
    )
    return EventData(
        meta=meta,
        practice_laps=practice,
        qualifying=qualifying,
        qualifying_weather=qualifying_weather,
        race_laps=race,
        race_weather=race_weather,
        results=results,
    )


@pytest.fixture
def event():
    return make_event()
