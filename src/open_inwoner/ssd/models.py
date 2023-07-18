from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from open_inwoner.utils.validators import CharFieldValidator, validate_digits


class SSDConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("service")


class SSDConfig(SingletonModel):
    service = models.ForeignKey(
        "soap.SoapService",
        verbose_name=_("SOAP service"),
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    # basic configuration
    applicatie_naam = models.CharField(
        _("Application name"),
        max_length=32,
        help_text=_("Name of the application"),
        validators=[CharFieldValidator],
        blank=True,
    )
    bedrijfs_naam = models.CharField(
        _("Company name"),
        max_length=32,
        help_text=_("Name of the supplier"),
        validators=[CharFieldValidator],
        blank=True,
    )
    gemeentecode = models.CharField(
        _("Municipality code"),
        max_length=4,
        help_text=_("Municipality code to register zaken"),
        validators=[validate_digits],
        blank=True,
    )

    # report options
    jaaropgave_enabled = models.BooleanField(
        _("Enable download of yearly reports"),
        default=True,
    )
    jaaropgave_range = models.SmallIntegerField(
        _("Show yearly reports for the last # years"),
        default=3,
    )
    jaaropgave_available_from = models.CharField(
        _("Yearly report available from (dd-mm)"),
        max_length=5,
        default="29-01",
        help_text=_(
            "Month from when the report for the preceding year is available for download"
        ),
    )
    maandspecificatie_enabled = models.BooleanField(
        _("Enable download of monthly reports"),
        default=True,
    )
    maandspecificatie_range = models.SmallIntegerField(
        _("Show yearly reports for the last # months"),
        default=12,
    )
    maandspecificatie_available_from = models.SmallIntegerField(
        _("Monthly report available from the # day of the month"),
        default=25,
        help_text=_(
            "Day of the month from when the report for the preceding month is available for download"
        ),
    )

    class Meta:
        verbose_name = _("SSD")
