from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class MijnAfvalConfig(SingletonModel):
    openafval_service = models.OneToOneField(
        to="zgw_consumers.Service",
        verbose_name=_("OpenAfval API service"),
        limit_choices_to={"api_type": APITypes.orc},
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Configuratie Mijn Afval")
