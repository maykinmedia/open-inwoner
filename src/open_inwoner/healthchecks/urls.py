from django.urls import path

from . import views

app_name = "healthchecks"

urlpatterns = [
    # Basic health check
    path("healthz/", views.health, name="healthz"),
    # Liveness probe
    path("livez/", views.liveness, name="livez"),
    # Readiness probe
    path("readyz/", views.readiness, name="readyz"),
    # Startup probe
    path("startupz/", views.startup, name="startupz"),
]
