from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import Text


@plugin_pool.register_plugin
class TextPlugin(CMSPluginBase):
    model = Text
    name = _("Text")
    render_template = "cms/plugins/text.html"
    cache = False
