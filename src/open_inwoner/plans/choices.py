from django.db import models
from django.utils.translation import gettext_lazy as _


class PlanStatusChoices(models.TextChoices):
    empty = "", _("Status")
    open = "open", _("Open")
    closed = "closed", _("Afgerond")
