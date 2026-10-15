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

from django.conf import settings

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


def patch_static_alias_plugin_restrictions():
    """
    Make the structure board restrict the plugins of static aliases by their
    static code.

    The plugins that can be added to, or moved into, a placeholder are passed to
    the structure board by `get_placeholder_toolbar_js()`, which looks them up by
    the placeholder's slot.
    """
    if hasattr(BaseRenderer, "_original_get_placeholder_toolbar_js"):
        return

    BaseRenderer._original_get_placeholder_toolbar_js = (
        BaseRenderer.get_placeholder_toolbar_js
    )

    def get_placeholder_toolbar_js(self, placeholder, page=None):
        return self._original_get_placeholder_toolbar_js(
            get_conf_placeholder(placeholder), page
        )

    BaseRenderer.get_placeholder_toolbar_js = get_placeholder_toolbar_js
