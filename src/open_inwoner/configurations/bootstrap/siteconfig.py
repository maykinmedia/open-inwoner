from django.conf import settings

from django_setup_configuration.config_settings import ConfigSettings
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed

from open_inwoner.configurations.admin import SiteConfigurationAdminForm
from open_inwoner.configurations.models import SiteConfiguration

from .utils import convert_setting_to_model_field_name, log_form_errors


class SiteConfigurationStep(BaseConfigurationStep):
    """
    Set up general configuration ("Algemene configuratie")
    """

    verbose_name = "Site configuration step"
    config_settings = ConfigSettings(
        enable_setting="SITE_CONFIG_ENABLE",
        namespace="SITE",
        file_name="siteconfig",
        models=[SiteConfiguration],
        required_settings=[
            "SITE_NAME",
        ],
        optional_settings=[
            "SITE_ACCENT_COLOR",
            "SITE_ACCENT_FONT_COLOR",
            "SITE_ACCOUNT_HELP_TEXT",
            "SITE_ALLOW_MESSAGES_FILE_SHARING",
            "SITE_CONTACTMOMENT_CONTACT_FORM_ENABLED",
            "SITE_CONTACT_PAGE",
            "SITE_CONTACT_PHONENUMBER",
            "SITE_COOKIE_INFO_TEXT",
            "SITE_COOKIE_LINK_TEXT",
            "SITE_COOKIE_LINK_URL",
            "SITE_DISPLAY_SOCIAL",
            "SITE_EHERKENNING_ENABLED",
            "SITE_EMAIL_NEW_MESSAGE",
            "SITE_EMAIL_VERIFICATION_REQUIRED",
            "SITE_FOOTER_LOGO_TITLE",
            "SITE_FOOTER_LOGO_URL",
            "SITE_GA_CODE",
            "SITE_GTM_CODE",
            "SITE_HIDE_CATEGORIES_FROM_ANONYMOUS_USERS",
            "SITE_HIDE_SEARCH_FROM_ANONYMOUS_USERS",
            "SITE_HOME_HELP_TEXT",
            "SITE_HOME_MAP_INTRO",
            "SITE_HOME_MAP_TITLE",
            "SITE_HOME_PRODUCT_FINDER_INTRO",
            "SITE_HOME_PRODUCT_FINDER_TITLE",
            "SITE_HOME_QUESTIONNAIRE_INTRO",
            "SITE_HOME_QUESTIONNAIRE_TITLE",
            "SITE_HOME_THEME_INTRO",
            "SITE_HOME_THEME_TITLE",
            "SITE_HOME_WELCOME_INTRO",
            "SITE_HOME_WELCOME_TITLE",
            "SITE_KCM_SURVEY_LINK_TEXT",
            "SITE_KCM_SURVEY_LINK_URL",
            "SITE_LOGIN_2FA_SMS",
            "SITE_LOGIN_ALLOW_REGISTRATION",
            "SITE_LOGIN_SHOW",
            "SITE_LOGIN_TEXT",
            "SITE_MATOMO_SITE_ID",
            "SITE_MATOMO_URL",
            "SITE_NOTIFICATIONS_ACTIONS_ENABLED",
            "SITE_NOTIFICATIONS_CASES_ENABLED",
            "SITE_NOTIFICATIONS_MESSAGES_ENABLED",
            "SITE_NOTIFICATIONS_PLANS_ENABLED",
            "SITE_OPENID_CONNECT_LOGIN_TEXT",
            "SITE_OPENID_DISPLAY",
            "SITE_PLANS_EDIT_MESSAGE",
            "SITE_PLANS_INTRO",
            "SITE_PLANS_NO_PLANS_MESSAGE",
            "SITE_PLAN_HELP_TEXT",
            "SITE_PRIMARY_COLOR",
            "SITE_PRIMARY_FONT_COLOR",
            "SITE_PRODUCT_HELP_TEXT",
            "SITE_QUESTIONNAIRE_HELP_TEXT",
            "SITE_RECIPIENTS_EMAIL_DIGEST",
            "SITE_REDIRECT_TO",
            "SITE_REGISTRATION_TEXT",
            "SITE_SEARCH_FILTER_CATEGORIES",
            "SITE_SEARCH_FILTER_ORGANIZATIONS",
            "SITE_SEARCH_FILTER_TAGS",
            "SITE_SEARCH_HELP_TEXT",
            "SITE_SECONDARY_COLOR",
            "SITE_SECONDARY_FONT_COLOR",
            "SITE_SELECT_QUESTIONNAIRE_INTRO",
            "SITE_SELECT_QUESTIONNAIRE_TITLE",
            "SITE_SITEIMPROVE_ID",
            "SITE_THEME_HELP_TEXT",
            "SITE_THEME_INTRO",
            "SITE_THEME_TITLE",
            "SITE_WARNING_BANNER_BACKGROUND_COLOR",
            "SITE_WARNING_BANNER_ENABLED",
            "SITE_WARNING_BANNER_FONT_COLOR",
            "SITE_WARNING_BANNER_TEXT",
        ],
    )

    def is_enabled(self):
        return getattr(settings, self.config_settings.enable_setting, False)

    def is_configured(self):
        config = SiteConfiguration.get_solo()

        for required_setting in self.config_settings.required_settings:
            field_name = convert_setting_to_model_field_name(
                required_setting, self.config_settings.namespace
            )
            if not getattr(config, field_name, None):
                return False

        return True

    def configure(self):
        if not self.is_enabled():
            return

        config = SiteConfiguration.get_solo()

        # use model defaults for form data
        form_data = {
            field.name: getattr(config, field.name)
            for field in SiteConfiguration._meta.fields
        }

        all_settings = (
            self.config_settings.required_settings
            + self.config_settings.optional_settings
        )

        for setting in all_settings:
            value = getattr(settings, setting, None)
            if value is not None:
                field_name = convert_setting_to_model_field_name(
                    setting, self.config_settings.namespace
                )
                form_data[field_name] = value

        # validate settings with admin form
        form = SiteConfigurationAdminForm(data=form_data)
        if not form.is_valid():
            log_form_errors(self, form)
            raise ConfigurationRunFailed(
                f"Something went wrong while saving configuration: {form.errors}"
            )

        form.save()

    def test_configuration(self):
        ...
