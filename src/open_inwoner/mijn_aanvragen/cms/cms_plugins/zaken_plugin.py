from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from furl import furl

from open_inwoner.mijn_aanvragen.cms.models.zaken_plugin_config import (
    CMSZakenPluginConfig,
)
from open_inwoner.mijn_aanvragen.models import ZGWApiGroupConfig

logger = structlog.stdlib.get_logger(__name__)


@plugin_pool.register_plugin
class CMSZakenPlugin(CMSPluginBase):
    model = CMSZakenPluginConfig
    name = _("Zaken Plugin")
    render_template = "cms/plugins/zaken/zaken.html"
    cache = False

    def render(self, context, instance, placeholder) -> dict:
        """
        Render the CMS Zaken Plugin

        This method prepares the initial container that will use HTMX to load
        zaken data asynchronously.
        """
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

        mijn_zaken_url = reverse("cases:index")

        context.update(
            {
                "show_zaken_plugin": True,
                "mijn_zaken_url": mijn_zaken_url,
                "plugin_title": instance.title,
                "hx_get_url": f_url.url,
            }
        )

        return context
