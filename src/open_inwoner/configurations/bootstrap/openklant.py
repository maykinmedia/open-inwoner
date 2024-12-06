from django.core.exceptions import ValidationError

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from open_inwoner.configurations.bootstrap.utils import get_service
from open_inwoner.openklant.models import OpenKlantConfig


class KlantenApiConfigurationModel(ConfigurationModel):
    klanten_service_identifier: str
    contactmomenten_service_identifier: str
    exclude_contactmoment_kanalen: list[str] | None = DjangoModelRef(
        OpenKlantConfig,
        "exclude_contactmoment_kanalen",
        default=None,
    )

    class Meta:
        django_model_refs = {
            OpenKlantConfig: (
                "register_email",
                "register_contact_moment",
                "register_bronorganisatie_rsin",
                "register_channel",
                "register_type",
                "register_employee_id",
                "use_rsin_for_innNnpId_query_parameter",
                "send_email_confirmation",
            )
        }


class OpenKlantConfigurationStep(BaseConfigurationStep[KlantenApiConfigurationModel]):
    """
    Configure the KIC settings and set any feature flags or other options if specified
    """

    verbose_name = "Klantinteractie APIs configuration"
    enable_setting = "openklant_config_enable"
    namespace = "openklant_config"
    config_model = KlantenApiConfigurationModel

    def execute(self, model: KlantenApiConfigurationModel):
        config = OpenKlantConfig.get_solo()

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
                "Unable to validate and save configuration"
            ) from exc
