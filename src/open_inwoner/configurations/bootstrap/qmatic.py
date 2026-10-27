from django.core.exceptions import ValidationError

from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from open_inwoner.configurations.bootstrap.utils import get_service
from open_inwoner.qmatic.models import QmaticConfig


class QmaticConfigurationModel(ConfigurationModel):
    """Configuration for the Qmatic API backing "Mijn afspraken"."""

    service_identifier: str = DjangoModelRef(QmaticConfig, "service")

    class Meta:
        django_model_refs = {
            QmaticConfig: [
                "booking_base_url",
            ],
        }


class QmaticConfigurationStep(BaseConfigurationStep):
    """
    Configures the Qmatic Orchestra Calendar API used to retrieve a user's
    upcoming appointments for "Mijn afspraken".

    Only the fields present in the YAML source are applied: re-running this
    step, or running it with a YAML source that only lists a handful of
    fields, does not reset the fields it omits back to their defaults.
    """

    verbose_name = "Qmatic configuration"
    enable_setting = "qmatic_config_enable"
    namespace = "qmatic_config"
    config_model = QmaticConfigurationModel

    def execute(self, model: QmaticConfigurationModel) -> None:
        config = QmaticConfig.get_solo()

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
                f"Something went wrong while saving QmaticConfig: {exc}"
            ) from exc
