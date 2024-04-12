from django.conf import settings

from django_setup_configuration.configuration import BaseConfigurationStep

from open_inwoner.configurations.models import SiteConfiguration


class SiteConfigurationStep(BaseConfigurationStep):
    """
    Set up general configuration ("Algemene configuratie")
    """

    verbose_name = "Site configuration"
    required_settings = [
        "SITE_NAME",
        "SITE_PRIMARY_COLOR",
        "SITE_SECONDARY_COLOR",
        "SITE_ACCENT_COLOR",
    ]
    setting_to_config = {
        "SITE_NAME": "name",
        "SITE_PRIMARY_COLOR": "primary_color",
        "SITE_SECONDARY_COLOR": "secondary_color",
        "SITE_ACCENT_COLOR": "accent_color",
        "SITE_PRIMARY_FONT_COLOR": "primary_font_color",
        "SITE_SECONDARY_FONT_COLOR": "secondary_font_color",
        "SITE_ACCENT_FONT_COLOR": "accent_font_color",
        "SITE_WARNING_BANNER_ENABLED": "warning_banner_enabled",
        "SITE_WARNING_BANNER_TEXT": "warning_banner_text",
        "SITE_WARNING_BANNER_BACKGROUND_COLOR": "warning_banner_background_color",
        "SITE_WARNING_BANNER_FONT_COLOR": "warning_banner_font_color",
        "SITE_LOGIN_SHOW": "login_show",
        "SITE_LOGIN_ALLOW_REGISTRATION": "login_allow_registration",
        "SITE_LOGIN_2FA_SMS": "login_2fa_sms",
        "SITE_LOGIN_TEXT": "login_text",
        "SITE_REGISTRATION_TEXT": "registration_text",
        "SITE_HOME_WELCOME_TITLE": "home_welcome_title",
        "SITE_HOME_WELCOME_INTRO": "home_welcome_intro",
        "SITE_HOME_THEME_TITLE": "home_theme_title",
        "SITE_HOME_THEME_INTRO": "home_theme_intro",
        "SITE_THEME_TITLE": "theme_title",
        "SITE_THEME_INTRO": "theme_intro",
        "SITE_HOME_MAP_TITLE": "home_map_title",
        "SITE_HOME_MAP_INTRO": "home_map_intro",
        "SITE_HOME_QUESTIONNAIRE_TITLE": "home_questionnaire_title",
        "SITE_HOME_QUESTIONNAIRE_INTRO": "home_questionnaire_intro",
        "SITE_HOME_PRODUCT_FINDER_TITLE": "home_product_finder_title",
        "SITE_HOME_PRODUCT_FINDER_INTRO": "home_product_finder_intro",
        "SITE_SELECT_QUESTIONNAIRE_TITLE": "select_questionnaire_title",
        "SITE_SELECT_QUESTIONNAIRE_INTRO": "select_questionnaire_intro",
        "SITE_PLANS_INTRO": "plans_intro",
        "SITE_PLANS_NO_PLANS_MESSAGE": "plans_no_plans_message",
        "SITE_PLANS_EDIT_MESSAGE": "plans_edit_message",
        "SITE_FOOTER_LOGO_TITLE": "footer_logo_title",
        "SITE_FOOTER_LOGO_URL": "footer_logo_url",
        "SITE_HOME_HELP_TEXT": "home_help_text",
        "SITE_THEME_HELP_TEXT": "theme_help_text",
        "SITE_PRODUCT_HELP_TEXT": "product_help_text",
        "SITE_SEARCH_HELP_TEXT": "search_help_text",
        "SITE_ACCOUNT_HELP_TEXT": "account_help_text",
        "SITE_QUESTIONNAIRE_HELP_TEXT": "questionnaire_help_text",
        "SITE_PLAN_HELP_TEXT": "plan_help_text",
        "SITE_SEARCH_FILTER_CATEGORIES": "search_filter_categories",
        "SITE_SEARCH_FILTER_TAGS": "search_filter_tags",
        "SITE_SEARCH_FILTER_ORGANIZATIONS": "search_filter_organizations",
        "SITE_EMAIL_NEW_MESSAGE": "email_new_message",
        "SITE_RECIPIENTS_EMAIL_DIGEST": "recipients_email_digest",
        "SITE_CONTACT_PHONENUMBER": "contact_phonenumber",
        "SITE_CONTACT_PAGE": "contact_page",
        "SITE_GTM_CODE": "gtm_code",
        "SITE_GA_CODE": "ga_code",
        "SITE_MATOMO_URL": "matomo_url",
        "SITE_MATOMO_SITE_ID": "matomo_site_id",
        "SITE_SITEIMPROVE_ID": "siteimprove_id",
        "SITE_COOKIE_INFO_TEXT": "cookie_info_text",
        "SITE_COOKIE_LINK_TEXT": "cookie_link_text",
        "SITE_COOKIE_LINK_URL": "cookie_link_url",
        "SITE_KCM_SURVEY_LINK_TEXT": "kcm_survey_link_text",
        "SITE_KCM_SURVEY_LINK_URL": "kcm_survey_link_url",
        "SITE_OPENID_CONNECT_LOGIN_TEXT": "openid_connect_login_text",
        "SITE_OPENID_DISPLAY": "openid_display",
        "SITE_REDIRECT_TO": "redirect_to",
        "SITE_ALLOW_MESSAGES_FILE_SHARING": "allow_messages_file_sharing",
        "SITE_HIDE_CATEGORIES_FROM_ANONYMOUS_USERS": "hide_categories_from_anonymous_users",
        "SITE_HIDE_SEARCH_FROM_ANONYMOUS_USERS": "hide_search_from_anonymous_users",
        "SITE_DISPLAY_SOCIAL": "display_social",
        "SITE_EHERKENNING_ENABLED": "eherkenning_enabled",
    }

    def is_configured(self):
        config = SiteConfiguration.get_solo()

        for required_setting in self.required_settings:
            config_field = self.setting_to_config[required_setting]
            if not getattr(config, config_field, None):
                return False
        return True

    def configure(self):
        config = SiteConfiguration.get_solo()

        for key, value in self.setting_to_config.items():
            setting = getattr(settings, key)
            if setting is not None:
                setattr(config, value, setting)
        config.save()

    def test_configuration(self):
        ...
