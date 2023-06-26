from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from open_inwoner.utils.validators import CharFieldValidator, validate_digits


class SSDConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("service")


class SSDConfig(SingletonModel):
    service = models.ForeignKey(
        "soap.SoapService",
        verbose_name=_("SOAP Service"),
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    gemeentecode = models.CharField(
        _("Municipality code"),
        max_length=4,
        help_text=_("Municipality code to register zaken"),
        validators=[validate_digits],
        blank=True,
    )

    bedrijfs_naam = models.CharField(
        _("Company Name"),
        max_length=32,
        help_text=_("Name of the supplier"),
        validators=[CharFieldValidator()],
        blank=True,
    )

    applicatie_naam = models.CharField(
        _("Application Name"),
        max_length=32,
        help_text=_("Name of the application"),
        validators=[CharFieldValidator()],
        blank=True,
    )
