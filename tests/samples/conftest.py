"""Fixtures and CLI flags for Level 2 sample / golden tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.samples.paths import ARTIFACTS_HTML_DIR, GOLDENS_OPTIONS_DIR

from vizly.config import reset_config
from vizly.maps import reset_opt_in_maps
from vizly.theme.registry import reset_registry


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-goldens",
        action="store_true",
        default=False,
        help="Rewrite goldens/options/*.json from current to_option() output.",
    )


@pytest.fixture
def update_goldens(request: pytest.FixtureRequest) -> bool:
    return bool(request.config.getoption("--update-goldens"))


@pytest.fixture(autouse=True)
def _clean_sample_state():
    reset_registry()
    reset_config()
    reset_opt_in_maps()
    yield
    reset_registry()
    reset_config()
    reset_opt_in_maps()


@pytest.fixture(scope="session")
def artifacts_html_dir() -> Path:
    ARTIFACTS_HTML_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_HTML_DIR


@pytest.fixture(scope="session")
def goldens_options_dir() -> Path:
    GOLDENS_OPTIONS_DIR.mkdir(parents=True, exist_ok=True)
    return GOLDENS_OPTIONS_DIR
