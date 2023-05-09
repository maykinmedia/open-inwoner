from django.db import models
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin
from filer.fields.image import FilerImageField


class Banner(CMSPlugin):
    name = models.CharField(_("Name"), max_length=250, default="")
    title = models.CharField(
        _("Title"),
        null=True,
        blank=True,
        max_length=250,
        help_text=_("Title to be shown along with the banner."),
    )
    description = models.TextField(
        verbose_name=_("Description"),
        null=True,
        blank=True,
        help_text=_("Description to be shown along with the banner."),
    )
    image = FilerImageField(
        verbose_name=_("Banner image"),
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        help_text=_("Banner image"),
    )
    image_height = models.PositiveIntegerField(
        verbose_name=_("Custom image height"),
        blank=True,
        null=True,
        help_text=_(
            "The image custom height as number in pixels. "
            'Example: "720" and not "720px".'
            "Leave this field empty if you want the original height of the image to be applied."
        ),
    )

    def __str__(self):
        return self.name
