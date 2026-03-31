from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

import structlog
from cms.models import Page, PageContent
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from djangocms_versioning.constants import PUBLISHED

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
            cms_pages = [
                page
                for page in cms_pages
                if not (
                    hasattr(page, "commonextension")
                    and page.commonextension.requires_auth
                )
            ]

        contact_form_page_ids = PageContent._original_manager.filter(
            template="cms/contactform/form_outer.html",
            versions__state=PUBLISHED,
        ).values_list("page_id", flat=True)
        contact_form_pages = Page.objects.filter(id__in=contact_form_page_ids)

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
        # Page.placeholders M2M was removed in CMS 4 (migration 0028_remove_page_placeholders).
        # Placeholders now belong to PageContent objects, so look up via PageContent instead.
        page_contents = PageContent._original_manager.filter(
            placeholders=cms_plugin_placeholder
        )

        if page_contents.count() > 1:
            logger.warning("Multiple CMS pages found for CMSFlatPagePlugin")

        cms_page = page_contents.first().page if page_contents.exists() else None

        if not hasattr(context, "user") or not context["user"].is_authenticated:
            if (
                hasattr(cms_page, "commonextension")
                and cms_page.commonextension.requires_auth
            ):
                raise PermissionDenied

        context["cms_flatpage_plugin"] = instance
        return context
