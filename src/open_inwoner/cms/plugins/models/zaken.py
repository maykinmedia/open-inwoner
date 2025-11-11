from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin


class CMSZakenPluginConfig(CMSPlugin):
    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("The title of the zaken plugin block"),
        default=_("Mijn Zaken"),
    )
