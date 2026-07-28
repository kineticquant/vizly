"""Packaging contracts — version sync and declared runtime dependencies."""

from __future__ import annotations

from pathlib import Path

import vizly as vz

_ROOT = Path(__file__).resolve().parents[1]
_PYPROJECT = _ROOT / "pyproject.toml"


def _project_table_lines() -> list[str]:
    lines = _PYPROJECT.read_text(encoding="utf-8").splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "[project]":
            start = i + 1
            break
    if start is None:
        raise AssertionError("[project] table not found in pyproject.toml")
    out: list[str] = []
    for line in lines[start:]:
        if line.strip().startswith("["):
            break
        out.append(line)
    return out


def _pyproject_version() -> str:
    for line in _project_table_lines():
        stripped = line.strip()
        if stripped.startswith("version"):
            _, _, value = stripped.partition("=")
            return value.strip().strip("\"'")
    raise AssertionError("version not found under [project] in pyproject.toml")


def _pyproject_dependency_names() -> set[str]:
    lines = _project_table_lines()
    names: set[str] = set()
    in_deps = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("dependencies"):
            in_deps = True
            # dependencies = [ ... ] on one line is unlikely; handle list form
            if "[" in stripped and "]" in stripped:
                inner = stripped.split("[", 1)[1].rsplit("]", 1)[0]
                for part in inner.split(","):
                    part = part.strip().strip("\"'")
                    if part:
                        names.add(_req_name(part))
                break
            continue
        if in_deps:
            if stripped.startswith("]"):
                break
            if stripped.startswith("#") or not stripped:
                continue
            item = stripped.rstrip(",").strip("\"'")
            if item:
                names.add(_req_name(item))
    return names


def _req_name(spec: str) -> str:
    name = spec.split("[", 1)[0]
    for sep in (">=", "==", "<=", "~=", "!=", ">", "<"):
        if sep in name:
            name = name.split(sep, 1)[0]
            break
    return name.strip().lower()


def test_version_matches_pyproject():
    assert vz.__version__ == _pyproject_version()


def test_runtime_requires_pandas_and_numpy():
    names = _pyproject_dependency_names()
    assert "pandas" in names
    assert "numpy" in names
