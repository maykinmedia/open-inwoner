from django.apps import AppConfig


class MijnAanvragenConfig(AppConfig):
    name = "open_inwoner.mijn_aanvragen"
    label = "openzaak"  # Keep the old label to avoid migrations
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        # Import CMS plugins to trigger autodiscovery/registration
        import open_inwoner.mijn_aanvragen.cms.cms_plugins  # noqa
