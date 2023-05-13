from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class OpenKlantConfig(SingletonModel):
    """
    Global configuration and defaults for Klant & Contactmomenten APIs
    """

    klanten_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Klanten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.kc},
        related_name="+",
        null=True,
    )
    contactmomenten_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Contactmomenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.cmc},
        related_name="+",
        null=True,
    )

    class Meta:
        verbose_name = _("Open Klant configuration")
