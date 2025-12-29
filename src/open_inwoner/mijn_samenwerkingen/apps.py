from django.apps import AppConfig


class MijnSamenwerkingenConfig(AppConfig):
    name = "open_inwoner.mijn_samenwerkingen"
    label = "plans"  # Keep the original label to preserve migration history

    def ready(self):
        # Import CMS integration to trigger autodiscovery/registration
        import open_inwoner.mijn_samenwerkingen.cms.cms_apps  # noqa
        import open_inwoner.mijn_samenwerkingen.cms.cms_plugins  # noqa
