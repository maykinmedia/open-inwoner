from django.apps import AppConfig


class PluginsConfig(AppConfig):
    name = "open_inwoner.cms.plugins"

    def ready(self):
        # imports models, which can't happen before the app registry is ready
        from open_inwoner.cms.utils.static_aliases import (
            patch_static_alias_plugin_restrictions,
        )

        patch_static_alias_plugin_restrictions()
