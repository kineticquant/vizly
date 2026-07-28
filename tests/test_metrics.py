"""Ops metric payload → DataFrame helpers."""

from __future__ import annotations

import pytest

import vizly as vz
from vizly.data import DataError


def test_from_prometheus_matrix():
    payload = {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"__name__": "up", "job": "api"},
                    "values": [[1700000000, "1"], [1700000060, "0"]],
                }
            ],
        },
    }
    df = vz.from_prometheus(payload)
    assert list(df.columns) == ["timestamp", "value", "series"]
    assert len(df) == 2
    assert df["value"].tolist() == [1.0, 0.0]
    assert "up{job=api}" in df["series"].iloc[0]
    chart = vz.line(df, x="timestamp", y="value", theme="ops_grafana")
    assert chart.to_option()["series"][0]["type"] == "line"


def test_from_prometheus_vector():
    payload = {
        "data": {
            "resultType": "vector",
            "result": [{"metric": {"job": "a"}, "value": [1700000000, "3.5"]}],
        }
    }
    df = vz.from_prometheus(payload)
    assert len(df) == 1
    assert df["value"].iloc[0] == 3.5


def test_from_cloudwatch_datapoints():
    payload = {
        "Datapoints": [
            {
                "Timestamp": "2026-01-01T00:00:00Z",
                "Average": 1.5,
                "Unit": "Count",
            },
            {
                "Timestamp": "2026-01-01T00:01:00Z",
                "Average": 2.0,
                "Unit": "Count",
            },
        ]
    }
    df = vz.from_cloudwatch(payload)
    assert df["value"].tolist() == [1.5, 2.0]
    assert "unit" in df.columns


def test_from_cloudwatch_metric_data():
    payload = {
        "MetricDataResults": [
            {
                "Id": "m1",
                "Label": "CPU",
                "Timestamps": ["2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z"],
                "Values": [10.0, 20.0],
            }
        ]
    }
    df = vz.from_cloudwatch(payload)
    assert df["series"].tolist() == ["CPU", "CPU"]
    assert df["value"].tolist() == [10.0, 20.0]


def test_from_elasticsearch_date_histogram():
    payload = {
        "aggregations": {
            "by_time": {
                "buckets": [
                    {
                        "key_as_string": "2026-01-01T00:00:00.000Z",
                        "key": 1735689600000,
                        "doc_count": 4,
                        "avg_latency": {"value": 12.5},
                    },
                    {
                        "key_as_string": "2026-01-01T01:00:00.000Z",
                        "key": 1735693200000,
                        "doc_count": 7,
                        "avg_latency": {"value": 9.0},
                    },
                ]
            }
        }
    }
    df = vz.from_elk(payload)
    assert df["value"].tolist() == [4.0, 7.0]
    df2 = vz.from_elasticsearch(payload, metric="avg_latency")
    assert df2["value"].tolist() == [12.5, 9.0]


def test_from_prometheus_bad_payload():
    with pytest.raises(DataError):
        vz.from_prometheus({"nope": True})


def test_from_prometheus_skips_malformed_with_warning():
    payload = {
        "data": {
            "resultType": "matrix",
            "result": [
                "bad-item",
                {
                    "metric": {"__name__": "up"},
                    "values": [[1700000000, "1"], "short"],
                },
            ],
        }
    }
    with pytest.warns(UserWarning, match="skipped"):
        df = vz.from_prometheus(payload)
    assert len(df) == 1
    assert df.attrs["vizly_skipped"] == 2


def test_ops_themes_registered():
    for name in ("ops_grafana", "ops_cloudwatch", "ops_kibana"):
        t = vz.set_theme(name)
        assert t["name"] == name
        assert t["series_defaults"]["line"]["smooth"] is False
