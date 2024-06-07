from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class QmaticConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class QmaticConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Calendar API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
        help_text=_(
            "The Qmatic Orchestra Calendar Public Appointment API service. "
            "Example: https://example.com:8443/rest/"
        ),
    )
    booking_base_url = models.URLField(
        verbose_name=_("Booking base URL"),
        max_length=1000,
        help_text=_(
            "The base URL where the user can reschedule or delete their appointment"
        ),
        blank=True,
    )

    objects = QmaticConfigManager()

    class Meta:
        verbose_name = _("Qmatic configuration")
