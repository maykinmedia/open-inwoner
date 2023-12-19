from django import forms
from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected as default_delete_selected
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site
from django.core import exceptions
from django.core.validators import URLValidator
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline
from solo.admin import SingletonModelAdmin

from open_inwoner.ckeditor5.widgets import CKEditorWidget

from ..utils.colors import ACCESSIBLE_CONTRAST_RATIO, get_contrast_ratio
from ..utils.css import ALLOWED_PROPERTIES
from ..utils.fields import CSSEditorWidget
from ..utils.iteration import split
from .models import SiteConfiguration, SiteConfigurationPage


@admin.action(description=_("Delete selected websites"))
def delete_selected(modeladmin, request, queryset):
    """
    Override `delete_selected` action to prevent accidental deletion of all websites
    """
    if queryset.count() == Site.objects.all().count():
        messages.add_message(
            request,
            messages.WARNING,
            _("You cannot delete all websites; at least one site must remain."),
        )
        return HttpResponseRedirect(reverse("admin:sites_site_changelist"))
    return default_delete_selected(modeladmin, request, queryset)


class CustomSiteAdmin(SiteAdmin):
    """
    Overrides `SiteAdmin` to prevent deletion of last website
    """

    model = Site
    actions = [delete_selected]

    def delete_model(self, request, obj):
        if self.model.objects.count() < 2:
            messages.add_message(
                request, messages.WARNING, _("You cannot delete the last site.")
            )
            return redirect("admin:sites_site_changelist")
        else:
            super().delete_model(request, obj)


# re-register `Site` with our CustomSiteAdmin
admin.site.unregister(Site)
admin.site.register(Site, CustomSiteAdmin)


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


class SiteConfigurarionAdminForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = "__all__"
        widgets = {
            "extra_css": CSSEditorWidget,
        }

    def clean_redirect_to(self):
        redirect_to = self.cleaned_data["redirect_to"]

        if redirect_to:
            if redirect_to.startswith("/"):
                try:
                    resolve(redirect_to)
                except Resolver404:
                    raise ValidationError(_("The entered path is invalid."))
            else:
                validate_url = URLValidator()
                try:
                    validate_url(redirect_to)
                except exceptions.ValidationError:
                    raise ValidationError(_("The entered url is invalid."))

        return redirect_to


@admin.register(SiteConfiguration)
class SiteConfigurarionAdmin(OrderedInlineModelAdminMixin, SingletonModelAdmin):
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "login_show",
                    "login_allow_registration",
                    "login_2fa_sms",
                    "allow_messages_file_sharing",
                    "redirect_to",
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
                    "theme_stylesheet",
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
                )
            },
        ),
        (
            _("Warning banner"),
            {
                "classes": ("collapse",),
                "fields": (
                    "warning_banner_enabled",
                    "warning_banner_text",
                    "warning_banner_background_color",
                    "warning_banner_font_color",
                ),
            },
        ),
        (
            _("Page texts"),
            {
                "classes": ("collapse",),
                "fields": (
                    "login_text",
                    "registration_text",
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
            _("Search filter options"),
            {
                "fields": (
                    "search_filter_categories",
                    "search_filter_tags",
                    "search_filter_organizations",
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
                    "openid_display",
                )
            },
        ),
        (
            _("Authentication"),
            {"fields": ("eherkenning_enabled",)},
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
        (
            _("Cookie consent"),
            {
                "fields": (
                    "cookie_info_text",
                    "cookie_link_text",
                    "cookie_link_url",
                ),
            },
        ),
        (
            _("Display options for anonymous users"),
            {
                "fields": (
                    "hide_categories_from_anonymous_users",
                    "hide_search_from_anonymous_users",
                )
            },
        ),
        (
            _("Advanced display options"),
            {
                "classes": ["collapse"],
                "fields": (
                    "extra_css",
                    "extra_css_allowed",
                ),
            },
        ),
        (_("Social media"), {"fields": ("display_social",)}),
    )
    inlines = [SiteConfigurationPageInline]
    form = SiteConfigurarionAdminForm

    readonly_fields = [
        "extra_css_allowed",
    ]

    @admin.display(
        description=_("Allowed CSS properties"),
    )
    def extra_css_allowed(self, obj):
        columns = split(ALLOWED_PROPERTIES, 4)

        def _get_column(props):
            return format_html_join("", "{}<br>", ((p,) for p in props))

        return format_html(
            '<div class="css-properties-table">\n{}\n</div>',
            format_html_join(
                "\n",
                '<div class="css-properties-table__column">{}</div>',
                ((_get_column(c),) for c in columns),
            ),
        )

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
        check_contrast_ratio(
            _("Warning banner background color"),
            obj.warning_banner_background_color,
            _("Warning banner font color"),
            obj.warning_banner_font_color,
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
