import os
from importlib import import_module
from pathlib import Path

from django.apps import AppConfig


class UserFeedConfig(AppConfig):
    name = "open_inwoner.userfeed"
    label = "userfeed"
    verbose_name = "User Feed"

    def ready(self):
        auto_import_hooks()


def auto_import_hooks():
    """
    import files from hooks directory

    this expects things calling their register_xyz() function at module level
    """

    hooks_dir = Path(__file__).parent / "hooks"
    for f in os.listdir(hooks_dir):
        name, ext = os.path.splitext(f)
        if ext == ".py" and name != "__init__":
            path = f"open_inwoner.userfeed.hooks.{name}"
            import_module(path)
