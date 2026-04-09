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
                "fields": (
                    "service",
                    "brp_version",
                ),
            },
        ),
        (
            _("Request headers"),
            {
                "fields": ("headers",),
            },
        ),
    )
