from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django_prosemirror.fields import ProsemirrorModelField
from django_prosemirror.schema import MarkType, NodeType


class ContactFormConfig(CMSPlugin):
    description_authenticated_user = ProsemirrorModelField(
        _("Description authenticated users"),
        allowed_node_types=[NodeType.PARAGRAPH],
        allowed_mark_types=[
            MarkType.STRONG,
            MarkType.ITALIC,
            MarkType.UNDERLINE,
            MarkType.LINK,
        ],
        null=True,
        blank=True,
        help_text=_("Description of the contact form for authenticated users"),
    )
    description_anonymous_user = ProsemirrorModelField(
        _("Description anonymous users"),
        allowed_node_types=[NodeType.PARAGRAPH],
        allowed_mark_types=[
            MarkType.STRONG,
            MarkType.ITALIC,
            MarkType.UNDERLINE,
            MarkType.LINK,
        ],
        null=True,
        blank=True,
        help_text=_(
            "Description of the contact form for anonymous/non-authenticated users"
        ),
    )


@plugin_pool.register_plugin
class ContactFormPlugin(CMSPluginBase):
    model = ContactFormConfig
    app_hook = "OpenKlantApphook"
    name = _("Contact form plugin")
    render_template = "cms/contactform/form_inner.html"
    cache = False

    def render(self, context, instance, placeholder):
        user = context["request"].user
        form_description = (
            instance.description_authenticated_user
            if user.is_authenticated
            else instance.description_anonymous_user
        )
        context.update(
            {
                "plugin_instance": instance,
                "form_description": form_description,
            }
        )
        return context
