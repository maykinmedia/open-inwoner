"""
Plugin restrictions for static aliases.

djangocms-alias stores the content of every alias in a placeholder with the slot
``content`` (and renders it with the same template), so `CMS_PLACEHOLDER_CONF`
can't tell the static aliases in our templates (the footer columns, the login
banner) apart from each other, or from the ``content`` placeholder of pages: they
all get the plugins allowed in ``content``.

This looks up the plugins allowed in a static alias by its ``static_code``
instead, when `CMS_PLACEHOLDER_CONF` has an entry for it.
"""

import copy
import inspect

from django.conf import settings
from django.core import checks

from cms.models import Placeholder
from cms.plugin_rendering import BaseRenderer
from djangocms_alias.models import AliasContent


def get_conf_placeholder(placeholder: Placeholder) -> Placeholder:
    """
    The placeholder to look up the `CMS_PLACEHOLDER_CONF` of `placeholder` with.

    For a static alias with an entry in `CMS_PLACEHOLDER_CONF`, this is an
    (unsaved) copy of the placeholder with the alias' static code as its slot.
    """
    source = placeholder.source
    if not isinstance(source, AliasContent):
        return placeholder

    # `None` is the key of the global configuration, so guard against aliases
    # without a static code
    static_code = source.alias.static_code
    if not static_code or static_code not in settings.CMS_PLACEHOLDER_CONF:
        return placeholder

    conf_placeholder = copy.copy(placeholder)
    conf_placeholder.slot = static_code
    return conf_placeholder


# The signature of `BaseRenderer.get_placeholder_toolbar_js()` the patch is written
# against
PATCHED_METHOD_PARAMETERS = ["self", "placeholder", "page"]


def get_patch_incompatibility() -> str | None:
    """
    Why `BaseRenderer` can't be patched, or `None` if it can.
    """
    original = getattr(BaseRenderer, "get_placeholder_toolbar_js", None)
    if original is None:
        return "`BaseRenderer.get_placeholder_toolbar_js()` does not exist"

    signature = inspect.signature(original)
    if list(signature.parameters) != PATCHED_METHOD_PARAMETERS:
        return (
            "`BaseRenderer.get_placeholder_toolbar_js()` has the signature "
            f"`{signature}`, expected `(self, placeholder, page=None)`"
        )

    return None


def is_patched() -> bool:
    return getattr(
        getattr(BaseRenderer, "get_placeholder_toolbar_js", None),
        "patched_for_static_aliases",
        False,
    )


def patch_static_alias_plugin_restrictions():
    """
    Make the structure board restrict the plugins of static aliases by their
    static code.

    The plugins that can be added to, or moved into, a placeholder are passed to
    the structure board by `get_placeholder_toolbar_js()`, which looks them up by
    the placeholder's slot.

    Written against django-cms 5.0.11 (`cms.plugin_rendering.BaseRenderer`) and
    djangocms-alias 2.0.5. If an upgrade renames or changes the signature of
    `get_placeholder_toolbar_js()`, the patch is skipped (static aliases then get
    the plugins of ``content``) and `check_static_alias_plugin_restrictions`
    reports it.
    """
    if is_patched() or get_patch_incompatibility():
        return

    original = BaseRenderer.get_placeholder_toolbar_js

    def get_placeholder_toolbar_js(self, placeholder, page=None):
        return original(self, get_conf_placeholder(placeholder), page)

    get_placeholder_toolbar_js.patched_for_static_aliases = True
    BaseRenderer.get_placeholder_toolbar_js = get_placeholder_toolbar_js


@checks.register()
def check_static_alias_plugin_restrictions(app_configs, **kwargs):
    if is_patched():
        return []

    reason = get_patch_incompatibility() or "the patch was not applied"
    return [
        checks.Warning(
            "The plugins of static aliases (the footer columns, the login banner) "
            "are not restricted by their static code: "
            f"{reason}.",
            hint=(
                "Update `open_inwoner.cms.utils.static_aliases` for the installed "
                "version of django-cms."
            ),
            obj=BaseRenderer,
            id="open_inwoner.cms.W001",
        )
    ]
