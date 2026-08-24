from django.core.exceptions import ValidationError

from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from pydantic import Field
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from open_inwoner.configurations.bootstrap.utils import get_service
from open_inwoner.haalcentraal.models import HaalCentraalConfig


class HaalCentraalHeaderConfig(ConfigurationModel):
    """A single request header sent on every Haal Centraal BRP request."""

    key: str
    value: str


class HaalCentraalConfigurationModel(ConfigurationModel):
    """Configuration for the Haal Centraal BRP ("personen") API."""

    service_identifier: str = DjangoModelRef(HaalCentraalConfig, "service")
    # Not DjangoModelRef'd: `headers` is a custom JSONFormField and the nested
    # key/value shape is clearer expressed as its own model than as a bare
    # `list[dict]`.
    headers: list[HaalCentraalHeaderConfig] = Field(default_factory=list)

    class Meta:
        django_model_refs = {
            HaalCentraalConfig: ["brp_version"],
        }


class HaalCentraalConfigurationStep(BaseConfigurationStep):
    """
    Configures the Haal Centraal BRP ("personen") API used to look up
    resident data (BSN lookups, address data, etc).

    Only the fields present in the YAML source are applied: re-running this
    step, or running it with a YAML source that only lists a handful of
    fields, does not reset the fields it omits back to their defaults.
    """

    verbose_name = "Haal Centraal BRP configuration"
    enable_setting = "haalcentraal_config_enable"
    namespace = "haalcentraal_config"
    config_model = HaalCentraalConfigurationModel

    def execute(self, model: HaalCentraalConfigurationModel) -> None:
        config = HaalCentraalConfig.get_solo()

        try:
            service = get_service(model.service_identifier)
        except Service.DoesNotExist as exc:
            raise ConfigurationRunFailed(
                "Unable to retrieve Service with identifier "
                f"`{model.service_identifier}`. Try first configuring the "
                "`zgw_consumers` configuration steps."
            ) from exc

        if service.api_type != APITypes.orc:
            raise ConfigurationRunFailed(
                f"Found service with identifier `{model.service_identifier}`, but "
                f"expected `api_type` to equal `{APITypes.orc}` and got "
                f"`{service.api_type}`."
            )

        config.service = service

        for field, value in model.model_dump(
            exclude={"service_identifier"}, exclude_unset=True
        ).items():
            setattr(config, field, value)

        try:
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                f"Something went wrong while saving HaalCentraalConfig: {exc}"
            ) from exc
