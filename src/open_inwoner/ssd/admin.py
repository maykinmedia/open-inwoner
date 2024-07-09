from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from open_inwoner.ckeditor5.widgets import CKEditorWidget

from .models import SSDConfig


class SSDAdminForm(forms.ModelForm):
    class Meta:
        model = SSDConfig
        fields = "__all__"
        widgets = {
            "jaaropgave_display_text": CKEditorWidget,
            "maandspecificatie_display_text": CKEditorWidget,
        }


@admin.register(SSDConfig)
class SSDConfigAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            _("SSD clients"),
            {
                "fields": (
                    "service",
                    "maandspecificatie_endpoint",
                    "jaaropgave_endpoint",
                    "bedrijfs_naam",
                    "applicatie_naam",
                    "gemeentecode",
                )
            },
        ),
        (_("Mijn Uitkeringen"), {"fields": ("mijn_uitkeringen_text",)}),
        (
            _("Maandspecificatie"),
            {
                "fields": (
                    "maandspecificatie_enabled",
                    "maandspecificatie_delta",
                    "maandspecificatie_available_from",
                    "maandspecificatie_display_text",
                    "maandspecificatie_pdf_comments",
                )
            },
        ),
        (
            _("Jaaropgave"),
            {
                "fields": (
                    "jaaropgave_enabled",
                    "jaaropgave_delta",
                    "jaaropgave_available_from",
                    "jaaropgave_display_text",
                    "jaaropgave_pdf_comments",
                )
            },
        ),
    )
    form = SSDAdminForm

    class Meta:
        verbose_name = _("SSD configuration")

    class Media:
        css = {"all": ("css/custom_admin.css",)}
