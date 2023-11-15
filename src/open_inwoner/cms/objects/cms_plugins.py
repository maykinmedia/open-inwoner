from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import ComponentChoices, ObjectsList


@plugin_pool.register_plugin
class ObjectsListPlugin(CMSPluginBase):
    model = ObjectsList
    name = _("Object List Plugin")
    render_template = "cms/objects/objects_list.html"
    cache = False

    def _get_render_template(self, context, instance, placeholder):
        default_template = super()._get_render_template(context, instance, placeholder)
        if component := instance.component:
            match component:
                case ComponentChoices.link:
                    return "cms/objects/objects_list.html"
                case ComponentChoices.map:
                    return "cms/objects/objects_map.html"

        return default_template

    def render(self, context, instance, placeholder):
        request = context["request"]
        context["instance"] = instance
        context["objects"] = []

        if request.user.is_authenticated and (bsn := request.user.bsn):
            objects = instance.get_objects_by_bsn(bsn)
            match instance.component:
                case ComponentChoices.link:
                    context["objects"] = instance.convert_objects_to_actiondata(objects)
                case ComponentChoices.map:
                    context["objects"] = instance.convert_objects_to_geodata(objects)
        return context
