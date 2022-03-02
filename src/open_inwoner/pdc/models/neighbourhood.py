from django.db import models
from django.utils.translation import ugettext_lazy as _


class Neighbourhood(models.Model):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
        unique=True,
        help_text=_("Neighbourhood name"),
    )

    class Meta:
        verbose_name = _("Neighbourhood")
        verbose_name_plural = _("Neighbourhoods")

    def __str__(self):
        return self.name
