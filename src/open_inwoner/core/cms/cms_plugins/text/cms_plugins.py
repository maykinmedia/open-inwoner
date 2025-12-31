from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import TextPluginConfig


@plugin_pool.register_plugin
class TextPlugin(CMSPluginBase):
    model = TextPluginConfig
    name = _("Text")
    render_template = "cms/plugins/text.html"
    cache = False


__all__ = ["TextPlugin"]
