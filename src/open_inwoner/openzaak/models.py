from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes


class OpenZaakConfigManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("service")


class OpenZaakConfig(SingletonModel):
    """
    Global configuration and defaults
    """

    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Open Zaak API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.zrc},
        related_name="+",
        null=True,
    )

    objects = OpenZaakConfigManager()

    class Meta:
        verbose_name = _("Open Zaak configuration")
