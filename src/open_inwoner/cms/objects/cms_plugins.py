from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import ObjectsList


@plugin_pool.register_plugin
class ObjectsListPlugin(CMSPluginBase):
    model = ObjectsList
    name = _("Object List Plugin")
    render_template = "cms/objects/objects_list.html"
    cache = False
