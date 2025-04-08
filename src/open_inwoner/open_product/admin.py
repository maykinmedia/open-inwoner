# admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import OpenProductConfig


@admin.register(OpenProductConfig)
class OpenProductConfigAdmin(SingletonModelAdmin):
    """
    Admin for configuring product type action URLs.
    """

    fieldsets = [
        (
            _("Open Product Configuration"),
            {
                "fields": ["action_urls"],
                "description": _(
                    """
                    Configure URLs for producttype actions.

                    Example:
                    {"Paspoort:Afspraak maken": "https://example.nl/passport/request"}
                    """
                ),
            },
        )
    ]
