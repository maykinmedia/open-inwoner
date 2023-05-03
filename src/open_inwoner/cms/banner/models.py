from django.db import models
from django.utils.translation import ugettext_lazy as _

from cms.models import CMSPlugin
from filer.fields.image import FilerImageField


class Banner(CMSPlugin):
    title = models.CharField(_("title"), max_length=250, default="")
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
        return self.title
