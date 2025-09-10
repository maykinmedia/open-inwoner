import logging

from django import forms
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin, Page
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from djangocms_text_ckeditor.widgets import TextEditorWidget

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.models import KlantenSysteemConfig

from .models import CMSFlatPageModel

logger = logging.getLogger(__name__)


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

        # Get ContactFormPlugin instances
        contact_form_plugins = CMSPlugin.objects.filter(plugin_type="ContactFormPlugin")

        # Get placeholders containing the plugins
        placeholder_ids = contact_form_plugins.values_list("placeholder_id", flat=True)

        # Get the CMS pages containing the placeholders
        contact_form_pages = Page.objects.filter(
            placeholders__id__in=placeholder_ids, publisher_is_draft=False
        )

        # Use the first page if it exists
        if contact_form_pages.exists() and klant_config.contact_registration_enabled:
            cms_pages.insert(0, contact_form_pages.first())

        context["cms_pages"] = cms_pages
        return context


class CMSFlatPageModelForm(forms.ModelForm):
    class Meta:
        model = CMSFlatPageModel
        fields = "__all__"
        widgets = {
            "content": TextEditorWidget,
        }


@plugin_pool.register_plugin
class CMSFlatPagePlugin(CMSPluginBase):
    name = _("CMS Flatpage Plugin")
    model = CMSFlatPageModel
    form = CMSFlatPageModelForm
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
