from django.db import models
from django.utils.translation import gettext_lazy as _


class CompanyType(models.TextChoices):
    hoofdvestiging = "hoofdvestiging", _("Hoofdvestiging")
    nevenvestiging = "nevenvestiging", _("Nevenvestiging")
    rechtspersoon = "rechtspersoon", _("Rechtspersoon")
