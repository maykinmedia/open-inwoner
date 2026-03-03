from django.db import models
from django.utils.translation import gettext_lazy as _

from django_prosemirror.fields import ProsemirrorModelField
from django_prosemirror.schema import MarkType, NodeType
from solo.models import SingletonModel

from open_inwoner.configurations.models import SiteConfiguration
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
        help_text=_(
            "The text displayed as overview of the 'Mijn Uitkeringen' section."
        ),
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
    jaaropgave_display_text = ProsemirrorModelField(
        _("Display text"),
        allowed_node_types=[NodeType.HARD_BREAK, NodeType.PARAGRAPH],
        allowed_mark_types=[
            MarkType.STRONG,
            MarkType.ITALIC,
            MarkType.UNDERLINE,
            MarkType.LINK,
        ],
        null=True,
        blank=True,
        help_text=_("The text displayed as overview of the 'Jaaropgave' tab"),
    )
    jaaropgave_pdf_comments = ProsemirrorModelField(
        _("PDF help text"),
        allowed_node_types=[NodeType.HARD_BREAK, NodeType.PARAGRAPH],
        allowed_mark_types=[],
        null=True,
        blank=True,
        help_text=_(
            "Optional comments to be included in the jaaropgave PDF. Markdown formatting is supported."
        ),
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
    maandspecificatie_display_text = ProsemirrorModelField(
        _("Display text"),
        allowed_node_types=[NodeType.HARD_BREAK, NodeType.PARAGRAPH],
        allowed_mark_types=[
            MarkType.STRONG,
            MarkType.ITALIC,
            MarkType.UNDERLINE,
            MarkType.LINK,
        ],
        null=True,
        blank=True,
        help_text=_("The text displayed as overview of the 'Maandspecificatie' tab"),
    )
    maandspecificatie_pdf_comments = ProsemirrorModelField(
        _("PDF help text"),
        allowed_node_types=[NodeType.HARD_BREAK, NodeType.PARAGRAPH],
        allowed_mark_types=[],
        null=True,
        blank=True,
        help_text=_(
            "Optional comments to be included in the maandspecificatie PDF. "
            "Markdown formatting is supported."
        ),
    )

    @property
    def logo(self):
        return SiteConfiguration.get_solo().logo

    class Meta:
        verbose_name = _("SSD")
