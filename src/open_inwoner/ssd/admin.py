from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import JaaropgaveConfig, MaandspecificatieConfig, SSDConfig


class JaaropgaveConfigInline(admin.StackedInline):
    model = JaaropgaveConfig
    min_num = 1
    max_num = 1
    can_delete = False
    verbose_name = _("Jaaropgave report configuration")


class MaandspecificatieConfigInline(admin.StackedInline):
    model = MaandspecificatieConfig
    min_num = 1
    max_num = 1
    can_delete = False
    verbose_name = _("Maandspecificatie report configuration")


@admin.register(SSDConfig)
class SSDConfigAdmin(SingletonModelAdmin):
    inlines = [MaandspecificatieConfigInline, JaaropgaveConfigInline]
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
        (_("Mijn Uitkeringen"), {"fields": ("mijn_uitkeringen_text",)}),
    )

    class Meta:
        verbose_name = _("SSD configuration")

    class Media:
        css = {"all": ("css/custom_admin.css",)}
