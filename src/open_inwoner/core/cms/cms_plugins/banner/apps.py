from django.apps import AppConfig


class BannerConfig(AppConfig):
    name = "open_inwoner.core.cms.cms_plugins.banner"
    label = "banner"  # Preserve the original app label for migration history
    default_auto_field = "django.db.models.BigAutoField"
