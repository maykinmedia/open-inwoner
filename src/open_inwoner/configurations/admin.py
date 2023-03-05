from django.contrib import admin, messages
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import ugettext_lazy as _

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline
from solo.admin import SingletonModelAdmin

from open_inwoner.ckeditor5.widgets import CKEditorWidget

from ..utils.colors import ACCESSIBLE_CONTRAST_RATIO, get_contrast_ratio
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
                    "show_plans",
                    "show_actions",
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
                    "footer_logo",
                    "footer_logo_title",
                    "footer_logo_url",
                    "hero_image_login",
                    "favicon",
                    "plans_banner",
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
                    "home_product_finder_title",
                    "home_product_finder_intro",
                    "theme_title",
                    "theme_intro",
                    "home_questionnaire_title",
                    "home_questionnaire_intro",
                    "select_questionnaire_title",
                    "select_questionnaire_intro",
                    "plans_intro",
                    "plans_no_plans_message",
                    "plans_edit_message",
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
            {
                "fields": (
                    "gtm_code",
                    "ga_code",
                    "matomo_url",
                    "matomo_site_id",
                    "siteimprove_id",
                )
            },
        ),
    )
    inlines = [SiteConfigurationPageInline]

    def report_contrast_ratio(self, request, obj):
        def check_contrast_ratio(label1, color1, label2, color2, expected_ratio):
            ratio = get_contrast_ratio(color1, color2)
            if ratio < expected_ratio:
                message = "'{label1}' ({color1}) en '{label2}' ({color2}) hebben niet genoeg contrast: {ratio}:1 waar {expected}:1 wordt verwacht.".format(
                    label1=label1,
                    color1=color1,
                    label2=label2,
                    color2=color2,
                    ratio=round(ratio, 1),
                    expected=expected_ratio,
                )
                self.message_user(request, message, messages.WARNING)

        check_contrast_ratio(
            _("Primary color"),
            obj.primary_color,
            _("Primary font color"),
            obj.primary_font_color,
            ACCESSIBLE_CONTRAST_RATIO,
        )
        check_contrast_ratio(
            _("Secondary color"),
            obj.secondary_color,
            _("Secondary font color"),
            obj.secondary_font_color,
            ACCESSIBLE_CONTRAST_RATIO,
        )
        check_contrast_ratio(
            _("Accent color"),
            obj.accent_color,
            _("Accent font color"),
            obj.accent_font_color,
            ACCESSIBLE_CONTRAST_RATIO,
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.report_contrast_ratio(request, obj)


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
