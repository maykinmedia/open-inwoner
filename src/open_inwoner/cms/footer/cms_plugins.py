from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

import structlog
from cms.models import Page
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.models import KlantenSysteemConfig

from .models import CMSFlatPageModel

logger = structlog.stdlib.get_logger(__name__)


@plugin_pool.register_plugin
class FooterPagesPlugin(CMSPluginBase):
    name = _("Pages List")
    render_template = "cms/footer/footer_pages_plugin.html"
    cache = False

    def render(self, context, instance, placeholder):
        config = SiteConfiguration.get_solo()
        klant_config = KlantenSysteemConfig.get_solo()

        cms_pages = config.get_ordered_cms_pages()
        user = context["request"].user
        if not user.is_authenticated:
            for page in cms_pages:
                if (
                    hasattr(page, "commonextension")
                    and page.commonextension.requires_auth
                ):
                    cms_pages.remove(page)

        # In CMS 4.x, template is stored on PageContent, not Page
        contact_form_pages = Page.objects.filter(
            pagecontent_set__template="cms/contactform/form_outer.html"
        ).distinct()

        # Use the first page if it exists
        if contact_form_pages.exists() and klant_config.contact_registration_enabled:
            cms_pages.insert(0, contact_form_pages.first())

        context["cms_pages"] = cms_pages
        return context


@plugin_pool.register_plugin
class CMSFlatPagePlugin(CMSPluginBase):
    name = _("CMS Flatpage Plugin")
    model = CMSFlatPageModel
    render_template = "cms/cms_flatpage.html"

    def render(self, context, instance, placeholder):
        cms_plugin_placeholder = instance.placeholder
        cms_pages = Page.objects.filter(placeholders=cms_plugin_placeholder)

        if cms_pages.count() > 1:
            logger.warning("Multiple CMS pages found for CMSFlatPagePlugin")

        cms_page = cms_pages.first()

        if not hasattr(context, "user") or not context["user"].is_authenticated:
            if (
                hasattr(cms_page, "commonextension")
                and cms_page.commonextension.requires_auth
            ):
                raise PermissionDenied

        context["cms_flatpage_plugin"] = instance
        return context
