from django.apps import AppConfig


class ExtensionsConfig(AppConfig):
    name = "open_inwoner.core.cms.cms_plugins.extensions"
    label = "extensions"  # Preserve the original app label for migration history
    default_auto_field = "django.db.models.AutoField"
