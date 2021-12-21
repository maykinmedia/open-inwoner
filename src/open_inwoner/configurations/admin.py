from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from solo.admin import SingletonModelAdmin

from open_inwoner.ckeditor.widgets import CKEditorWidget

from .models import SiteConfiguration


class SiteConfigurationAdminForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = "__all__"
        widgets = {"footer_visitor_mail": CKEditorWidget}


@admin.register(SiteConfiguration)
class SiteConfigurarionAdmin(SingletonModelAdmin):
    form = SiteConfigurationAdminForm
    fieldsets = (
        (None, {"fields": ("name", "login_allow_registration")}),
        (
            _("Color"),
            {
                "fields": (
                    "primary_color",
                    "secondary_color",
                    "accent_color",
                )
            },
        ),
        (
            _("Font"),
            {
                "fields": (
                    "primary_font_color",
                    "secondary_font_color",
                    "accent_font_color",
                )
            },
        ),
        (
            _("Images"),
            {
                "fields": (
                    "logo",
                    "hero_image_login",
                )
            },
        ),
        (
            _("Text"),
            {
                "fields": (
                    "login_text",
                    "home_welcome_title",
                    "home_welcome_intro",
                    "theme_title",
                    "theme_intro",
                    "home_map_title",
                    "home_map_intro",
                )
            },
        ),
        (
            _("Footer"),
            {"fields": ("footer_visitor_mail",)},
        ),
    )
