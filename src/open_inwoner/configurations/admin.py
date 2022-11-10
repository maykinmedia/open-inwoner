from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import ugettext_lazy as _

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline
from solo.admin import SingletonModelAdmin

from open_inwoner.ckeditor5.widgets import CKEditorWidget

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
        (
            None,
            {
                "fields": (
                    "name",
                    "login_show",
                    "login_allow_registration",
                    "show_cases",
                    "show_product_finder",
                )
            },
        ),
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
            _("Page texts"),
            {
                "classes": ("collapse",),
                "fields": (
                    "login_text",
                    "home_welcome_title",
                    "home_welcome_intro",
                    "home_theme_title",
                    "home_theme_intro",
                    "home_map_title",
                    "home_map_intro",
                    "theme_title",
                    "theme_intro",
                    "home_questionnaire_title",
                    "home_questionnaire_subtitle",
                    "select_questionnaire_title",
                    "select_questionnaire_subtitle",
                ),
            },
        ),
        (
            _("Help texts"),
            {
                "classes": ("collapse",),
                "fields": (
                    "home_help_text",
                    "theme_help_text",
                    "product_help_text",
                    "search_help_text",
                    "account_help_text",
                    "questionnaire_help_text",
                    "plan_help_text",
                ),
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
        (_("Emails"), {"fields": ("email_new_message",)}),
        (
            _("Openid Connect"),
            {
                "fields": (
                    "openid_connect_logo",
                    "openid_connect_login_text",
                )
            },
        ),
        (
            _("Analytics"),
            {"fields": ("gtm_code", "ga_code", "matomo_url", "matomo_site_id")},
        ),
    )
    inlines = [SiteConfigurationPageInline]


class FlatPageAdminForm(FlatpageForm):
    class Meta:
        model = FlatPage
        fields = "__all__"
        widgets = {"content": CKEditorWidget}


class CustomFlatPageAdmin(FlatPageAdmin):
    form = FlatPageAdminForm


# Re-register FlatPageAdmin
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, CustomFlatPageAdmin)
