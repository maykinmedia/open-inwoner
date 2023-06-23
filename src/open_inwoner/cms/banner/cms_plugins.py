from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .forms import BannerImageForm, BannerTextForm
from .models import BannerImage, BannerText


@plugin_pool.register_plugin
class BannerImagePlugin(CMSPluginBase):
    model = BannerImage
    form = BannerImageForm
    name = _("Banner Image Plugin")
    render_template = "cms/banner/banner_image_plugin.html"
    cache = False


@plugin_pool.register_plugin
class BannerTextPlugin(CMSPluginBase):
    model = BannerText
    form = BannerTextForm
    name = _("Banner Text Plugin")
    render_template = "cms/banner/banner_text_plugin.html"
    cache = False
