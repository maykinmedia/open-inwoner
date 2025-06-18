from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models.pluginmodel import CMSPlugin


class CMSFlatPageModel(CMSPlugin):
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=255,
        blank=True,
        help_text=_("The title of the page"),
    )
    content = models.TextField(
        verbose_name=_("Content"),
        blank=True,
        help_text=_("The content of the page"),
    )
