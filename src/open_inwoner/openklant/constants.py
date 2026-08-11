import enum

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


class KlantenServiceType(enum.Enum):
    ESUITE = "esuite"
    OPENKLANT2 = "openklant2"


# Default bound on the pagination requests a klantcontactmomenten listing follows, so
# a klant with a long history has a bounded worst case. Lives here rather than on the
# client or the service because both the model field default and the client need it.
DEFAULT_KLANTCONTACTMOMENTEN_MAX_REQUESTS = 5
