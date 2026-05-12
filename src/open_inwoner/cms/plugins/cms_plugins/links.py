from django import forms
from django.utils.translation import gettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from djangocms_link.cms_plugins import LinkPlugin as OriginalLinkPlugin

from open_inwoner.cms.plugins.models.links import CMSLinkPluginConfig, ExtendedCMSLink

# Replace original CMS LinkPlugin model with extended Model
plugin_pool.unregister_plugin(OriginalLinkPlugin)


@plugin_pool.register_plugin
class CMSLinkPlugin(CMSPluginBase):
    model = CMSLinkPluginConfig
    render_template = "cms/plugins/links/external-links.html"
    module = _("General")
    name = _("External Link Plugin")
    allow_children = True
    child_classes = ["LinkPlugin"]
    cache = False

    def render(self, context, instance, placeholder):
        if not context["request"].user.is_authenticated:
            return context

        context.update(
            {
                "link_plugin": instance,
            }
        )
        return context


class CustomLinkForm(forms.ModelForm):
    """Custom form for ExtendedCMSLink without advanced fields"""

    class Meta:
        model = ExtendedCMSLink
        fields = ["name", "link", "icon", "target"]


@plugin_pool.register_plugin
class LinkPlugin(OriginalLinkPlugin):
    """
    Extension of CMS `LinkPlugin` to display additional fields (e.g. `ExtendedCMSLink.icon`)
    """

    model = ExtendedCMSLink
    form = CustomLinkForm
    allow_children = False
    render_template = "cms/plugins/links/link.html"

    def get_render_template(self, context, instance, placeholder):
        """
        Override to use our custom template instead of the dynamic template path
        computed by OriginalLinkPlugin.get_render_template(), which would resolve to
        djangocms_link/{instance.template}/link.html and bypass our render_template
        attribute entirely."""
        return self.render_template

    fieldsets = [
        (
            None,
            {
                "fields": (
                    "name",
                    "link",
                    "icon",
                )
            },
        ),
        (
            _("Advanced settings"),
            {
                "classes": ("collapse",),
                "fields": ("target",),
            },
        ),
    ]
