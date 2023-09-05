from django.conf import settings as django_settings

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.models import Category, Question
from open_inwoner.search.forms import SearchForm


def settings(request):
    public_settings = (
        "GOOGLE_ANALYTICS_ID",
        "ENVIRONMENT",
        "SHOW_ALERT",
        "PROJECT_NAME",
        "DIGID_ENABLED",
    )

    config = SiteConfiguration.get_solo()

    context = {
        "site_name": config.name,
        "theming": {
            "primary": config.get_primary_color,
            "secondary": config.get_secondary_color,
            "accent": config.get_accent_color,
            "primary_font_color": config.primary_font_color,
            "secondary_font_color": config.secondary_font_color,
            "accent_font_color": config.accent_font_color,
        },
        "configurable_text": {
            "home_page": {
                "home_welcome_title": config.home_welcome_title,
                "home_welcome_intro": config.home_welcome_intro,
                "home_theme_title": config.home_theme_title,
                "home_theme_intro": config.home_theme_intro,
                "home_map_title": config.home_map_title,
                "home_map_intro": config.home_map_intro,
                "home_questionnaire_title": config.home_questionnaire_title,
                "home_questionnaire_intro": config.home_questionnaire_intro,
                "home_product_finder_title": config.home_product_finder_title,
                "home_product_finder_intro": config.home_product_finder_intro,
            },
            "theme_page": {
                "theme_title": config.theme_title,
                "theme_intro": config.theme_intro,
            },
            "plans_page": {
                "plans_intro": config.plans_intro,
                "plans_no_plans_message": config.plans_no_plans_message,
                "plans_edit_message": config.plans_edit_message,
            },
            "questionnaire_page": {
                "select_questionnaire_title": config.select_questionnaire_title,
                "select_questionnaire_intro": config.select_questionnaire_intro,
            },
        },
        "footer": {
            "logo": config.footer_logo,
            "logo_alt": config.name,
            "logo_url": config.footer_logo_url,
            "logo_title": config.footer_logo_title,
        },
        "hero_image_login": (
            config.hero_image_login.file.url if config.hero_image_login else ""
        ),
        "favicon": (config.favicon.file.url if config.favicon else ""),
        "login_allow_registration": config.login_allow_registration,
        "login_text": config.login_text,
        "gtm_code": config.gtm_code,
        "ga_code": config.ga_code,
        "google_enabled": config.google_enabled,
        "matomo_url": config.matomo_url,
        "matomo_site_id": config.matomo_site_id,
        "matomo_enabled": config.matomo_enabled,
        "siteimprove_id": config.siteimprove_id,
        "siteimprove_enabled": config.siteimprove_enabled,
        "cookiebanner_enabled": config.cookiebanner_enabled,
        "cookie_info_text": config.cookie_info_text,
        "cookie_link_text": config.cookie_link_text,
        "cookie_link_url": config.cookie_link_url,
        "extra_css": config.extra_css,
        "menu_categories": Category.get_root_nodes().published(),
        # default SearchForm, might be overwritten by actual SearchView
        "search_form": SearchForm(auto_id=False),
        "search_filter_categories": config.search_filter_categories,
        "search_filter_tags": config.search_filter_tags,
        "search_filter_organizations": config.search_filter_organizations,
        "has_general_faq_questions": Question.objects.general().exists(),
        "settings": dict(
            [(k, getattr(django_settings, k, None)) for k in public_settings]
        ),
        "hide_categories_from_anonymous_users": config.hide_categories_from_anonymous_users,
        "warning_banner_enabled": config.warning_banner_enabled,
        "warning_banner_text": config.warning_banner_text,
        "warning_banner_background_color": config.warning_banner_background_color,
        "warning_banner_font_color": config.warning_banner_font_color,
    }

    if hasattr(django_settings, "SENTRY_CONFIG"):
        context.update(dsn=django_settings.SENTRY_CONFIG.get("public_dsn", ""))

    return context
