#!/usr/bin/env python3
"""Validate a formula-augury forecast artifact against the v0.1 contract."""

import json
import re
import sys
from pathlib import Path

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
DRIVER_CODE = re.compile(r"^[A-Z]{3}$")
IMPACTS = {"positive", "negative", "neutral"}
STATUSES = {"finished", "dnf", "dsq"}


def fail(message):
    raise SystemExit(f"invalid artifact: {message}")


def require(condition, message):
    if not condition:
        fail(message)


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def main(path):
    try:
        data = json.loads(Path(path).read_text())
    except json.JSONDecodeError as error:
        fail(f"not valid JSON: {error}")

    for key in ("schema_version", "mock", "generated_at", "warnings", "race", "model", "drivers", "actual", "evaluation"):
        require(key in data, f"missing top-level field {key!r}")

    require(data["schema_version"] == "0.1.0", "unsupported schema_version")
    require(isinstance(data["mock"], bool), "mock must be a boolean")
    require(isinstance(data["warnings"], list), "warnings must be a list")
    require(all(isinstance(item, str) for item in data["warnings"]), "warnings must contain strings")

    race = data["race"]
    for key in ("id", "season", "round", "name", "circuit", "location", "date", "format", "conditions", "status"):
        require(key in race, f"missing race.{key}")
    require(race["format"] in {"standard", "sprint"}, "race.format is invalid")
    require(race["conditions"] in {"dry", "wet"}, "race.conditions is invalid")
    require(race["status"] == "completed", "race.status must be completed")

    model = data["model"]
    for key in ("version", "target", "training_window", "monte_carlo_runs", "seed", "assumptions"):
        require(key in model, f"missing model.{key}")
    require(isinstance(model["monte_carlo_runs"], int) and model["monte_carlo_runs"] > 0, "monte_carlo_runs must be positive")

    assumptions = model["assumptions"]
    for key in ("weather", "safety_car", "dnf", "pit_strategy", "pit_loss_seconds", "overtaking"):
        require(key in assumptions, f"missing model.assumptions.{key}")
    require(isinstance(assumptions["safety_car"], bool), "safety_car must be a boolean")
    require(isinstance(assumptions["dnf"], bool), "dnf must be a boolean")

    drivers = data["drivers"]
    require(isinstance(drivers, list) and len(drivers) >= 2, "drivers must contain at least two entries")
    total = len(drivers)
    codes = [driver.get("code") for driver in drivers]
    require(all(isinstance(code, str) and DRIVER_CODE.match(code) for code in codes), "driver codes must be three uppercase letters")
    require(len(set(codes)) == total, "driver codes must be unique")

    predicted = [driver.get("predicted_position") for driver in drivers]
    require(predicted == list(range(1, total + 1)), "drivers must be sorted by predicted_position 1..N")

    grids = [driver.get("grid") for driver in drivers]
    require(all(isinstance(grid, int) for grid in grids), "grid positions must be integers")
    require(sorted(grids) == list(range(1, total + 1)), "grid positions must be a permutation of 1..N")

    for driver in drivers:
        code = driver["code"]
        for key in ("name", "number", "team", "team_color", "grid", "predicted_position", "probabilities", "reasoning"):
            require(key in driver, f"{code}: missing {key}")
        require(isinstance(driver["team_color"], str) and HEX_COLOR.match(driver["team_color"]), f"{code}: team_color must be #RRGGBB")

        probabilities = driver["probabilities"]
        for key in ("win", "podium", "points"):
            require(key in probabilities, f"{code}: missing probabilities.{key}")
            value = probabilities[key]
            require(is_number(value) and 0 <= value <= 1, f"{code}: {key} probability must be between 0 and 1")
        require(probabilities["win"] <= probabilities["podium"] <= probabilities["points"], f"{code}: probabilities must satisfy win <= podium <= points")

        reasoning = driver["reasoning"]
        require(isinstance(reasoning.get("sentence"), str) and reasoning["sentence"], f"{code}: reasoning sentence is empty")
        factors = reasoning.get("factors")
        require(isinstance(factors, list) and len(factors) == 3, f"{code}: reasoning must have exactly three factors")
        for factor in factors:
            require(isinstance(factor.get("name"), str) and factor["name"], f"{code}: factor name is empty")
            require(is_number(factor.get("value")), f"{code}: factor value must be a number")
            require(isinstance(factor.get("unit"), str) and factor["unit"], f"{code}: factor unit is empty")
            require(factor.get("impact") in IMPACTS, f"{code}: factor impact is invalid")

    actual = data["actual"]
    require(isinstance(actual, dict), "actual must be an object")
    require(set(actual) == set(codes), "actual keys must match driver codes")

    finished = []
    for code, result in actual.items():
        require(result.get("status") in STATUSES, f"{code}: actual.status is invalid")
        position = result.get("position")
        if result["status"] == "finished":
            require(isinstance(position, int) and 1 <= position <= total, f"{code}: finished position must be 1..N")
            finished.append(position)
        else:
            require(position is None, f"{code}: non-finisher position must be null")
    require(sorted(finished) == list(range(1, len(finished) + 1)), "finished positions must be unique")

    for key, expected in (("win", 1.0), ("podium", 3.0), ("points", 10.0)):
        total_probability = sum(driver["probabilities"][key] for driver in drivers)
        require(abs(total_probability - expected) <= 0.02, f"{key} probabilities must sum to {expected}, got {total_probability:.3f}")

    evaluation = data["evaluation"]
    for key in ("spearman", "baseline_spearman", "podium_hit_rate", "baseline_podium_hit_rate", "brier_win", "brier_podium", "brier_points"):
        require(key in evaluation, f"missing evaluation.{key}")
        require(is_number(evaluation[key]), f"evaluation.{key} must be a number")
    require(-1 <= evaluation["spearman"] <= 1, "evaluation.spearman must be between -1 and 1")
    require(-1 <= evaluation["baseline_spearman"] <= 1, "evaluation.baseline_spearman must be between -1 and 1")
    require(0 <= evaluation["podium_hit_rate"] <= 1, "evaluation.podium_hit_rate must be between 0 and 1")
    require(0 <= evaluation["baseline_podium_hit_rate"] <= 1, "evaluation.baseline_podium_hit_rate must be between 0 and 1")

    if data["mock"]:
        require(any("mock" in warning.lower() for warning in data["warnings"]), "mock artifacts must warn that the data is mock")

    print(f"OK: {path} ({total} drivers)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} PATH")
    main(sys.argv[1])
