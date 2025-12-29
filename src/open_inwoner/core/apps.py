from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "open_inwoner.core"

    _has_run = False

    def ready(self):
        if self._has_run:
            return
        self._has_run = True

        # Import CMS plugins to trigger autodiscovery/registration
        import open_inwoner.core.cms.cms_plugins  # noqa: F401
