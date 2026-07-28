"""
Minimal Django demo for vizly template tags.

Run (from repo root, with django installed)::

    set DJANGO_SETTINGS_MODULE=examples.django_demo.settings
    django-admin runserver --pythonpath=.
"""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "vizly-django-demo-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "vizly.integrations.django",
]

ROOT_URLCONF = "examples.django_demo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

MIDDLEWARE = []
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
USE_TZ = True
STATIC_URL = "/static/"
