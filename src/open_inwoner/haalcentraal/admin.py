from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import HaalCentraalConfig


@admin.register(HaalCentraalConfig)
class HaalCentraalConfigAdmin(SingletonModelAdmin):
    readonly_fields = ("run_fetch_brp_check",)
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
        (
            _("Checks"),
            {
                "fields": ("run_fetch_brp_check",),
            },
        ),
    )

    @admin.display(description="Run BRP check")
    def run_fetch_brp_check(self, obj):
        url = reverse("run_fetch_brp_check")
        return format_html(
            '<a class="button" href="{}">Run BRP check</a>',
            url,
        )
