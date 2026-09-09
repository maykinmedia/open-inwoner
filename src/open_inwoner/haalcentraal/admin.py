from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from maykin_config_checks.api.api import with_config_checks

from .config_checks.fetch_brp import FetchBRPCheck
from .models import HaalCentraalConfig


@admin.register(HaalCentraalConfig)
@with_config_checks(FetchBRPCheck)
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
        (
            _("Checks"),
            {
                "fields": ("config_check_links",),
            },
        ),
    )
    readonly_fields = ("config_check_links",)
