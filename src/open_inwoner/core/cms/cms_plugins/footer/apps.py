from django.apps import AppConfig


class FooterConfig(AppConfig):
    name = "open_inwoner.core.cms.cms_plugins.footer"
    label = "footer"  # Preserve the original app label for migration history
    default_auto_field = "django.db.models.BigAutoField"
