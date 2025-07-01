from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import HaalCentraalConfig


@admin.register(HaalCentraalConfig)
class HaalCentraalConfigAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            "Service",
            {
                "fields": ("service",),
            },
        ),
        (
            _("Headers for I Connect"),
            {
                "fields": (
                    "api_origin_oin",
                    "api_afnemer_oin",
                    "api_doelbinding",
                    "api_verwerking",
                )
            },
        ),
        (
            _("Headers for Centric"),
            {
                "fields": (
                    "x_request_organization",
                    "x_request_application",
                    "x_request_afnemerscode",
                    "x_request_user",
                )
            },
        ),
    )
