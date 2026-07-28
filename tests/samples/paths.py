"""Shared paths for Level 2 sample / golden suite."""

from __future__ import annotations

from pathlib import Path

# tests/samples/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDENS_OPTIONS_DIR = REPO_ROOT / "goldens" / "options"
ARTIFACTS_HTML_DIR = REPO_ROOT / "artifacts" / "html"


def golden_path(chart_type: str, theme: str) -> Path:
    return GOLDENS_OPTIONS_DIR / f"{chart_type}__{theme}.json"


def html_artifact_path(chart_type: str, theme: str) -> Path:
    return ARTIFACTS_HTML_DIR / f"{chart_type}__{theme}.html"
