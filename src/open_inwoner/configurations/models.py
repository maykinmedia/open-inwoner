from django.db import models
from django.utils.translation import ugettext_lazy as _

from colorfield.fields import ColorField
from filer.fields.image import FilerImageField
from solo.models import SingletonModel


class SiteConfiguration(SingletonModel):
    name = models.CharField(max_length=255, help_text=_("The name of the municipality"))
    primary_color = ColorField(
        help_text=_("The primary color of the municipality's site"),
    )
    secondary_color = ColorField(
        help_text=_("The secondary color of the municipality's site"),
    )
    accent_color = ColorField(
        help_text=_("The accent color of the municipality's site"),
    )
    logo = FilerImageField(
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="site_logo",
        help_text=_("Logo of the municipality"),
    )

    def __str__(self):
        return "Site Configuration"

    class Meta:
        verbose_name = "Site Configuration"
