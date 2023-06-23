from django.utils.translation import ugettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.plans.models import Plan

from ..utils.plugin_mixins import CMSActiveAppMixin


@plugin_pool.register_plugin
class ActivePlansPlugin(CMSActiveAppMixin, CMSPluginBase):
    module = _("Collaborate")
    name = _("Active Plans Plugin")
    render_template = "cms/collaborate/active_plans_plugin.html"
    cache = False
    disable_child_plugins = True
    app_hook = "CollaborateApphook"

    # own variables
    limit = 4

    def render(self, context, instance, placeholder):
        request = context["request"]
        if request.user.is_authenticated:
            context["plans"] = Plan.objects.connected(request.user)[: self.limit]
        return context
