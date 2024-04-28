from django.db import models
from django.utils.translation import gettext_lazy as _


class BasicFieldDescription(models.TextChoices):
    ArrayField = _("string, comma-delimited ('foo,bar,baz')")
    BooleanField = "True, False"
    CharField = _("string")
    IntegerField = _("string representing an integer")
    PositiveIntegerField = _("string representing a positive integer")
    TextField = _("text (string)")
    URLField = _("string (URL)")
    UUIDField = _("UUID string (e.g. f6b45142-0c60-4ec7-b43d-28ceacdc0b34)")
