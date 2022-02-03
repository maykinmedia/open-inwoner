from django.conf import settings as django_settings

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.models import Category
from open_inwoner.search.forms import SearchForm


def settings(request):
    public_settings = (
        "GOOGLE_ANALYTICS_ID",
        "ENVIRONMENT",
        "SHOW_ALERT",
        "PROJECT_NAME",
    )

    config = SiteConfiguration.get_solo()

    context = {
        "site_name": config.name,
        "site_logo": config.logo.file.url if config.logo else "",
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
            },
            "theme_page": {
                "theme_title": config.theme_title,
                "theme_intro": config.theme_intro,
            },
            "footer": {
                "footer_visiting_title": config.footer_visiting_title,
                "footer_visiting_intro": config.footer_visiting_intro,
                "footer_visiting_map": config.footer_visiting_map,
                "footer_mailing_title": config.footer_mailing_title,
                "footer_mailing_intro": config.footer_mailing_intro,
                "flatpages": config.get_ordered_flatpages,
            },
            "help": config.get_help_text(request),
        },
        "hero_image_login": config.hero_image_login.file.url
        if config.hero_image_login
        else "",
        "login_allow_registration": config.login_allow_registration,
        "show_cases": config.show_cases,
        "login_text": config.login_text,
        "gtm_code": config.gtm_code,
        "ga_code": config.ga_code,
        "google_enabled": config.google_enabled,
        "matomo_url": config.matomo_url,
        "matomo_site_id": config.matomo_site_id,
        "matomo_enabled": config.matomo_enabled,
        "menu_categories": Category.get_root_nodes(),
        "search_form": SearchForm(),
        "settings": dict(
            [(k, getattr(django_settings, k, None)) for k in public_settings]
        ),
    }

    if hasattr(django_settings, "SENTRY_CONFIG"):
        context.update(dsn=django_settings.SENTRY_CONFIG.get("public_dsn", ""))

    return context
