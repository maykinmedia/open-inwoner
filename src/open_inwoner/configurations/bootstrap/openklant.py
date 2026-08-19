from django.core.exceptions import ValidationError

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from pydantic import UUID4, Field
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from open_inwoner.configurations.bootstrap.utils import get_service
from open_inwoner.openklant.models import (
    ESuiteKlantConfig,
    KlantenSysteemConfig,
    OpenKlant2Config,
)


class OpenKlant2ConfigurationModel(ConfigurationModel):
    service_identifier: str = DjangoModelRef(OpenKlant2Config, "service")
    mijn_vragen_actor: UUID4 = DjangoModelRef(OpenKlant2Config, "mijn_vragen_actor")

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

        create_or_update_kwargs = model.model_dump(exclude={"service_identifier"}) | {
            "service": service
        }

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
