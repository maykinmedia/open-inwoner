from django.db import models
from django.utils.translation import gettext_lazy as _


class MijnAfvalApphookConfig(models.Model):
    namespace = models.CharField(
        _("Instance namespace"),
        max_length=100,
        unique=True,
        default=None,
    )
    page_heading = models.CharField(
        verbose_name=_("Page heading"),
        max_length=200,
        default="Mijn Afval",
        help_text=_("The heading of the 'Mijn Afval' page"),
    )
    page_description = models.TextField(
        verbose_name=_("Page description"),
        blank=True,
        help_text=_("The description for the 'Mijn Afval' page"),
    )
