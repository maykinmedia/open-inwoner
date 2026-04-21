from django.urls import path

from maykin_config_checks.views import run_config_check

urlpatterns = [
    path(
        "admin/config-check/<str:check_id>/",
        run_config_check,
        name="run_config_check_standalone",
    ),
    path(
        "admin/config-check/<str:app_label>/<str:model_name>/<int:pk>/<str:check_id>/",
        run_config_check,
        name="run_config_check",
    ),
]
