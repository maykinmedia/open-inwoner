from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from maykin_config_checks.api.api import with_config_checks

from .config_checks.fetch_company import FetchCompanyCheck
from .models import KvKConfig


@admin.register(KvKConfig)
@with_config_checks(FetchCompanyCheck)
class KvKConfigAdmin(SingletonModelAdmin):
    readonly_fields = ("config_check_links",)
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
        (
            _("Config checks"),
            {
                "fields": ("config_check_links",),
            },
        ),
    )
