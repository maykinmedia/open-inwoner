from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import Banner


@plugin_pool.register_plugin
class BannerPlugin(CMSPluginBase):
    model = Banner
    name = _("Banner Plugin")
    render_template = "cms/banner/banner_plugin.html"
