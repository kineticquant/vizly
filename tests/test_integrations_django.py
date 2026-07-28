"""Django template tag / response helper tests."""

from __future__ import annotations

import pandas as pd
import pytest

django = pytest.importorskip("django")

from django.conf import settings  # noqa: E402
from django.template import Context, Template  # noqa: E402

if not settings.configured:
    settings.configure(
        SECRET_KEY="test",
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "vizly.integrations.django",
        ],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {"context_processors": []},
            }
        ],
        USE_TZ=True,
    )
    django.setup()

import vizly as vz  # noqa: E402
from vizly.integrations.django import chart_response  # noqa: E402
from vizly.render import LOCAL_ASSET_MARKER  # noqa: E402


def _chart():
    df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
    return vz.bar(df, x="x", y="y", title="Sales <script>")


def test_django_template_tag_fragment_omits_assets_by_default():
    chart = _chart()
    tpl = Template("{% load vizly_tags %}{% vizly_chart chart fragment=True %}")
    html = tpl.render(Context({"chart": chart}))
    assert "<!DOCTYPE" not in html
    assert 'data-vizly-fragment="1"' in html
    assert LOCAL_ASSET_MARKER not in html
    assert "<script>alert" not in html


def test_django_dashboard_assets_tag():
    chart = _chart()
    tpl = Template(
        "{% load vizly_tags %}"
        "{% vizly_assets charts=charts %}"
        "{% vizly_chart chart %}"
        "{% vizly_chart chart %}"
        "{{ chart|vizly_html }}"
    )
    html = tpl.render(Context({"chart": chart, "charts": [chart, chart]}))
    assert html.count(LOCAL_ASSET_MARKER) == 1
    assert html.count("echarts.init") == 3


def test_django_filter_assets_mode_and_response():
    chart = _chart()
    tpl = Template("{% load vizly_tags %}{{ chart|vizly_html:'assets' }}")
    html = tpl.render(Context({"chart": chart}))
    assert LOCAL_ASSET_MARKER in html
    resp = chart_response(chart, fragment=False)
    assert resp.status_code == 200
    assert LOCAL_ASSET_MARKER in resp.content.decode("utf-8")


def test_django_vizly_dashboard_tag():
    chart = _chart()
    tpl = Template("{% load vizly_tags %}{% vizly_dashboard charts title='Ops' %}")
    html = tpl.render(Context({"charts": [chart, chart]}))
    assert html.count(LOCAL_ASSET_MARKER) == 1
    assert html.count("echarts.init") == 2
