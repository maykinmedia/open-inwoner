from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from solo.admin import SingletonModelAdmin

from .models import SiteConfiguration


@admin.register(SiteConfiguration)
class SiteConfigurarionAdmin(SingletonModelAdmin):
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
    )
