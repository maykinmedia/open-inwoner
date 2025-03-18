import uuid

from django.core.validators import RegexValidator
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


class ReisDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    reisdocumentnummer = models.CharField(validators=[RegexValidator("^[A-Z0-9]{9}$")])

    # Code of the type ('soort.code' in the API)
    type = models.CharField(validators=[RegexValidator("^[a-zA-Z0-9 \.]+$")])

    # 'soort.description' in the API
    description = models.CharField(
        validators=[RegexValidator("^[a-zA-Z0-9À-ž '\,\(\)\.\-]{1,200}$")]
    )

    # Falls under 'datumEindeGeldigheid' in the API
    endDateValid_date = models.CharField(max_length=10)
    # endDateValid_type = models.CharField()

    # Other fields...

    # TODO: voeg nog deze attributes toe aan de velden:
    # verbose_name
    # related_name
    # help_text
    # Check hoe deze attributes bij andere models zijn toegevoegd
