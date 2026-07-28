"""Django AppConfig so ``vizly.integrations.django`` can host templatetags."""

from __future__ import annotations

try:
    from django.apps import AppConfig
except ImportError:  # pragma: no cover
    AppConfig = object  # type: ignore[misc,assignment]


class VizlyConfig(AppConfig):  # type: ignore[misc]
    name = "vizly.integrations.django"
    # Avoid colliding with a user app labeled "vizly".
    label = "vizly_django"
    verbose_name = "vizly"
    default = True
