"""Tests for TabularView spine and file/SQL loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import vizly as vz
from vizly.data import ColumnarTable, as_tabular, filter_tabular
from vizly.loaders import (
    from_csv,
    from_excel,
    from_json,
    from_records,
    from_sql,
    from_tsv,
)


def test_as_tabular_records_and_columnar():
    t1 = as_tabular([{"region": "East", "sales": 10}, {"region": "West", "sales": 20}])
    assert list(t1.columns) == ["region", "sales"]
    assert t1.nrows == 2
    assert t1.column("sales") == [10, 20]

    t2 = as_tabular({"region": ["East", "West"], "sales": [10, 20]})
    assert t2.to_records() == [
        {"region": "East", "sales": 10},
        {"region": "West", "sales": 20},
    ]


def test_chart_without_dataframe():
    chart = vz.bar(
        [{"region": "East", "sales": 10}, {"region": "West", "sales": 20}],
        x="region",
        y="sales",
    )
    opt = chart.to_option()
    assert opt["series"][0]["type"] == "bar"


def test_from_csv_and_tsv(tmp_path: Path):
    csv_path = tmp_path / "t.csv"
    csv_path.write_text("region,sales\nEast,10\nWest,20\n", encoding="utf-8")
    table = from_csv(csv_path)
    assert table.column("sales") == [10, 20]
    chart = vz.bar(table, x="region", y="sales")
    assert chart.to_option()["xAxis"]["data"] == ["East", "West"]

    tsv_path = tmp_path / "t.tsv"
    tsv_path.write_text("region\tsales\nEast\t10\n", encoding="utf-8")
    assert from_tsv(tsv_path).nrows == 1


def test_from_json_records_and_columnar(tmp_path: Path):
    path = tmp_path / "t.json"
    path.write_text(
        json.dumps([{"name": "A", "value": 1}, {"name": "B", "value": 2}]),
        encoding="utf-8",
    )
    table = from_json(path)
    assert table.column("value") == [1, 2]

    col = from_json({"name": ["A", "B"], "value": [1, 2]}, orient="columnar")
    assert col.nrows == 2


def test_from_records_and_filter():
    table = from_records(
        [
            {"region": "East", "sales": 10},
            {"region": "West", "sales": 20},
            {"region": "East", "sales": 5},
        ]
    )
    filtered = filter_tabular(table, "region", "East")
    assert filtered.nrows == 2
    assert filtered.column("sales") == [10, 5]


def test_from_sql_sqlite():
    from sqlalchemy import create_engine, text

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE t (region TEXT, sales INTEGER)"))
        conn.execute(
            text("INSERT INTO t VALUES ('East', 10), ('West', 20)")
        )
    table = from_sql("SELECT region, sales FROM t ORDER BY region", bind=engine)
    assert table.column("region") == ["East", "West"]
    chart = vz.bar(table, x="region", y="sales")
    assert "series" in chart.to_option()


def test_from_excel(tmp_path: Path):
    pytest.importorskip("openpyxl")
    from openpyxl import Workbook

    path = tmp_path / "t.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["region", "sales"])
    ws.append(["East", 10])
    ws.append(["West", 20])
    wb.save(path)
    table = from_excel(path)
    assert table.column("sales") == [10, 20]


def test_set_data_live_update():
    chart = vz.line({"x": [1, 2], "y": [3, 4]}, x="x", y="y")
    opt1 = chart.to_option()
    chart.set_data({"x": [1, 2, 3], "y": [3, 4, 5]})
    opt2 = chart.to_option()
    assert len(opt2["xAxis"]["data"]) == 3
    assert opt1["xAxis"]["data"] != opt2["xAxis"]["data"]


def test_columnar_table_is_tabular_view():
    t = ColumnarTable({"a": [1], "b": [2]})
    assert isinstance(t, vz.TabularView) or hasattr(t, "to_pandas")
    df = t.to_pandas()
    assert list(df.columns) == ["a", "b"]
