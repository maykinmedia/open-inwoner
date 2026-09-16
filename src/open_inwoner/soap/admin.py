from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import SoapService


@admin.register(SoapService)
class SoapServiceAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "url",
    )
    search_fields = (
        "slug",
        "url",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "slug",
                    "url",
                ),
            },
        ),
        (
            _("Authentication"),
            {
                "fields": [
                    "client_certificate",
                    "server_certificate",
                ]
            },
        ),
    )
