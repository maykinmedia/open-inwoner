from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import MijnAfvalConfig


@admin.register(MijnAfvalConfig)
class MijnAfvalAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            _("OpenAfval API configuration"),
            {"fields": ("openafval_service",)},
        ),
    )

    class Meta:
        verbose_name = _("Configuratie Mijn Afval")
