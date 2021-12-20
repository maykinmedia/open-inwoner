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
            "home_welcome_title": config.home_welcome_title,
            "home_welcome_intro": config.home_welcome_intro,
            "theme_title": config.theme_title,
            "theme_intro": config.theme_intro,
            "home_map_title": config.home_map_title,
            "home_map_intro": config.home_map_intro,
        },
        "hero_image_login": config.hero_image_login.file.url
        if config.hero_image_login
        else "",
        "login_allow_registration": config.login_allow_registration,
        "login_text": config.login_text,
        "menu_categories": Category.get_root_nodes(),
        "search_form": SearchForm(),
        "settings": dict(
            [(k, getattr(django_settings, k, None)) for k in public_settings]
        ),
    }

    if hasattr(django_settings, "SENTRY_CONFIG"):
        context.update(dsn=django_settings.SENTRY_CONFIG.get("public_dsn", ""))

    return context
