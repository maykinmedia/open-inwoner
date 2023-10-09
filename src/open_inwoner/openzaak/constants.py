from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusIndicators(models.TextChoices):
    info = "info", _("Info")
    warning = "warning", _("Warning")
    failure = "failure", _("Failure")
    success = "success", _("Success")
