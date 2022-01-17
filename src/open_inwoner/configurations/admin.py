from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline
from solo.admin import SingletonModelAdmin

from .models import SiteConfiguration, SiteConfigurationPage


class SiteConfigurationPageInline(OrderedTabularInline):
    model = SiteConfigurationPage
    fields = (
        "flatpage",
        "order",
        "move_up_down_links",
    )
    readonly_fields = (
        "order",
        "move_up_down_links",
    )
    extra = 1
    ordering = ("order",)
    autocomplete_fields = ("flatpage",)


@admin.register(SiteConfiguration)
class SiteConfigurarionAdmin(OrderedInlineModelAdminMixin, SingletonModelAdmin):
    fieldsets = (
        (None, {"fields": ("name", "login_allow_registration")}),
        (
            _("Color"),
            {
                "fields": (
                    "primary_color",
                    "secondary_color",
                    "accent_color",
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
                    "home_theme_title",
                    "home_theme_intro",
                    "theme_title",
                    "theme_intro",
                    "home_map_title",
                    "home_map_intro",
                )
            },
        ),
        (
            _("Footer addresses"),
            {
                "fields": (
                    "footer_visiting_title",
                    "footer_visiting_intro",
                    "footer_visiting_map",
                    "footer_mailing_title",
                    "footer_mailing_intro",
                )
            },
        ),
    )
    inlines = [SiteConfigurationPageInline]
