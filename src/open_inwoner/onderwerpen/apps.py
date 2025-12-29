from django.apps import AppConfig


class OnderwerpenConfig(AppConfig):
    name = "open_inwoner.onderwerpen"
    label = "pdc"  # Keep the original label to preserve migration history

    def ready(self):
        # Import CMS integration to trigger autodiscovery/registration
        import open_inwoner.onderwerpen.cms.cms_apps  # noqa
        import open_inwoner.onderwerpen.cms.cms_plugins  # noqa
