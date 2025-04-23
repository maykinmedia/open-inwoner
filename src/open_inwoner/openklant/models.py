from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_jsonform.models.fields import ArrayField
from ordered_model.models import OrderedModel, OrderedModelManager
from solo.models import SingletonModel
from zgw_consumers.constants import APITypes

from open_inwoner.utils.validators import validate_array_contents_non_empty

from .constants import KlantenServiceType


class ESuiteKlantConfigManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("klanten_service", "contactmomenten_service")


class ESuiteKlantConfig(SingletonModel):
    """
    Configuration and defaults for eSuite Klant & Contactmomenten APIs
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
    send_klantcontact_confirmation_email = models.BooleanField(
        verbose_name=_("Send confirmation email for registration of klantcontact"),
        default=False,
        help_text=_(
            "If enabled, a confirmation email will be sent upon registering a klantcontact."
        ),
    )

    register_api_required_fields = (
        "contactmomenten_service",
        "klanten_service",
        "register_bronorganisatie_rsin",
        "register_type",
    )

    objects = ESuiteKlantConfigManager()

    class Meta:
        verbose_name = _("eSuite Klant configuration")

    @property
    def has_api_configuration(self):
        return all(getattr(self, f, "") for f in self.register_api_required_fields)


class ContactFormSubject(OrderedModel):
    subject = models.CharField(
        verbose_name=_("Onderwerp"),
        max_length=255,
    )
    esuite_subject_code = models.CharField(
        verbose_name=_("e-Suite 'onderwerp' code"),
        max_length=255,
        null=True,
        blank=True,
    )
    esuite_config = models.ForeignKey(
        "ESuiteKlantConfig",
        null=True,
        on_delete=models.CASCADE,
    )
    openklant_config = models.ForeignKey(
        "OpenKlant2Config",
        null=True,
        on_delete=models.CASCADE,
    )

    order_with_respect_to = "esuite_config"

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


class OpenKlant2Config(SingletonModel):
    service = models.OneToOneField(
        "zgw_consumers.Service",
        verbose_name=_("Klanten API"),
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )

    # Vragen
    mijn_vragen_kanaal = models.CharField(
        verbose_name=_("Mijn vragen kanaal"),
        default="",
        blank=True,
        help_text=_(
            "Het kanaal waaronder nieuwe vragen als Klantcontact object zullen worden aangemaakt"
        ),
    )
    mijn_vragen_organisatie_naam = models.CharField(
        verbose_name=_("Mijn vragen organisatie naam"),
        default="",
        blank=True,
    )
    mijn_vragen_actor = models.CharField(
        verbose_name=_("Mijn vragen actor"),
        default="",
        blank=True,
        help_text=_(
            "De UUID van een bestaande Actor in de de configureerde API waaraan nieuwe vragen worden toegewezen"
        ),
    )
    interne_taak_gevraagde_handeling = models.CharField(
        verbose_name=_("Interne taak gevraagde handeling"),
        default="",
        blank=True,
        help_text=_(
            "Beschrijving van de gevraagde handeling voor de interne taak die ontstaat als resultaat van een vraag"
        ),
    )
    interne_taak_toelichting = models.CharField(
        verbose_name=_("Interne taak toelichting"),
        default="",
        blank=True,
        help_text=_(
            "Toelichting bij de gevraagde handeling voor de interne taak die ontstaat als resultaat van een vraag"
        ),
    )

    register_api_required_fields = ("service",)

    @property
    def has_api_configuration(self):
        return all(getattr(self, f, False) for f in self.register_api_required_fields)

    class Meta:
        verbose_name = _("OpenKlant2 configuration")


# Deprecated in favor of `validate_backend_choice`, which has more general use
# TODO: Can be removed after migration openklant.0024_alter_klantensysteemconfig_primary_backend has been squashed
def validate_primary_backend(value):
    if value == KlantenServiceType.OPENKLANT2.value:
        config = OpenKlant2Config.get_solo()
        if not config.service:
            raise ValidationError(
                "OpenKlant2 must be configured with a Klanten API service before it can be selected "
                "as backend"
            )
        return

    config = ESuiteKlantConfig.get_solo()
    if not config.klanten_service:
        raise ValidationError(
            "The Esuite klant system must be configured with a Klanten API service before it can be selected "
            "as backend"
        )
    if not config.contactmomenten_service:
        raise ValidationError(
            "The Esuite klant system must be configured with a Contactmomenten API service service before "
            "it can be selected as backend"
        )


def validate_backend_choice(value):
    if value == KlantenServiceType.OPENKLANT2.value:
        config = OpenKlant2Config.get_solo()
        if not config.service:
            raise ValidationError(
                "OpenKlant2 must be configured with a Klanten API service before it can be selected "
                "as backend"
            )
        return

    config = ESuiteKlantConfig.get_solo()
    if not config.klanten_service:
        raise ValidationError(
            "The Esuite klant system must be configured with a Klanten API service before it can be selected "
            "as backend"
        )
    if not config.contactmomenten_service:
        raise ValidationError(
            "The Esuite klant system must be configured with a Contactmomenten API service service before "
            "it can be selected as backend"
        )


class KlantenSysteemConfig(SingletonModel):
    primary_backend = models.CharField(
        verbose_name=_("Primary backend"),
        blank=True,
        max_length=10,
        choices=[(service.value, service.name) for service in KlantenServiceType],
        help_text=_(
            "Choose the primary backend for retrieving klanten data. "
            "Changes to klanten data will be saved to both backends (if configured)."
        ),
        validators=[validate_backend_choice],
    )
    register_contact_via_api = models.BooleanField(
        verbose_name=_("Registreer op API"),
        default=False,
        help_text=_(
            "Contacts initiated or questions submitted by a client (e.g. via a contact form) will be "
            "registered in the appropriate API (eSuite or OpenKlant2)."
        ),
    )
    register_contact_email = models.EmailField(
        verbose_name=_("Registreer op email adres"),
        blank=True,
        help_text=_(
            "Contacts initiated or questions submitted by a client (e.g. via a contact form) will be "
            "registered via email."
        ),
    )
    send_email_confirmation = models.BooleanField(
        verbose_name=_("Stuur contactformulier e-mailbevestiging"),
        help_text=_(
            "If enabled the 'contactform_confirmation' email template will be sent. "
            "If disabled the external API will send a confirmation email."
        ),
        default=False,
    )

    class Meta:
        verbose_name = _("Configuratie Klanten Systeem")

    def __str__(self):
        return "Configuratie Klanten Systeem"

    @property
    def has_api_configuration(self) -> bool:
        match self.primary_backend:
            case KlantenServiceType.ESUITE.value:
                config = ESuiteKlantConfig.get_solo()
            case KlantenServiceType.OPENKLANT2.value:
                config = OpenKlant2Config.get_solo()
            case _:
                config = None
        return getattr(config, "has_api_configuration", False)

    @property
    def contact_registration_enabled(self) -> bool:
        return bool(self.register_contact_email or self.has_api_configuration)

    @property
    def has_contactform_configuration(self) -> bool:
        contactform_subjects = ContactFormSubject.objects.filter(
            esuite_subject_code__isnull=self.primary_backend
            != KlantenServiceType.ESUITE.value
        )
        return self.contact_registration_enabled and contactform_subjects.exists()
