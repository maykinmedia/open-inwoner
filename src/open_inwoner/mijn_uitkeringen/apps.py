from django.apps import AppConfig


class MijnUitkeringenConfig(AppConfig):
    name = "open_inwoner.mijn_uitkeringen"
    label = "ssd"  # Keep the original label to preserve migration history

    def ready(self):
        # Import CMS integration to trigger autodiscovery/registration
        import open_inwoner.mijn_uitkeringen.cms.cms_apps  # noqa
