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

    def __str__(self):
        return self.title
