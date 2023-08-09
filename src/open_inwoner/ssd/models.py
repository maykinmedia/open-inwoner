from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from ..configurations.models import SiteConfiguration
from ..utils.validators import CharFieldValidator, validate_digits


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
    maandspecificatie_endpoint = models.CharField(
        _("Maandspecificatie endpoint"),
        max_length=256,
        default=("UitkeringsSpecificatieClient-v0600"),
        help_text=_("Endpoint for the maandspecificatie request"),
    )
    jaaropgave_endpoint = models.CharField(
        _("Jaaropgave endpoint"),
        max_length=256,
        default=("JaarOpgaveClient-v0400"),
        help_text=_("Endpoint for the jaaropgave request"),
    )
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
    mijn_uitkeringen_text = models.TextField(
        _("Overview text"),
        blank=True,
        help_text=_("The text displayed as overview of the 'Mijn Uikeringen' section."),
    )
    # report options (jaaropgave)
    jaaropgave_enabled = models.BooleanField(
        _("Enable download"),
        default=True,
    )
    jaaropgave_delta = models.SmallIntegerField(
        _("Show reports for the last # years"),
        default=3,
    )
    jaaropgave_available_from = models.CharField(
        _("Yearly report available from (dd-mm)"),
        max_length=5,
        default="29-01",
        help_text=_(
            "Day and month from when the report for the preceding year is available for download"
        ),
    )
    jaaropgave_display_text = models.TextField(
        _("Display text"),
        blank=True,
        help_text=_("The text displayed as overview of the 'Jaaropgave' tab"),
    )
    jaaropgave_comments = models.TextField(
        _("PDF help text"),
        blank=True,
        help_text=_("Help text for the columns in the Jaaropgave PDF"),
    )
    # report options (maandspecificatie)
    maandspecificatie_enabled = models.BooleanField(
        _("Enable download"),
        default=True,
    )
    maandspecificatie_delta = models.SmallIntegerField(
        _("Show reports for the last # months"),
        default=12,
    )
    maandspecificatie_available_from = models.SmallIntegerField(
        _("Report available from the # day of the month"),
        default=25,
        help_text=_(
            "Day of the month from when the report for the preceding month is available for download"
        ),
    )
    maandspecificatie_display_text = models.TextField(
        _("Display text"),
        blank=True,
        help_text=_("The text displayed as overview of the 'Maandspecificatie' tab"),
    )

    @property
    def logo(self):
        return SiteConfiguration.get_solo().logo

    class Meta:
        verbose_name = _("SSD")
