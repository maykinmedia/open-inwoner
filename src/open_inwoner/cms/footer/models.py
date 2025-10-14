from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models.pluginmodel import CMSPlugin
from django_prosemirror.fields import ProsemirrorModelField
from django_prosemirror.schema import MarkType, NodeType


class CMSFlatPageModel(CMSPlugin):
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=255,
        blank=True,
        help_text=_("The title of the page"),
    )
    content = ProsemirrorModelField(
        _("Content"),
        allowed_node_types=[NodeType.PARAGRAPH, NodeType.HEADING],
        allowed_mark_types=[
            MarkType.STRONG,
            MarkType.ITALIC,
            MarkType.UNDERLINE,
            MarkType.LINK,
        ],
        null=True,
        blank=True,
        help_text=_("The content of the page"),
    )
