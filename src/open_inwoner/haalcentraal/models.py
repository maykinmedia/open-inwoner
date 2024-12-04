from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from .validators import validate_verwerking_header


class HaalCentraalConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class HaalCentraalConfig(SingletonModel):
    """
    global configuration and defaults
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Haal Centraal API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
    )

    api_origin_oin = models.CharField(
        verbose_name=_("API 'OIN' header"),
        max_length=64,
        blank=True,
        help_text=_(
            "Value of the 'x-origin-oin' header for Haalcentraal BRP API requests."
        ),
    )
    api_afnemer_oin = models.CharField(
        verbose_name=_("API 'OIN' afnemer header"),
        max_length=64,
        blank=True,
        help_text=_(
            "Value of the 'x-afnemer-oin' header for Haalcentraal BRP API requests."
        ),
    )
    api_doelbinding = models.CharField(
        verbose_name=_("API 'doelbinding' header"),
        max_length=64,
        blank=True,
        help_text=_(
            "Value of the 'x-doelbinding' header for Haalcentraal BRP API requests."
        ),
    )
    api_verwerking = models.CharField(
        _("API 'verwerking' header"),
        max_length=242,
        blank=True,
        validators=[validate_verwerking_header],
        help_text=_(
            "Value of the 'x-verwerking' header for Haalcentraal BRP API requests"
        ),
    )

    objects = HaalCentraalConfigManager()

    class Meta:
        verbose_name = _("Haal Centraal configuration")
