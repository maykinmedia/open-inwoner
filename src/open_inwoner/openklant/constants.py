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


# Bounds the number of pagination requests a klantcontactmomenten listing follows, so
# a klant with a long history has a bounded worst case. A default rather than
# something each caller passes: the listing is cached per (klant, max_requests) pair,
# so callers that disagree about it (a page view, the login cache warm-up, the
# invalidation after asking a question) land on separate cache entries and stop
# seeing each other's writes.
DEFAULT_KLANTCONTACTMOMENTEN_MAX_REQUESTS = 5
