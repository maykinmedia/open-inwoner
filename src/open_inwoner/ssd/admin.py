from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import SSDConfig


@admin.register(SSDConfig)
class SSDConfigAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            _("SSD client"),
            {
                "fields": (
                    "service",
                    "bedrijfs_naam",
                    "applicatie_naam",
                    "gemeentecode",
                )
            },
        ),
        (
            _("Yearly reports"),
            {
                "fields": (
                    "jaaropgave_enabled",
                    "jaaropgave_range",
                    "jaaropgave_available_from",
                ),
            },
        ),
        (
            _("Monthly reports"),
            {
                "fields": (
                    "maandspecificatie_enabled",
                    "maandspecificatie_range",
                    "maandspecificatie_available_from",
                ),
            },
        ),
    )

    class Meta:
        verbose_name = _("SSD configuration")
