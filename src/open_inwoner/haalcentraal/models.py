from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from .validators import validate_verwerking_header


class BrpVersionChoices(models.TextChoices):
    V1_3 = "1.3", _("BRP 1.3")
    V2_0 = "2.0", _("BRP 2.0")
    V2_1 = "2.1", _("BRP 2.1")


class HaalCentraalConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class HaalCentraalConfig(SingletonModel):
    """
    global configuration and defaults
    """

    brp_version = models.CharField(
        verbose_name=_("BRP version"),
        max_length=3,
        choices=BrpVersionChoices.choices,
        default=BrpVersionChoices.V2_0,
        help_text=_(
            "Version of the Haal Centraal BRP API to use. "
            "See {url} for the API specification."
        ).format(url="https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/redoc"),
    )

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Haal Centraal API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.orc},
        related_name="+",
        null=True,
        help_text=_(
            "Fill in the appropriate headers for the chosen API service below."
        ),
    )

    # I connect headers
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

    # centric headers
    x_request_organization = models.CharField(
        _("API 'organization' header"),
        max_length=64,
        blank=True,
        help_text=_("Value of the 'x-request-organization' header"),
    )
    x_request_application = models.CharField(
        _("API 'application' header"),
        max_length=64,
        blank=True,
        help_text=_("Value of the 'x-request-application' header"),
    )
    x_request_afnemerscode = models.CharField(
        _("API 'afnemerscode' header"),
        max_length=64,
        blank=True,
        help_text=_("Value of the 'x-request-afnemerscode' header"),
    )
    x_request_user = models.CharField(
        _("API 'user' header"),
        max_length=64,
        blank=True,
        help_text=_("Value of the 'x-request-user' header"),
    )

    objects = HaalCentraalConfigManager()

    def clean(self):
        i_connect_values = (
            self.api_origin_oin
            or self.api_afnemer_oin
            or self.api_doelbinding
            or self.api_verwerking
        )
        centric_values = (
            self.x_request_organization
            or self.x_request_application
            or self.x_request_afnemerscode
            or self.x_request_user
        )

        if i_connect_values and centric_values:
            raise ValidationError(
                _(
                    "You can only define headers for one type of Haalcentraal service, not both"
                )
            )

    class Meta:
        verbose_name = _("Haal Centraal configuration")
