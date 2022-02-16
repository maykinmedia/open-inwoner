from django.db import models
from django.utils.translation import ugettext_lazy as _


class Neighbourhood(models.Model):
    name = models.CharField(
        _("name"), max_length=100, unique=True, help_text=_("Neighbourhood name")
    )

    class Meta:
        verbose_name = _("neighbourhood")
        verbose_name_plural = _("neighbourhoods")

    def __str__(self):
        return self.name
