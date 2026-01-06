from django.utils.translation import gettext_lazy as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.core.cms.utils.mixins import CMSActiveAppMixin
from open_inwoner.mijn_samenwerkingen.models import Plan


@plugin_pool.register_plugin
class ActivePlansPlugin(CMSActiveAppMixin, CMSPluginBase):
    module = _("Collaborate")
    name = _("Active Plans Plugin")
    render_template = "mijn_samenwerkingen/cms/active_plans_plugin.html"
    cache = False
    disable_child_plugins = True
    app_hook = "CollaborateApphook"

    # own variables
    limit = 3

    def render(self, context, instance, placeholder):
        request = context["request"]
        if request.user.is_authenticated:
            context["plans"] = Plan.objects.connected(request.user)[: self.limit]
        return context
