from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from django_prosemirror.fields import ProsemirrorModelField


class TextPluginConfig(CMSPlugin):
    """
    Configuration model for the Text CMS plugin.

    Renamed from 'Text' to 'TextPluginConfig' for consistency with other plugin models.
    """

    class Meta:
        app_label = "plugins"
        db_table = "plugins_text"  # Use existing table from legacy plugins app

    body = ProsemirrorModelField(
        _("Body"),
        help_text=_("The text content"),
    )

    def __str__(self):
        return self.body.html


__all__ = ["TextPluginConfig"]
