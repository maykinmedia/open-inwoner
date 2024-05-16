from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from open_inwoner.configurations.choices import ColorTypeChoices
from open_inwoner.configurations.models import SiteConfiguration

from ...bootstrap.siteconfig import SiteConfigurationStep


@override_settings(
    SITE_NAME="My site",
    SITE_PRIMARY_COLOR="#AAAAAA",
    SITE_SECONDARY_COLOR="#000000",
    SITE_ACCENT_COLOR="#000000",
    SITE_PRIMARY_FONT_COLOR="#111111",
    SITE_SECONDARY_FONT_COLOR="#222222",
    SITE_ACCENT_FONT_COLOR="#333333",
    SITE_WARNING_BANNER_ENABLED="True",
    SITE_WARNING_BANNER_TEXT="warning banner text",
    SITE_WARNING_BANNER_BACKGROUND_COLOR="#444444",
    SITE_WARNING_BANNER_FONT_COLOR="#555555",
    SITE_LOGIN_SHOW=False,
    SITE_LOGIN_ALLOW_REGISTRATION=True,
    SITE_LOGIN_2FA_SMS=True,
    SITE_LOGIN_TEXT="login text",
    SITE_REGISTRATION_TEXT="registration text",
    SITE_HOME_WELCOME_TITLE="welcome title",
    SITE_HOME_WELCOME_INTRO="welcome intro",
    SITE_HOME_THEME_TITLE="home theme title",
    SITE_HOME_THEME_INTRO="home theme intro",
    SITE_THEME_TITLE="theme title",
    SITE_THEME_INTRO="theme intro",
    SITE_HOME_MAP_TITLE="home map title",
    SITE_HOME_MAP_INTRO="home map intro",
    SITE_HOME_QUESTIONNAIRE_TITLE="home questionnaire title",
    SITE_HOME_QUESTIONNAIRE_INTRO="home questionnaire intro",
    SITE_HOME_PRODUCT_FINDER_TITLE="home product finder title",
    SITE_HOME_PRODUCT_FINDER_INTRO="home product finder intro",
    SITE_SELECT_QUESTIONNAIRE_TITLE="select questionnaire title",
    SITE_SELECT_QUESTIONNAIRE_INTRO="select questionnaire intro",
    SITE_PLANS_INTRO="plans intro",
    SITE_PLANS_NO_PLANS_MESSAGE="plans no plans_message",
    SITE_PLANS_EDIT_MESSAGE="plans edit message",
    SITE_FOOTER_LOGO_TITLE="footer logo title",
    SITE_FOOTER_LOGO_URL="footer logo url",
    SITE_HOME_HELP_TEXT="home help text",
    SITE_THEME_HELP_TEXT="theme help text",
    SITE_PRODUCT_HELP_TEXT="product help text",
    SITE_SEARCH_HELP_TEXT="search help text",
    SITE_ACCOUNT_HELP_TEXT="account help text",
    SITE_QUESTIONNAIRE_HELP_TEXT="questionnaire help text",
    SITE_PLAN_HELP_TEXT="plan help text",
    SITE_SEARCH_FILTER_CATEGORIES=False,
    SITE_SEARCH_FILTER_TAGS=False,
    SITE_SEARCH_FILTER_ORGANIZATIONS=False,
    SITE_EMAIL_NEW_MESSAGE=False,
    SITE_EMAIL_VERIFICATION_REQUIRED=False,
    SITE_RECIPIENTS_EMAIL_DIGEST=["test1@test.nl", "test2@test.nl"],
    SITE_CONTACT_PHONENUMBER="12345",
    SITE_CONTACT_PAGE="https://test.test",
    SITE_GTM_CODE="gtm code",
    SITE_GA_CODE="ga code",
    SITE_MATOMO_URL="matomo url",
    SITE_MATOMO_SITE_ID=88,
    SITE_SITEIMPROVE_ID="88",
    SITE_COOKIE_INFO_TEXT="cookie info text",
    SITE_COOKIE_LINK_TEXT="cookie link text",
    SITE_COOKIE_LINK_URL="cookie link url",
    SITE_KCM_SURVEY_LINK_TEXT="kcm survey link text",
    SITE_KCM_SURVEY_LINK_URL="kcm survey link url",
    SITE_OPENID_CONNECT_LOGIN_TEXT="openid connect login_text",
    SITE_OPENID_DISPLAY="openid display",
    SITE_REDIRECT_TO="redirect to",
    SITE_ALLOW_MESSAGES_FILE_SHARING=False,
    SITE_HIDE_CATEGORIES_FROM_ANONYMOUS_USERS=True,
    SITE_HIDE_SEARCH_FROM_ANONYMOUS_USERS=True,
    SITE_DISPLAY_SOCIAL=False,
    SITE_EHERKENNING_ENABLED=True,
)
class SiteConfigurationSetupTest(TestCase):
    def test_site_configure(self):
        configuration_step = SiteConfigurationStep()

        configuration_step.configure()

        config = SiteConfiguration.get_solo()

        self.assertTrue(configuration_step.is_configured())

        self.assertEqual(config.name, "My site")
        self.assertEqual(config.secondary_color, "#000000"),
        self.assertEqual(config.accent_color, "#000000"),
        self.assertEqual(config.primary_font_color, "#111111"),
        self.assertEqual(config.secondary_font_color, "#222222"),
        self.assertEqual(config.accent_font_color, "#333333"),
        self.assertTrue(config.warning_banner_enabled),
        self.assertEqual(config.warning_banner_text, "warning banner text"),
        self.assertEqual(config.warning_banner_background_color, "#444444"),
        self.assertEqual(config.warning_banner_font_color, "#555555"),
        self.assertFalse(config.login_show),
        self.assertTrue(config.login_allow_registration),
        self.assertTrue(config.login_2fa_sms),
        self.assertEqual(config.login_text, "login text"),
        self.assertEqual(config.registration_text, "registration text"),
        self.assertEqual(config.home_welcome_title, "welcome title"),
        self.assertEqual(config.home_welcome_intro, "welcome intro"),
        self.assertEqual(config.home_theme_title, "home theme title"),
        self.assertEqual(config.home_theme_intro, "home theme intro"),
        self.assertEqual(config.theme_title, "theme title"),
        self.assertEqual(config.theme_intro, "theme intro"),
        self.assertEqual(config.home_map_title, "home map title"),
        self.assertEqual(config.home_map_intro, "home map intro"),
        self.assertEqual(config.home_questionnaire_title, "home questionnaire title"),
        self.assertEqual(config.home_questionnaire_intro, "home questionnaire intro"),
        self.assertEqual(config.home_product_finder_title, "home product finder title"),
        self.assertEqual(config.home_product_finder_intro, "home product finder intro"),
        self.assertEqual(
            config.select_questionnaire_title, "select questionnaire title"
        ),
        self.assertEqual(
            config.select_questionnaire_intro, "select questionnaire intro"
        ),
        self.assertEqual(config.plans_intro, "plans intro"),
        self.assertEqual(config.plans_no_plans_message, "plans no plans_message"),
        self.assertEqual(config.plans_edit_message, "plans edit message"),
        self.assertEqual(config.footer_logo_title, "footer logo title"),
        self.assertEqual(config.footer_logo_url, "footer logo url"),
        self.assertEqual(config.home_help_text, "home help text"),
        self.assertEqual(config.theme_help_text, "theme help text"),
        self.assertEqual(config.product_help_text, "product help text"),
        self.assertEqual(config.search_help_text, "search help text"),
        self.assertEqual(config.account_help_text, "account help text"),
        self.assertEqual(config.questionnaire_help_text, "questionnaire help text"),
        self.assertEqual(config.plan_help_text, "plan help text"),
        self.assertFalse(config.search_filter_categories),
        self.assertFalse(config.search_filter_tags),
        self.assertFalse(config.search_filter_organizations),
        self.assertFalse(config.email_new_message),
        self.assertEqual(
            config.recipients_email_digest, ["test1@test.nl", "test2@test.nl"]
        ),
        self.assertEqual(config.contact_phonenumber, "12345"),
        self.assertEqual(config.contact_page, "https://test.test"),
        self.assertEqual(config.gtm_code, "gtm code"),
        self.assertEqual(config.ga_code, "ga code"),
        self.assertEqual(config.matomo_url, "matomo url"),
        self.assertEqual(config.matomo_site_id, 88),
        self.assertEqual(config.siteimprove_id, "88"),
        self.assertEqual(config.cookie_info_text, "cookie info text"),
        self.assertEqual(config.cookie_link_text, "cookie link text"),
        self.assertEqual(config.cookie_link_url, "cookie link url"),
        self.assertEqual(config.kcm_survey_link_text, "kcm survey link text"),
        self.assertEqual(config.kcm_survey_link_url, "kcm survey link url"),
        self.assertEqual(config.openid_connect_login_text, "openid connect login_text"),
        self.assertEqual(config.openid_display, "openid display"),
        self.assertEqual(config.redirect_to, "redirect to"),
        self.assertFalse(config.allow_messages_file_sharing),
        self.assertTrue(config.hide_categories_from_anonymous_users),
        self.assertTrue(config.hide_search_from_anonymous_users),
        self.assertFalse(config.display_social),
        self.assertTrue(config.eherkenning_enabled),

    @override_settings(
        SITE_NAME="My site",
        SITE_SECONDARY_COLOR="#000000",
        SITE_ACCENT_COLOR="#000000",
        SITE_PRIMARY_FONT_COLOR=None,
        SITE_SECONDARY_FONT_COLOR=None,
        SITE_ACCENT_FONT_COLOR=None,
        SITE_WARNING_BANNER_ENABLED=None,
    )
    def test_site_configure_use_defaults(self):
        configuration_step = SiteConfigurationStep()

        configuration_step.configure()

        config = SiteConfiguration.get_solo()

        self.assertEqual(config.primary_font_color, ColorTypeChoices.light)
        self.assertEqual(config.secondary_font_color, ColorTypeChoices.light)
        self.assertEqual(config.accent_font_color, ColorTypeChoices.dark)
        self.assertFalse(config.warning_banner_enabled)

    @override_settings(
        SITE_NAME=None,
        SITE_SECONDARY_COLOR="#000000",
        SITE_ACCENT_COLOR="#111111",
    )
    def test_site_not_configured(self):
        configuration_step = SiteConfigurationStep()

        configuration_step.configure()

        self.assertFalse(configuration_step.is_configured())

    @override_settings(
        SITE_NAME="My site",
        SITE_SECONDARY_COLOR="#000000",
        SITE_ACCENT_COLOR="#111111",
        SITE_LOGIN_SHOW="Should be boolean",
    )
    def test_site_configure_error(self):
        configuration_step = SiteConfigurationStep()

        with self.assertRaises(ValidationError):
            configuration_step.configure()
