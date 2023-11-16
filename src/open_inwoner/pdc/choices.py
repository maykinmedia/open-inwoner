from django.db import models
from django.utils.translation import gettext as _


class YesNo(models.TextChoices):
    yes = "yes", _("Ja")
    no = "no", _("Nee")
