"""Tests for deep-merge list/dict policy."""

from vizly.theme.merge import deep_merge


def test_deep_merge_nested_dicts():
    base = {"a": 1, "nested": {"x": 1, "y": 2}}
    overlay = {"nested": {"y": 9, "z": 3}, "b": 2}
    assert deep_merge(base, overlay) == {
        "a": 1,
        "b": 2,
        "nested": {"x": 1, "y": 9, "z": 3},
    }


def test_deep_merge_replaces_lists():
    base = {"palette": ["#111", "#222"]}
    overlay = {"palette": ["#AAA"]}
    assert deep_merge(base, overlay)["palette"] == ["#AAA"]


def test_deep_merge_does_not_mutate_inputs():
    base = {"nested": {"x": 1}, "palette": ["a"]}
    overlay = {"nested": {"x": 2}, "palette": ["b"]}
    deep_merge(base, overlay)
    assert base == {"nested": {"x": 1}, "palette": ["a"]}
    assert overlay == {"nested": {"x": 2}, "palette": ["b"]}


def test_deep_merge_none_overlay_copies_base():
    base = {"a": 1}
    result = deep_merge(base, None)
    assert result == {"a": 1}
    assert result is not base
