import json

import pandas as pd
import pytest

from formula_augury.dataset import IneligibleEvent, build_dataset, write_dataset
from formula_augury.schema import RESULT_COLUMNS, STINT_COLUMNS
from conftest import make_event


def test_dataset_columns(event):
    stints, results = build_dataset(event)
    assert list(stints.columns) == STINT_COLUMNS
    assert list(results.columns) == RESULT_COLUMNS


def test_row_counts(event):
    stints, results = build_dataset(event)
    assert len(stints) == 4
    assert len(results) == 2


def test_keys_and_features(event):
    stints, _ = build_dataset(event)
    assert stints["season"].unique().tolist() == [2026]
    assert stints["round"].unique().tolist() == [7]
    assert stints["event"].unique().tolist() == ["Barcelona Grand Prix"]
    assert stints.duplicated(["season", "round", "driver", "stint"]).sum() == 0
    assert stints["grid"].tolist() == [1, 1, 2, 2]
    assert stints["quali_gap_s"].tolist() == pytest.approx([0.0, 0.0, 0.3, 0.3])
    assert stints["track"].unique().tolist() == ["Barcelona"]
    assert stints["era"].unique().tolist() == [2026]


def test_result_table_is_separate(event):
    stints, results = build_dataset(event)
    assert "finish_position" not in stints.columns
    assert "points" not in stints.columns
    assert results.set_index("driver").loc["VER", "finish_position"] == 1
    assert results.set_index("driver").loc["HAM", "finish_position"] == 2


def test_sprint_is_rejected():
    with pytest.raises(IneligibleEvent, match="sprint"):
        build_dataset(make_event(format="sprint"))


def test_rain_is_rejected():
    with pytest.raises(IneligibleEvent, match="wet"):
        build_dataset(make_event(rainfall=True))


def test_wet_tyres_are_rejected():
    with pytest.raises(IneligibleEvent, match="wet"):
        build_dataset(make_event(wet_compound=True))


def test_write_and_read_back(event, tmp_path):
    stints, results = build_dataset(event)
    paths = write_dataset(stints, results, tmp_path, event, "test")

    written_stints = pd.read_parquet(paths["stints"])
    written_results = pd.read_parquet(paths["results"])
    pd.testing.assert_frame_equal(written_stints, stints)
    pd.testing.assert_frame_equal(written_results, results)

    manifest = json.loads(paths["manifest"].read_text())
    assert manifest["stint_rows"] == 4
    assert manifest["result_rows"] == 2
    assert manifest["race"]["round"] == 7
    assert manifest["source"] == "test"
    assert len(manifest["warnings"]) == 2
