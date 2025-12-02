from typing import Generator

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site
from django.core import exceptions
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.urls import resolve
from django.urls.exceptions import Resolver404
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _

import structlog
from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline
from solo.admin import SingletonModelAdmin

from open_inwoner.utils.colors import ACCESSIBLE_CONTRAST_RATIO, get_contrast_ratio
from open_inwoner.utils.css import ALLOWED_PROPERTIES
from open_inwoner.utils.fields import CSSEditorWidget
from open_inwoner.utils.iteration import split
from open_inwoner.utils.logentry import user_action

from .models import CustomFontSet, SiteConfiguration, SiteConfigurationPage

logger = structlog.stdlib.get_logger(__name__)

permission_to_fieldset = {
    "configurations.siteconfig_fieldset_color": _("Color"),
    "configurations.siteconfig_fieldset_images": _("Images"),
    "configurations.siteconfig_fieldset_warning_banner": _("Warning banner"),
    "configurations.siteconfig_fieldset_page_texts": _("Page texts"),
    "configurations.siteconfig_fieldset_help_texts": _("Help texts"),
}


class CustomSiteAdmin(SiteAdmin):
    model = Site

    def has_add_permission(self, request):
        return not Site.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# re-register `Site` with our CustomSiteAdmin
admin.site.unregister(Site)
admin.site.register(Site, CustomSiteAdmin)


class SiteConfigurationPageInline(OrderedTabularInline):
    model = SiteConfigurationPage
    fields = (
        "cms_page",
        "order",
        "move_up_down_links",
    )
    readonly_fields = (
        "order",
        "move_up_down_links",
    )
    extra = 1
    ordering = ("order",)
    autocomplete_fields = ("cms_page",)


class FontConfigurationInline(admin.StackedInline):
    model = CustomFontSet
    verbose_name = "Fonts"
    min_num = 1
    can_delete = False


class SiteConfigurationAdminForm(forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = "__all__"
        widgets = {
            "extra_css": CSSEditorWidget,
            "custom_javascript_confirmed": forms.CheckboxInput(
                attrs={"style": "margin-bottom: 8px; margin-right: 8px;"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only update the widget if the field exists in the form
        if "custom_javascript" in self.fields:
            self.fields["custom_javascript"].widget.attrs.update({"accept": ".js"})

    def clean_custom_javascript(self):
        custom_javascript = self.cleaned_data.get("custom_javascript")

        if custom_javascript and not settings.ALLOW_CUSTOM_JS:
            raise ValidationError(
                _(
                    "Custom JavaScript upload is disabled. Contact your system administrator to enable this feature by setting the ALLOW_CUSTOM_JS flag to true."
                )
            )

        return custom_javascript

    def clean_redirect_to(self):
        redirect_to = self.cleaned_data["redirect_to"]

        if redirect_to:
            if redirect_to.startswith("/"):
                try:
                    resolve(redirect_to)
                except Resolver404:
                    raise ValidationError(_("The entered path is invalid.")) from None
            else:
                validate_url = URLValidator()
                try:
                    validate_url(redirect_to)
                except exceptions.ValidationError:
                    raise ValidationError(_("The entered url is invalid.")) from None

        return redirect_to

    def clean(self):
        cleaned_data = super().clean()
        custom_javascript = cleaned_data.get("custom_javascript")
        confirmed = cleaned_data.get("custom_javascript_confirmed")

        if custom_javascript and not confirmed:
            raise ValidationError(
                {
                    "custom_javascript_confirmed": _(
                        "You must confirm that you have reviewed the JavaScript code before uploading."
                    )
                }
            )
        return cleaned_data


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(OrderedInlineModelAdminMixin, SingletonModelAdmin):
    form = SiteConfigurationAdminForm
    save_on_top = True
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "enable_crawler_indexing",
                    "login_show",
                    "login_allow_registration",
                    "enable_eherkenning_for_eenmanszaak",
                    "login_2fa_sms",
                    "allow_messages_file_sharing",
                    "redirect_to",
                    "security_txt_redirect_target",
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
                    "email_logo",
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
                    "account_help_text",
                    "questionnaire_help_text",
                    "plan_help_text",
                ),
            },
        ),
        (
            _("Search"),
            {
                "fields": (
                    "search_enabled",
                    "hide_search_from_anonymous_users",
                    "search_help_text",
                    "search_zero_results_text",
                    "include_cms_pages_in_search_index",
                    "search_filter_categories",
                    "search_filter_tags",
                    "search_filter_organizations",
                )
            },
        ),
        (
            _("Notifications"),
            {
                "fields": (
                    "enable_notification_channel_choice",
                    "notifications_cases_enabled",
                    "notifications_messages_enabled",
                    "notifications_plans_enabled",
                    "notifications_actions_enabled",
                    "email_verification_required",
                    "email_verification_message",
                    "contact_phonenumber",
                    "contact_page",
                    "recipients_email_digest",
                )
            },
        ),
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
            _("Customer satisfaction survey"),
            {
                "fields": (
                    "kcm_survey_link_text",
                    "kcm_survey_link_url",
                ),
            },
        ),
        (
            _("Display options for anonymous users"),
            {"fields": ("hide_categories_from_anonymous_users",)},
        ),
        (
            _("Advanced display options"),
            {
                "classes": ["collapse"],
                "fields": (
                    "theme_stylesheet",
                    "extra_css",
                    "extra_css_allowed",
                    "custom_javascript_confirmed",
                    "custom_javascript",
                    "custom_javascript_file_info",
                ),
            },
        ),
        (_("Social media"), {"fields": ("display_social",)}),
        (_("Questions"), {"fields": ("contactmoment_contact_form_enabled",)}),
    )
    inlines = [SiteConfigurationPageInline, FontConfigurationInline]
    form = SiteConfigurationAdminForm

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

    def get_authorized_fieldsets(self, request, obj=None):
        """Return fieldsets based on user permissions"""
        if request is None:
            return super().get_fieldsets(request, obj)

        # Full admin access
        if request.user.is_superuser or request.user.has_perm(
            "configurations.change_siteconfiguration"
        ):
            return super().get_fieldsets(request, obj)

        # Partial admin access
        permitted_fieldsets = []
        all_fieldsets = super().get_fieldsets(request, obj)

        # Add fieldsets based on permissions
        for perm, fieldset_name in permission_to_fieldset.items():
            if request.user.has_perm(perm):
                for fieldset in all_fieldsets:
                    if fieldset[0] == fieldset_name:
                        permitted_fieldsets.append(fieldset)
                        break

        return permitted_fieldsets

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(self.get_authorized_fieldsets(request, obj))

        for i, (name, options) in enumerate(fieldsets):
            if name == _("Advanced display options"):
                fields = list(options["fields"])

                if not settings.ALLOW_CUSTOM_JS:
                    # Remove ALL JavaScript-related fields when disabled
                    js_fields_to_remove = [
                        "custom_javascript_confirmed",
                        "custom_javascript",
                        "custom_javascript_file_info",
                    ]
                    for js_field in js_fields_to_remove:
                        if js_field in fields:
                            fields.remove(js_field)

                    # Add ONLY the status field when disabled
                    fields.append("custom_javascript_status")
                else:
                    # When enabled, show all fields normally
                    # Find where to insert the status field
                    insert_index = len(fields)
                    js_fields = [
                        "custom_javascript_confirmed",
                        "custom_javascript",
                        "custom_javascript_file_info",
                    ]

                    for js_field in js_fields:
                        if js_field in fields:
                            insert_index = fields.index(js_field)
                            break

                    # Insert status field before JS fields when enabled
                    fields.insert(insert_index, "custom_javascript_status")

                new_options = options.copy()
                new_options["fields"] = tuple(fields)
                fieldsets[i] = (name, new_options)
                break

        return tuple(fieldsets)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [
            "extra_css_allowed",
            "custom_javascript_status",
        ]

        if settings.ALLOW_CUSTOM_JS:
            readonly_fields.append("custom_javascript_file_info")

        return readonly_fields

    @admin.display(description=_("Custom JavaScript Status"))
    def custom_javascript_status(self, obj):
        if settings.ALLOW_CUSTOM_JS:
            return format_html(
                '<span class="js-enabled">{}</span>', _("Custom JavaScript is enabled")
            )
        else:
            return format_html(
                '<span class="js-disabled">{}</span>',
                _("Custom JavaScript is disabled. Contact your system administrator."),
            )

    @admin.display(description=_("Current upload"))
    def custom_javascript_file_info(self, obj):
        if obj.custom_javascript:
            try:
                if obj.custom_javascript.storage.exists(obj.custom_javascript.name):
                    if settings.ALLOW_CUSTOM_JS:
                        size_kb = obj.custom_javascript.size / 1024
                        # Extract just the filename from the full path
                        filename = obj.custom_javascript.name.split("/")[-1]
                        # Filename extraction
                        if "_" in filename and filename.endswith(".js"):
                            base_name = filename.split("_")[0]
                            original_filename = f"{base_name}.js"
                        else:
                            original_filename = filename

                        return format_html(
                            "{}: {} KB",
                            original_filename,  # Show filename
                            round(size_kb, 1),  # Show size
                        )
                    else:
                        return _("File uploaded but feature is disabled")
                else:
                    return _("File missing from storage")
            except Exception:
                logger.exception(
                    "Unable to render custom javascript_file_info admin field"
                )
                return _("Error accessing file")

        return _("No file uploaded")

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

    def _get_fields_from_fieldsets(
        self, fieldset_names: list[str]
    ) -> Generator[str, None, None]:
        """Get all fields from the specified fieldsets"""
        for name, opts in super().get_fieldsets(None):
            if name in fieldset_names:
                fields_ = opts["fields"]
                # process nested fields
                for f in fields_:
                    if isinstance(f, (list, tuple)):
                        yield from f
                    else:
                        yield f

    def save_model(self, request, obj, form, change):
        self.report_contrast_ratio(request, obj)

        # Users with full permissions can save everything
        if request.user.is_superuser or request.user.has_perm(
            "configurations.change_siteconfiguration"
        ):
            return super().save_model(request, obj, form, change)

        # Users with partial permissions
        allowed_fieldset_names = []
        for perm, fieldset_name in permission_to_fieldset.items():
            if request.user.has_perm(perm):
                allowed_fieldset_names.append(fieldset_name)

        if not allowed_fieldset_names:
            raise exceptions.PermissionDenied(
                _("You do not have the rights to make changes")
            )

        # Get allowed fields from permitted fieldsets
        allowed_fields = self._get_fields_from_fieldsets(allowed_fieldset_names)

        # Check if user is trying to modify fields they don't have permission for
        unauthorized_fields = [
            field for field in form.changed_data if field not in allowed_fields
        ]

        if unauthorized_fields:
            user_action(
                request,
                request.user,
                "Unauthorized attempt to modify SiteConfiguration",
            )
            raise exceptions.PermissionDenied(
                _("You do not have permission to modify these fields")
            )

        return super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        # For superusers and users with full permissions, allow full access
        if request.user.is_superuser or request.user.has_perm(
            "configurations.change_siteconfiguration"
        ):
            return True

        # Check partial editing permissions
        return any(request.user.has_perm(perm) for perm in permission_to_fieldset)
