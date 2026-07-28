from __future__ import annotations

from django.urls import path

from examples.django_demo import views

urlpatterns = [
    path("", views.index),
]
