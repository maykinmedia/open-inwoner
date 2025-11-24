from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from furl import furl

from open_inwoner.cms.plugins.models import CMSZakenPluginConfig
from open_inwoner.openzaak.models import ZGWApiGroupConfig

logger = structlog.stdlib.get_logger(__name__)


@plugin_pool.register_plugin
class CMSZakenPlugin(CMSPluginBase):
    model = CMSZakenPluginConfig
    name = _("Zaken Plugin")
    render_template = "cms/plugins/zaken/zaken.html"
    cache = False

    def render(self, context, instance, placeholder) -> dict[str, str]:
        if not ZGWApiGroupConfig.objects.exists():
            return context

        user = context["request"].user
        if not user.is_authenticated or not user.is_bsn_user:
            return context

        # HTMX endpoint with num_zaken parameter
        f_url = furl(
            reverse("cms_plugins:zaken_content", kwargs={"plugin_id": instance.pk})
        )
        f_url.args["num_zaken"] = instance.num_zaken

        context.update(
            {
                "instance": instance,
                "hxget": f_url.url,
            }
        )

        return context
