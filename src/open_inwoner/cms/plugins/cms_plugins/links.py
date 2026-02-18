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
        fields = ["name", "external_link", "icon", "target"]

    # `LinkPlugin.get_form()` from djangocms-link dynamically wraps the form class and
    # calls `for_site()`, which filters the `linternal_link` field's queryset to only show
    # CMS pages from the current site. We don't support internal links so the method
    # can be empty, but must be present to avoid `AttributeError` when editing links
    def for_site(self, site):
        pass


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
        Override to use our custom template that supports ProsemirrorModelField

        Note: setting the template via the render_template attribute does not work;
        template resolution seems to be broken by inheritance. Revisit when upgrading to
        Django CMS 4
        """
        return self.render_template

    fieldsets = [
        (
            None,
            {
                "fields": (
                    "name",
                    "external_link",
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
