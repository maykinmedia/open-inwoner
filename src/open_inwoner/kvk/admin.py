from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import KvKConfig


@admin.register(KvKConfig)
class KvKConfigAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            _("Basic"),
            {
                "fields": ("api_root",),
            },
        ),
        (
            _("Authentication"),
            {
                "fields": [
                    "api_key",
                    "client_certificate",
                    "server_certificate",
                ]
            },
        ),
    )
