from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


# Create your models here.
class OpenProductConfig(SingletonModel):
    """
    Configuration for product type action URLs
    """

    action_urls = models.JSONField(
        default=dict,
        verbose_name=_("Action URLs"),
        help_text=_("URL configurations for product type actions"),
    )

    class Meta:
        verbose_name = _("Open Product Configuration")
