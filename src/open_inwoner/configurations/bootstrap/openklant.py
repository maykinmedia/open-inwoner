from django.core.exceptions import ValidationError
from django.db.models import Q

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from pydantic import UUID4, Field
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from open_inwoner.configurations.bootstrap.utils import get_service
from open_inwoner.openklant.models import (
    ContactFormSubject,
    ESuiteKlantConfig,
    KlantenSysteemConfig,
    OpenKlant2Config,
)


class ContactFormSubjectConfigurationModel(ConfigurationModel):
    """
    A single selectable subject ("onderwerp") on the contact form.

    `ContactForm` refuses to render without at least one for the active backend
    (its `subject` field has no choices otherwise), so this is not optional in
    practice, just modelled as a list for deployments with more than one.
    """

    subject: str
    esuite_subject_code: str | None = Field(
        default=None,
        description=(
            "The e-Suite 'onderwerp' code this maps to. Required for an eSuite "
            "subject; must stay unset for an OpenKlant2 one, since `ContactForm` "
            "picks the subjects it offers by whether this is set at all."
        ),
    )


class OpenKlant2ConfigurationModel(ConfigurationModel):
    service_identifier: str = DjangoModelRef(OpenKlant2Config, "service")
    mijn_vragen_actor: UUID4 = DjangoModelRef(OpenKlant2Config, "mijn_vragen_actor")
    subjects: list[ContactFormSubjectConfigurationModel] | None = Field(default=None)

    class Meta:
        django_model_refs = {
            OpenKlant2Config: (
                "mijn_vragen_kanaal",
                "mijn_vragen_organisatie_naam",
                "interne_taak_gevraagde_handeling",
                "interne_taak_toelichting",
            )
        }


class EsuiteKlantConfigurationModel(ConfigurationModel):
    klanten_service_identifier: str
    contactmomenten_service_identifier: str
    exclude_contactmoment_kanalen: list[str] | None = DjangoModelRef(
        ESuiteKlantConfig,
        "exclude_contactmoment_kanalen",
        default=None,
    )
    subjects: list[ContactFormSubjectConfigurationModel] | None = Field(default=None)

    class Meta:
        django_model_refs = {
            ESuiteKlantConfig: (
                "register_bronorganisatie_rsin",
                "register_channel",
                "register_type",
                "register_employee_id",
                "use_rsin_for_innNnpId_query_parameter",
            )
        }


class KlantenSysteemConfigurationModel(ConfigurationModel):
    esuite_config: EsuiteKlantConfigurationModel | None = Field(default=None)
    openklant2_config: OpenKlant2ConfigurationModel | None = Field(default=None)

    class Meta:
        django_model_refs = {
            KlantenSysteemConfig: (
                "primary_backend",
                "register_contact_via_api",
                "register_contact_email",
                "send_email_confirmation",
            )
        }


class KlantenSysteemConfigurationStep(
    BaseConfigurationStep[KlantenSysteemConfigurationModel]
):
    """
    Configuration related to connecting Open Inwoner to a backend for storing
    customer and contact information.
    """

    verbose_name = "KlantenSysteem configuration"
    enable_setting = "klantensysteem_config_enable"
    namespace = "klantensysteem_config"
    config_model = KlantenSysteemConfigurationModel

    def execute(self, model: KlantenSysteemConfigurationModel):
        # Configure eSuite if provided
        if model.esuite_config:
            self._configure_esuite(model.esuite_config)

        # Configure OpenKlant2 if provided
        if model.openklant2_config:
            self._configure_openklant2(model.openklant2_config)

        # Configure KlantenSysteem
        config = KlantenSysteemConfig.get_solo()

        for key, val in model.model_dump(
            exclude={"esuite_config", "openklant2_config"}
        ).items():
            setattr(config, key, val)

        try:
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                "Unable to validate and save KlantenSysteemConfig"
            ) from exc

    def _configure_esuite(self, model: EsuiteKlantConfigurationModel):
        """Configure eSuite Klant APIs"""
        config = ESuiteKlantConfig.get_solo()

        try:
            kc = get_service(model.klanten_service_identifier)
            if kc.api_type != APITypes.kc:
                raise ConfigurationRunFailed(
                    f"Found klanten service with identifier `{kc.slug}`, but expected"
                    f" `api_type` to equal `{APITypes.kc}` and got `{kc.api_type}`"
                )
            config.klanten_service = kc

            cm = get_service(model.contactmomenten_service_identifier)
            if cm.api_type != APITypes.cmc:
                raise ConfigurationRunFailed(
                    f"Found contactmomenten service with identifier `{cm.slug}`, but"
                    f" expected `api_type` to equal `{APITypes.cmc}` and got "
                    f"`{cm.api_type}`"
                )

            config.contactmomenten_service = cm
        except Service.DoesNotExist as exc:
            raise ConfigurationRunFailed(
                "Unable to retrieve `klanten_service` and/or `contactmomenten_service`"
                ". Try first configuring the `zgw_consumers` configuration steps, and."
                " ensure that both the `identifier` and `api_type` fields match."
            ) from exc

        for key, val in model.model_dump(
            exclude={
                "klanten_service_identifier",
                "contactmomenten_service_identifier",
                "subjects",
            }
        ).items():
            setattr(config, key, val)

        try:
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                "Unable to validate and save ESuiteKlantConfig"
            ) from exc

        self._sync_subjects(model.subjects, esuite_config=config)

    def _sync_subjects(
        self,
        subjects: list[ContactFormSubjectConfigurationModel] | None,
        *,
        esuite_config: ESuiteKlantConfig | None = None,
        openklant_config: OpenKlant2Config | None = None,
    ) -> None:
        """
        Replace the contact-form subjects offered to this backend to match `subjects`.

        Left alone when `subjects` is omitted (``None``), the same rule this step
        follows for everything else it doesn't explicitly manage; pass an empty
        list to clear them instead. Replacing rather than diffing keeps this in
        line with the rest of the step, which always overwrites to match rather
        than reconciling field by field.

        Also clears subjects with both FKs unset -- rows predating the migration
        that introduced `esuite_config`/`openklant_config`, still offered by
        `ContactForm` (which picks a backend's subjects by
        `esuite_subject_code__isnull` alone, not by either FK) but invisible to
        every other lookup in this codebase. Which backend they belong to is
        judged the same way the form does.

        Checked here rather than on `ContactFormSubjectConfigurationModel` itself:
        a pydantic validator can't tell which parent field it's nested under, and
        the sphinx directive that renders this step's example YAML instantiates
        every model in isolation, so a validator rejecting the combination in one
        context would also reject the auto-generated example for the other.
        """
        if subjects is None:
            return

        is_esuite = esuite_config is not None
        wrong_backend = [
            s.subject for s in subjects if bool(s.esuite_subject_code) != is_esuite
        ]
        if wrong_backend:
            config_field = "esuite_config" if is_esuite else "openklant2_config"
            requirement = (
                "have `esuite_subject_code` set"
                if is_esuite
                else "leave `esuite_subject_code` unset"
            )
            raise ConfigurationRunFailed(
                f"Every subject under `{config_field}` must {requirement}; "
                "ContactForm decides which backend offers a subject by whether "
                f"it's set. Affected subjects: {', '.join(wrong_backend)}."
            )

        belongs_to_this_backend = Q(esuite_subject_code__isnull=esuite_config is None)
        orphaned = Q(esuite_config__isnull=True, openklant_config__isnull=True)
        ContactFormSubject.objects.filter(
            Q(esuite_config=esuite_config, openklant_config=openklant_config)
            | (orphaned & belongs_to_this_backend)
        ).delete()
        for subject in subjects:
            ContactFormSubject.objects.create(
                subject=subject.subject,
                esuite_subject_code=subject.esuite_subject_code,
                esuite_config=esuite_config,
                openklant_config=openklant_config,
            )

    def _configure_openklant2(self, model: OpenKlant2ConfigurationModel):
        """Configure OpenKlant2 APIs"""
        try:
            service = get_service(model.service_identifier)
        except Service.DoesNotExist as exc:
            raise ConfigurationRunFailed(
                "Unable to retrieve Service with identifier"
                f" `{model.service_identifier}`. Try first configuring the `zgw_consum"
                "ers` configuration steps."
            ) from exc

        create_or_update_kwargs = model.model_dump(
            exclude={"service_identifier", "subjects"}
        ) | {"service": service}

        config = OpenKlant2Config.get_solo()

        for key, val in create_or_update_kwargs.items():
            setattr(config, key, val)

        try:
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                "Unable to validate and save OpenKlant2Config"
            ) from exc

        self._sync_subjects(model.subjects, openklant_config=config)
