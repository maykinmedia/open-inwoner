from django.db import models
from django.utils.translation import gettext_lazy as _

from django_jsonform.models.fields import JSONField as JSONFormField
from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from open_inwoner.haalcentraal.validators import validate_no_standard_http_headers


class BrpVersionChoices(models.TextChoices):
    V1_3 = "1.3", _("BRP 1.3")
    V2_0 = "2.0", _("BRP 2.0")
    V2_1 = "2.1", _("BRP 2.1")


HEADERS_SCHEMA = {
    "type": "array",
    "title": "",
    "items": {
        "type": "object",
        "keys": {
            "key": {
                "type": "string",
                "title": _("Header name"),
                "placeholder": "e.g. x-origin-oin",
            },
            "value": {
                "type": "string",
                "title": _("Value"),
            },
        },
    },
}


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
        help_text=_("Configure the request headers for the chosen API service below."),
    )

    headers = JSONFormField(
        verbose_name=_("Request headers"),
        schema=HEADERS_SCHEMA,
        default=list,
        blank=True,
        validators=[validate_no_standard_http_headers],
        help_text=_(
            "Key/value pairs sent as additional HTTP headers on each BRP request. "
            "Refer to your vendor's documentation for more information about these "
            "headers. iConnect example keys: 'x-origin-oin', 'x-afnemer-oin', "
            "'x-doelbinding', 'x-verwerking'. Centric: "
            "'x-request-organization', 'x-request-application', "
            "'x-request-afnemerscode', 'x-request-user'."
        ),
    )

    objects = HaalCentraalConfigManager()

    class Meta:
        verbose_name = _("Haal Centraal configuration")
