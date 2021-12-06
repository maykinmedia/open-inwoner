from django.conf import settings as django_settings

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.models import Category


def settings(request):
    public_settings = (
        "GOOGLE_ANALYTICS_ID",
        "ENVIRONMENT",
        "SHOW_ALERT",
        "PROJECT_NAME",
    )

    config = SiteConfiguration.get_solo()

    context = {
        "site_logo": config.logo.file.url if config.logo else "",
        "theming": f"--color-primary: {config.primary_color}; --color-secondary: {config.secondary_color}; --color-accent: {config.accent_color};",
        "menu_categories": Category.get_root_nodes(),
        "settings": dict(
            [(k, getattr(django_settings, k, None)) for k in public_settings]
        ),
    }

    if hasattr(django_settings, "SENTRY_CONFIG"):
        context.update(dsn=django_settings.SENTRY_CONFIG.get("public_dsn", ""))

    return context
