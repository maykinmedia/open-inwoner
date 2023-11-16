from django.db import models
from django.utils.translation import gettext_lazy as _


class Status(models.TextChoices):
    nieuw = "nieuw", _("Nieuw")
    in_behandeling = "in_behandeling", _("In behandeling")
    afgehandeld = "afgehandeld", _("Afgehandeld")

    @classmethod
    def safe_label(cls, value, default=""):
        if not value:
            return default
        try:
            return getattr(cls, value).label
        except AttributeError:
            if default:
                return default
            return str(value).replace("_", " ").title()
