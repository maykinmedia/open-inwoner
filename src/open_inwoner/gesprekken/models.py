from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class MijnGesprekkenConfig(SingletonModel):
    """
    Configuration of "Mijn gesprekken": conversations about a zaak, kept in a
    Gesprekken API (draft MijnGesprekken standard).
    """

    enabled = models.BooleanField(
        verbose_name=_("Ingeschakeld"),
        default=False,
        help_text=_(
            "Toon de sectie 'Mijn gesprekken' op de detailpagina van een zaak."
        ),
    )
    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Gesprekken API"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    organisatie_naam = models.CharField(
        verbose_name=_("Naam organisatie"),
        max_length=255,
        blank=True,
        default="",
        help_text=_(
            "Getoond als afzender van bijdragen van medewerkers. Laat leeg om de "
            "naam uit de siteconfiguratie te gebruiken."
        ),
    )
    burger_mag_gesprek_starten = models.BooleanField(
        verbose_name=_("Inwoner mag een gesprek starten"),
        default=False,
        help_text=_(
            "Toon op een open zaak een formulier om een nieuw gesprek te starten. "
            "Standaard start alleen de gemeente een gesprek. Werkt alleen met een "
            "ontvanger hieronder en een bekende Partij in Klantinteracties."
        ),
    )
    ontvanger_actor_url = models.URLField(
        verbose_name=_("Ontvanger van nieuwe gesprekken (Actor)"),
        max_length=1000,
        blank=True,
        default="",
        help_text=_(
            "URL van de Actor (Klantinteracties API) die een gesprek ontvangt dat "
            "de inwoner start. Voorlopig één vaste Actor: wie per zaak de ontvanger "
            "is, is nog een open vraag (C1)."
        ),
    )
    ontvanger_actor_naam = models.CharField(
        verbose_name=_("Naam van de ontvanger"),
        max_length=255,
        blank=True,
        default="",
        help_text=_("Weergavenaam van deze Actor in het gesprek."),
    )
    bijlagen_ingeschakeld = models.BooleanField(
        verbose_name=_("Bijlagen ingeschakeld"),
        default=False,
        help_text=_(
            "De inwoner mag een bijlage toevoegen aan een gespreksbijdrage. De "
            "Gesprekken API slaat het bestand op."
        ),
    )
    email_vertraging_minuten = models.PositiveIntegerField(
        verbose_name=_("Vertraging e-mailmelding (minuten)"),
        default=10,
        help_text=_(
            "Na een nieuwe bijdrage van de gemeente krijgt de inwoner pas een "
            "e-mail als hij de bijdrage na deze tijd nog niet heeft gezien."
        ),
    )
    polling_interval_seconden = models.PositiveIntegerField(
        verbose_name=_("Verversinterval (seconden)"),
        default=5,
        help_text=_("Hoe vaak de pagina controleert of er iets is veranderd."),
    )

    class Meta:
        verbose_name = _("Mijn gesprekken configuratie")

    @property
    def is_active(self) -> bool:
        return self.enabled and self.service_id is not None

    @property
    def heeft_ontvanger(self) -> bool:
        return bool(self.ontvanger_actor_url and self.ontvanger_actor_naam)


class GesprekkenEventStroom(SingletonModel):
    """
    Where the portal is in the event stream of the Gesprekken API: the id of the
    last event it processed, sent as Last-Event-ID when it (re)connects.
    """

    cursor = models.CharField(_("Cursor"), max_length=100, blank=True, default="")
    bijgewerkt_op = models.DateTimeField(_("Bijgewerkt op"), auto_now=True)

    class Meta:
        verbose_name = _("Gesprekken eventstroom")


class VerwerktGesprekEvent(models.Model):
    """
    An event of the event stream that was processed. Events can arrive more than
    once; the CloudEvent id identifies duplicates.
    """

    event_id = models.CharField(_("Event id"), max_length=100, unique=True)
    verwerkt_op = models.DateTimeField(_("Verwerkt op"), auto_now_add=True)

    class Meta:
        verbose_name = _("Verwerkt gesprekevent")
        verbose_name_plural = _("Verwerkte gesprekevents")


class GesprekGezien(models.Model):
    """
    The last time a user saw a gesprek in the portal. Decides whether a new
    bijdrage of the municipality still needs an e-mail notification.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gesprek_url = models.URLField(_("Gesprek"), max_length=1000)
    gezien_op = models.DateTimeField(_("Gezien op"))

    class Meta:
        verbose_name = _("Gezien gesprek")
        verbose_name_plural = _("Geziene gesprekken")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "gesprek_url"], name="unique_user_gesprek_gezien"
            )
        ]
