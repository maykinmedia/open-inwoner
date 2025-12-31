from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin


class UserFeedPluginConfig(CMSPlugin):
    """
    Configuration model for the User Feed CMS plugin.

    Renamed from 'UserFeed' to 'UserFeedPluginConfig' for consistency.
    """

    class Meta:
        app_label = "plugins"
        db_table = "plugins_userfeed"  # Use existing table from legacy plugins app

    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("The title of the plugin block"),
        default=_("Openstaande acties"),
    )

    def __str__(self):
        return self.title or super().__str__()


__all__ = ["UserFeedPluginConfig"]
