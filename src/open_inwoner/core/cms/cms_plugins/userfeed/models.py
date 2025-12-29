from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin


class UserFeed(CMSPlugin):
    class Meta:
        app_label = "plugins"  # Keep original app_label to use existing table

    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("The title of the plugin block"),
        default=_("Openstaande acties"),
    )

    def __str__(self):
        return self.title or super().__str__()
