"""Tests for data standardization and role inference."""

import math
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from vizly.data import (
    DataError,
    column_values,
    infer_roles,
    records,
    require_columns,
    resolve_y_columns,
    standardize,
)


def test_standardize_dataframe_copy():
    df = pd.DataFrame({"a": [1, 2]})
    out = standardize(df)
    assert list(out["a"]) == [1, 2]
    out["a"] = [9, 9]
    assert list(df["a"]) == [1, 2]


def test_standardize_list_of_dicts():
    df = standardize([{"x": 1, "y": 2}, {"x": 3, "y": 4}])
    assert list(df.columns) == ["x", "y"]
    assert df.shape == (2, 2)


def test_standardize_dict_of_lists():
    df = standardize({"region": ["East", "West"], "sales": [10, 20]})
    assert list(df["region"]) == ["East", "West"]


def test_standardize_unequal_column_lengths():
    with pytest.raises(DataError, match="unequal lengths"):
        standardize({"a": [1, 2], "b": [1]})


def test_standardize_unsupported_type():
    with pytest.raises(DataError, match="Unsupported data type"):
        standardize("not-data")  # type: ignore[arg-type]


def test_nan_to_none_in_column_values():
    df = standardize({"a": [1.0, math.nan, None], "b": [1, 2, 3]})
    assert column_values(df, "a") == [1.0, None, None]


def test_datetime_to_iso():
    df = standardize(
        {
            "date": [datetime(2026, 1, 2), pd.Timestamp("2026-02-03")],
            "value": [1, 2],
        }
    )
    vals = column_values(df, "date")
    assert vals[0].startswith("2026-01-02")
    assert vals[1].startswith("2026-02-03")
    rows = records(df)
    assert rows[0]["date"].startswith("2026-01-02")
    assert rows[0]["value"] == 1


def test_numpy_nan_to_none():
    df = standardize({"v": [np.float64(1.5), np.nan]})
    assert column_values(df, "v") == [1.5, None]


def test_infer_line_datetime_numeric():
    df = standardize(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
            "revenue": [10, 20, 30],
        }
    )
    roles = infer_roles(df)
    assert roles["chart_type"] == "line"
    assert roles["x"] == "date"
    assert roles["y"] == "revenue"
    assert roles["confidence"] == "high"


def test_infer_bar_categorical_numeric():
    df = standardize({"region": ["A", "B", "C"], "sales": [1, 2, 3]})
    roles = infer_roles(df)
    assert roles["chart_type"] == "bar"
    assert roles["x"] == "region"
    assert roles["y"] == "sales"


def test_infer_scatter_two_numerics():
    df = standardize({"height": [1.0, 2.0], "weight": [10.0, 20.0]})
    roles = infer_roles(df)
    assert roles["chart_type"] == "scatter"
    assert roles["x"] == "height"
    assert roles["y"] == "weight"


def test_infer_pie_name_value():
    df = standardize({"name": ["a", "b"], "value": [1, 2]})
    roles = infer_roles(df)
    assert roles["chart_type"] == "pie"
    assert roles["names"] == "name"
    assert roles["values"] == "value"


def test_infer_ambiguous_empty():
    with pytest.raises(DataError, match="empty"):
        infer_roles(pd.DataFrame())


def test_require_columns_error_lists_available():
    df = standardize({"a": [1], "b": [2]})
    with pytest.raises(DataError, match="Available columns: a, b"):
        require_columns(df, "a", "missing")


def test_resolve_y_columns():
    assert resolve_y_columns("a") == ["a"]
    assert resolve_y_columns(["a", "b"]) == ["a", "b"]
    with pytest.raises(DataError):
        resolve_y_columns([])
