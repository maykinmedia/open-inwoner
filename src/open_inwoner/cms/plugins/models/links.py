from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from django_prosemirror.fields import ProsemirrorModelField
from django_prosemirror.schema import MarkType, NodeType
from djangocms_link.models import AbstractLink


class CMSLinkPluginConfig(CMSPlugin):
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=128,
        help_text=_("The title of the plugin block"),
        default=_("Ga naar"),
    )


class ExtendedCMSLink(AbstractLink):
    """Extended CMS `Link` model with icon field"""

    # Override search_fields to use our plain text property
    search_fields = ("name_text",)

    name = ProsemirrorModelField(
        verbose_name=_("Name"),
        allowed_node_types=[NodeType.HARD_BREAK, NodeType.PARAGRAPH],
        allowed_mark_types=[
            MarkType.STRONG,
            MarkType.ITALIC,
            MarkType.UNDERLINE,
        ],
        help_text=_("The text displayed for the link"),
    )
    icon = models.CharField(
        verbose_name=_("Icon"),
        max_length=96,
        blank=True,
        default="east",
        help_text=_(
            "Material icon name (e.g., 'east', 'arrow_forward', 'check', 'home'). "
            "See https://fonts.google.com/icons for available icons."
        ),
    )

    @property
    def name_text(self):
        """Return plain text version of name for search and display"""
        if self.name and self.name.html:
            return strip_tags(self.name.html)
        return ""

    def __str__(self):
        """
        Return string representation of the link name

        Necessary because `ProsemirrorModelField` content is a `dict` but Django CMS
        requires a `str` for editing fields
        """
        return self.name_text or str(self.pk)

    def get_short_description(self):
        return self.name_text or str(self.pk)
