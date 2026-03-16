from django.urls import path

from .admin_views import run_fetch_cases_check

urlpatterns = [
    path(
        "fetch-cases-check/<int:api_group_id>/",
        run_fetch_cases_check,
        name="run_fetch_cases_check",
    ),
]
