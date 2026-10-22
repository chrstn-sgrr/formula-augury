import pandas as pd
import pytest

from formula_augury.dataset import build_dataset
from formula_augury.schema import validate_results, validate_stints


def test_valid_tables_pass(event):
    stints, results = build_dataset(event)
    validate_stints(stints)
    validate_results(results)


def test_missing_column_is_rejected(event):
    stints, _ = build_dataset(event)
    with pytest.raises(ValueError, match="columns"):
        validate_stints(stints.drop(columns="compound"))


def test_result_column_is_rejected(event):
    stints, _ = build_dataset(event)
    stints["finish_position"] = 1
    with pytest.raises(ValueError, match="columns"):
        validate_stints(stints)


def test_missing_qualifying_feature_is_rejected(event):
    stints, _ = build_dataset(event)
    stints.loc[0, "quali_gap_s"] = None
    with pytest.raises(ValueError, match="quali_gap_s"):
        validate_stints(stints)


def test_duplicate_stint_is_rejected(event):
    stints, _ = build_dataset(event)
    stints = pd.concat([stints, stints.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        validate_stints(stints)


def test_unknown_compound_is_rejected(event):
    stints, _ = build_dataset(event)
    stints.loc[0, "compound"] = "INTERMEDIATE"
    with pytest.raises(ValueError, match="compound"):
        validate_stints(stints)


def test_non_finite_target_is_rejected(event):
    stints, _ = build_dataset(event)
    stints.loc[0, "stint_median_pace_delta"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        validate_stints(stints)


def test_bad_result_status_is_rejected(event):
    _, results = build_dataset(event)
    results.loc[0, "status"] = "retired"
    with pytest.raises(ValueError, match="status"):
        validate_results(results)
