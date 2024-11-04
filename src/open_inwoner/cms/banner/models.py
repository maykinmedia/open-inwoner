import os

from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin
from filer.fields.image import FilerImageField


class BannerImage(CMSPlugin):
    image = FilerImageField(
        verbose_name=_("Banner image"),
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
        return os.path.basename(self.image.file.name)


class BannerText(CMSPlugin):
    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("The title of the text block"),
    )
    description = models.TextField(
        verbose_name=_("Description"),
        null=True,
        blank=True,
        help_text=_("The description of the text block"),
    )

    def __str__(self):
        return self.title
