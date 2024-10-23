import uuid
from dataclasses import dataclass
from typing import Self
from urllib.parse import urljoin

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_jsonform.models.fields import ArrayField
from ordered_model.models import OrderedModel, OrderedModelManager
from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from open_inwoner.utils.validators import validate_array_contents_non_empty


class OpenKlantConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("klanten_service", "contactmomenten_service")


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
        blank=True,
    )
    contactmomenten_service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Contactmomenten API"),
        on_delete=models.PROTECT,
        limit_choices_to={"api_type": APITypes.cmc},
        related_name="+",
        null=True,
        blank=True,
    )

    register_email = models.EmailField(
        verbose_name=_("Registreer op email adres"),
        blank=True,
    )
    register_contact_moment = models.BooleanField(
        verbose_name=_("Registreer in Contactmomenten API"),
        default=False,
    )
    register_bronorganisatie_rsin = models.CharField(
        verbose_name=_("Organisatie RSIN"),
        max_length=9,
        default="",
        blank=True,
    )
    register_channel = models.CharField(
        verbose_name=_("Contactmoment kanaal"),
        max_length=50,
        default="contactformulier",
        blank=True,
        help_text=_("The channel through which contactmomenten are created"),
    )
    register_type = models.CharField(
        verbose_name=_("Contactmoment type"),
        max_length=50,
        default="Melding",  # 'Melding' is the default
        blank=True,
        help_text=_("Naam van 'contacttype' uit e-Suite"),
    )
    register_employee_id = models.CharField(
        verbose_name=_("Medewerker identificatie"),
        max_length=24,
        default="",
        blank=True,
        help_text=_("Gebruikersnaam van actieve medewerker uit e-Suite"),
    )

    use_rsin_for_innNnpId_query_parameter = models.BooleanField(
        verbose_name=_(
            "Fetch resources from Klanten and Contactmomenten APIs for users authenticated with eHerkenning using RSIN"
        ),
        help_text=_(
            "If enabled, resources from the Klanten and Contactmomenten APIs for eHerkenning "
            "users are fetched using the company RSIN (Open Klant). "
            "If not enabled, these resources are fetched using the KvK number."
        ),
        default=False,
    )
    send_email_confirmation = models.BooleanField(
        verbose_name=_("Stuur contactformulier e-mailbevestiging"),
        help_text=_(
            "If enabled the 'contactform_confirmation' email template will be sent. "
            "If disabled the external API will send a confirmation email."
        ),
        default=False,
    )
    exclude_contactmoment_kanalen = ArrayField(
        base_field=models.CharField(
            blank=True,
            max_length=100,
            help_text=_(
                "Contactmomenten registered via one of these channels will not be "
                "displayed to users."
            ),
        ),
        null=True,
        blank=True,
        default=list,
        validators=[validate_array_contents_non_empty],
    )

    register_api_required_fields = (
        "register_contact_moment",
        "contactmomenten_service",
        "klanten_service",
        "register_bronorganisatie_rsin",
        "register_type",
    )

    objects = OpenKlantConfigManager()

    class Meta:
        verbose_name = _("Open Klant configuration")

    def has_register(self) -> bool:
        return self.register_email or self.has_api_configuration()

    def has_form_configuration(self) -> bool:
        return self.has_register() and self.contactformsubject_set.exists()

    def has_api_configuration(self):
        return all(getattr(self, f, "") for f in self.register_api_required_fields)


class ContactFormSubject(OrderedModel):
    subject = models.CharField(
        verbose_name=_("Onderwerp"),
        max_length=255,
    )
    subject_code = models.CharField(
        verbose_name=_("e-Suite 'onderwerp' code"),
        max_length=255,
        blank=True,
    )
    # FK for easy inline admins
    config = models.ForeignKey(
        OpenKlantConfig,
        on_delete=models.CASCADE,
    )

    order_with_respect_to = "config"

    objects = OrderedModelManager()

    class Meta(OrderedModel.Meta):
        verbose_name = _("Contact formulier onderwerp")
        verbose_name_plural = _("Contact formulier onderwerpen")
        ordering = ("order",)

    def __str__(self):
        return self.subject


class KlantContactMomentAnswer(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="contactmoment_answers",
        help_text=_(
            "This is the user that asked the question to which this is an answer."
        ),
    )
    contactmoment_url = models.URLField(
        verbose_name=_("ContactMoment URL"), max_length=1000
    )
    is_seen = models.BooleanField(
        verbose_name=_("Is seen"),
        help_text=_("Whether or not the user has seen the answer"),
        default=False,
    )

    class Meta:
        verbose_name = _("KlantContactMoment")
        verbose_name_plural = _("KlantContactMomenten")
        unique_together = [["user", "contactmoment_url"]]


@dataclass
class OpenKlant2Config:
    api_root: str
    api_path: str
    api_token: str

    # Question/Answer settings
    mijn_vragen_kanaal: str
    mijn_vragen_organisatie_naam: str
    mijn_vragen_actor: str | uuid.UUID | None
    interne_taak_gevraagde_handeling: str
    interne_taak_toelichting: str

    @property
    def api_url(self):
        return urljoin(self.api_root, self.api_path)

    @classmethod
    def from_django_settings(cls) -> Self:
        from django.conf import settings

        if not (config := getattr(settings, "OPENKLANT2_CONFIG", None)):
            raise ImproperlyConfigured(
            raise RuntimeError(
                "Please set OPENKLANT2_CONFIG in your settings to configure OpenKlant2"
            )

        return cls(**config)
