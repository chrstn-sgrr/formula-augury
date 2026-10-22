"""Thin FastF1 adapter.

Everything downstream works on plain DataFrames. FastF1 is imported lazily so
tests and schema checks do not need network access or a session cache.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


class SourceUnavailable(RuntimeError):
    """FastF1 could not provide cached or downloaded session data."""


@dataclass(frozen=True)
class EventMeta:
    season: int
    round: int
    name: str
    circuit: str
    location: str
    date: str
    format: str


@dataclass(frozen=True)
class EventData:
    meta: EventMeta
    practice_laps: pd.DataFrame
    qualifying: pd.DataFrame
    qualifying_weather: pd.DataFrame
    race_laps: pd.DataFrame
    race_weather: pd.DataFrame
    results: pd.DataFrame


def load_event(season: int, round_number: int, cache_dir: Path) -> EventData:
    """Load FP2, qualifying and race, plus the separate actual result."""
    try:
        import fastf1
        from fastf1._api import SessionNotAvailableError
        from fastf1.exceptions import DataNotLoadedError
    except ImportError as error:  # pragma: no cover - dependency is installed by uv
        raise SourceUnavailable("fastf1 is not installed; run `uv sync` in pipeline/") from error

    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))

    try:
        schedule = fastf1.get_event_schedule(season, include_testing=False)
        row = schedule[schedule["RoundNumber"] == round_number]
        if row.empty:
            raise SourceUnavailable(f"round {round_number} is not in the {season} schedule")
        event = row.iloc[0]

        practice = _load_session(fastf1, season, round_number, "FP2")
        qualifying = _load_session(fastf1, season, round_number, "Q")
        race = _load_session(fastf1, season, round_number, "R")
    except (DataNotLoadedError, SessionNotAvailableError) as error:
        raise _unavailable(season, round_number) from error

    meta = EventMeta(
        season=season,
        round=round_number,
        name=str(event["EventName"]),
        # shortcut: the schedule has no circuit name, use Location until session info is available after auth
        circuit=str(event["Location"]),
        location=str(event["Location"]),
        date=pd.Timestamp(event["EventDate"]).date().isoformat(),
        format="standard" if event["EventFormat"] == "conventional" else "sprint",
    )

    return EventData(
        meta=meta,
        practice_laps=_normalise_laps(practice.laps),
        qualifying=_normalise_qualifying(qualifying.results),
        qualifying_weather=_normalise_weather(qualifying.weather_data),
        race_laps=_normalise_laps(race.laps),
        race_weather=_normalise_weather(race.weather_data),
        results=_normalise_results(race.results),
    )


def _unavailable(season: int, round_number: int) -> SourceUnavailable:
    return SourceUnavailable(
        f"FastF1 has no session data for {season} round {round_number}. "
        "F1 session data now requires an F1TV subscription token. Run "
        "`uv run python -m fastf1 auth f1tv --authenticate` in pipeline/ and retry."
    )


def _load_session(fastf1, season, round_number, code):
    session = fastf1.get_session(season, round_number, code)
    session.load(laps=True, telemetry=False, weather=True, messages=False)
    if session.laps.empty:
        raise _unavailable(season, round_number)
    return session


def _normalise_laps(laps: pd.DataFrame) -> pd.DataFrame:
    """Reduce FastF1 laps to the columns the pipeline understands."""
    lap_time = laps["LapTime"]
    if pd.api.types.is_timedelta64_dtype(lap_time):
        lap_time = lap_time.dt.total_seconds()

    return pd.DataFrame(
        {
            "driver": laps["Driver"],
            "team": laps["Team"],
            "lap_number": laps["LapNumber"],
            "lap_time_s": lap_time,
            "compound": _column(laps, "Compound"),
            "tyre_life": _column(laps, "TyreLife"),
            "stint": _column(laps, "Stint"),
            "is_pit_in": laps["PitInTime"].notna(),
            "is_pit_out": laps["PitOutTime"].notna(),
            "is_accurate": laps["IsAccurate"].fillna(False).astype(bool),
            "track_status": _column(laps, "TrackStatus").astype("string").fillna("0"),
        }
    )


def _normalise_qualifying(results: pd.DataFrame) -> pd.DataFrame:
    best = results[["Q1", "Q2", "Q3"]].min(axis=1)
    if pd.api.types.is_timedelta64_dtype(best):
        best = best.dt.total_seconds()

    return pd.DataFrame(
        {
            "driver": results["Abbreviation"],
            "team": results["TeamName"],
            "position": pd.to_numeric(results["Position"], errors="coerce").astype("Int64"),
            "best_time_s": best,
        }
    )


def _normalise_weather(weather: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "air_temp_c": weather["AirTemp"],
            "track_temp_c": weather["TrackTemp"],
            "rainfall": weather["Rainfall"].fillna(False).astype(bool),
        }
    )


def _normalise_results(results: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "driver": results["Abbreviation"],
            "team": results["TeamName"],
            "finish_position": pd.to_numeric(results["Position"], errors="coerce").astype("Int64"),
            "status": results["Status"].map(_result_status),
            "points": pd.to_numeric(results["Points"], errors="coerce").fillna(0.0),
            "classified": results["Classified"].fillna(False).astype(bool),
        }
    )


def _result_status(status: str) -> str:
    text = str(status)
    if text.startswith(("Finished", "+", "Lapped")):
        return "finished"
    if "Disqualified" in text:
        return "dsq"
    return "dnf"


def _column(frame: pd.DataFrame, name: str):
    if name in frame:
        return frame[name]
    return pd.Series(pd.NA, index=frame.index)
