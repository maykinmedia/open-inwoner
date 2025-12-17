from django.apps import AppConfig


class MijnAfvalConfig(AppConfig):
    name = "open_inwoner.mijn_afval"

    def ready(self):
        # Import CMS integration to trigger autodiscovery/registration
        import open_inwoner.mijn_afval.cms.cms_apps  # noqa
