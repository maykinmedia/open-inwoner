from django.apps import AppConfig


class UserFeedConfig(AppConfig):
    name = "open_inwoner.userfeed"
    label = "userfeed"
    verbose_name = "User Feed"

    def ready(self):
        auto_import_adapters()

        from .config_checks import fetch_userfeed  # noqa


def auto_import_adapters():
    """
    import files from hooks directory to register adapters
    """
    import open_inwoner.userfeed.hooks  # noqa
