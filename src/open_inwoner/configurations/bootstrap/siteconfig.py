from django.core.exceptions import ValidationError

from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed

from open_inwoner.configurations.models import SiteConfiguration


def _resolve_default(field_name: str) -> str:
    """
    Resolve a CharField's translated default to a plain string.

    DjangoModelRef defaults must be concrete values: pydantic validates field
    defaults against their declared type, and a `django.utils.functional.lazy`
    proxy (as produced by `gettext_lazy`) is not a `str` instance.
    """
    return str(SiteConfiguration._meta.get_field(field_name).default)


# Fields that are not configurable through this step, because they require an
# uploaded file (logos, favicon, custom stylesheet/javascript, the JS "I have
# reviewed this" checkbox) or point at CMS pages managed elsewhere. Keep this in
# sync with SiteConfigurationModel: AppHookMappingTests-style reflection tests
# in the test suite assert every other SiteConfiguration field is covered.
EXCLUDED_FIELDS = frozenset(
    {
        "logo",
        "hero_image_login",
        "footer_logo",
        "email_logo",
        "favicon",
        "openid_connect_logo",
        "theme_stylesheet",
        "custom_javascript",
        "custom_javascript_confirmed",
        "cms_pages",
    }
)


class SiteConfigurationModel(ConfigurationModel):
    """General site configuration ("Algemene configuratie")."""

    # Django field types without an exact match in DjangoModelRef's type mapping
    # need an explicit annotation; everything else comes from django_model_refs below.
    primary_color: str = DjangoModelRef(SiteConfiguration, "primary_color")
    secondary_color: str = DjangoModelRef(SiteConfiguration, "secondary_color")
    accent_color: str = DjangoModelRef(SiteConfiguration, "accent_color")
    warning_banner_background_color: str = DjangoModelRef(
        SiteConfiguration, "warning_banner_background_color"
    )
    warning_banner_font_color: str = DjangoModelRef(
        SiteConfiguration, "warning_banner_font_color"
    )
    extra_css: str = DjangoModelRef(SiteConfiguration, "extra_css")
    recipients_email_digest: list[str] = DjangoModelRef(
        SiteConfiguration, "recipients_email_digest"
    )
    # Rich-text fields accept an HTML fragment, matching what the admin's
    # ProseMirror widget produces; it is converted to the field's internal
    # document format on assignment.
    warning_banner_text: str | None = DjangoModelRef(
        SiteConfiguration, "warning_banner_text"
    )
    login_text: str | None = DjangoModelRef(SiteConfiguration, "login_text")
    search_zero_results_text: str | None = DjangoModelRef(
        SiteConfiguration, "search_zero_results_text"
    )

    class Meta:
        django_model_refs = {
            SiteConfiguration: [
                "name",
                "primary_font_color",
                "secondary_font_color",
                "accent_font_color",
                "warning_banner_enabled",
                "login_show",
                "login_allow_registration",
                "login_2fa_sms",
                "enable_eherkenning_for_eenmanszaak",
                "registration_text",
                "home_welcome_title",
                "home_welcome_intro",
                "home_theme_title",
                "home_theme_intro",
                "theme_title",
                "theme_intro",
                "home_map_title",
                "home_map_intro",
                "home_questionnaire_title",
                "home_questionnaire_intro",
                "home_product_finder_title",
                "home_product_finder_intro",
                "select_questionnaire_title",
                "select_questionnaire_intro",
                "plans_intro",
                "plans_no_plans_message",
                "plans_edit_message",
                "footer_logo_title",
                "footer_logo_url",
                "home_help_text",
                "theme_help_text",
                "product_help_text",
                "account_help_text",
                "questionnaire_help_text",
                "plan_help_text",
                "search_enabled",
                "hide_search_from_anonymous_users",
                "search_help_text",
                "include_cms_pages_in_search_index",
                "search_filter_categories",
                "search_filter_tags",
                "search_filter_organizations",
                "enable_notification_channel_choice",
                "notifications_cases_enabled",
                "notifications_messages_enabled",
                "notifications_plans_enabled",
                "notifications_actions_enabled",
                "email_verification_required",
                "email_verification_message",
                "contact_phonenumber",
                "contact_page",
                "gtm_code",
                "ga_code",
                "matomo_url",
                "matomo_site_id",
                "siteimprove_id",
                "cookie_info_text",
                "cookie_link_text",
                "cookie_link_url",
                "kcm_survey_link_text",
                "kcm_survey_link_url",
                "openid_connect_login_text",
                "openid_display",
                "redirect_to",
                "allow_messages_file_sharing",
                "hide_categories_from_anonymous_users",
                "display_social",
                "eherkenning_enabled",
                "contactmoment_contact_form_enabled",
                "enable_crawler_indexing",
                "security_txt_redirect_target",
                "enable_virus_scan",
                "clamav_host",
                "clamav_port",
                "clamav_timeout",
            ]
        }
        # These fields default to a gettext_lazy() value, which pydantic
        # rejects as a default because it is not a plain `str`. Resolve each
        # to a plain string instead.
        extra_kwargs = {
            field: {"default": _resolve_default(field)}
            for field in (
                "home_welcome_title",
                "home_theme_title",
                "theme_title",
                "home_map_title",
                "home_questionnaire_title",
                "home_product_finder_title",
                "select_questionnaire_title",
                "plans_no_plans_message",
                "plans_edit_message",
            )
        }


class SiteConfigurationStep(BaseConfigurationStep):
    """
    Configures general site settings ("Algemene configuratie"), the single
    solo ``SiteConfiguration`` record that most of the site's copy, branding
    and feature toggles are drawn from.

    Every field this step manages is overwritten on every run, using its
    default when the YAML source doesn't set it: changes made to them in the
    admin do not survive a re-run. ``name`` has no sensible default and must
    always be provided.

    Fields that require an uploaded file (logos, favicon, the custom
    stylesheet/javascript and its confirmation checkbox) or link to CMS pages
    are not configurable through this step; set those up in the admin.
    """

    verbose_name = "Site configuration"
    enable_setting = "site_config_enable"
    namespace = "site_config"
    config_model = SiteConfigurationModel

    def execute(self, model: SiteConfigurationModel) -> None:
        config = SiteConfiguration.get_solo()

        for field, value in model.model_dump().items():
            setattr(config, field, value)

        try:
            # save() also lives here: SiteConfiguration.save() runs extra_css
            # through a CSS cleaner, which could in principle raise too
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                f"Something went wrong while saving SiteConfiguration: {exc}"
            ) from exc
