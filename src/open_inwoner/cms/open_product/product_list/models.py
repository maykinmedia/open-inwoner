from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import CMSPlugin


class ProductList(CMSPlugin):
    title = models.CharField(
        verbose_name=_("Title"), help_text=_("Title of this product list.")
    )
    description = models.CharField(
        verbose_name=_("Description"),
        help_text=_("Description of this product list."),
    )
    theme = models.CharField(
        verbose_name=_("Theme"),
        help_text="What theme of Open Products the list will render.",
    )

    def __str__(self):
        return self.title
