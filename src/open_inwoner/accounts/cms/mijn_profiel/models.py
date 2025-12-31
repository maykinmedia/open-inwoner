from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin


class UserAppointments(CMSPlugin):
    """
    CMS plugin for displaying user appointments.

    This model was originally created in the 'plugins' app. The app_label and
    db_table settings preserve compatibility until a future data migration updates
    ContentType references.
    """

    class Meta:
        app_label = "plugins"
        db_table = (
            "plugins_userappointments"  # Preserve existing table from plugins app
        )

    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("The title of the plugin block"),
        default=_("Geplande balie-afspraken"),
    )

    def __str__(self):
        return self.title or super().__str__()
