from django.core.exceptions import ValidationError

from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from open_inwoner.configurations.bootstrap.utils import get_service
from open_inwoner.mijn_afval.models import MijnAfvalConfig


class MijnAfvalConfigurationModel(ConfigurationModel):
    """Configuration for the Open Afval API backing the "Mijn afval" page."""

    service_identifier: str = DjangoModelRef(MijnAfvalConfig, "openafval_service")


class MijnAfvalConfigurationStep(BaseConfigurationStep):
    """
    Configures the Open Afval API used to look up a resident's waste
    collection data (containers, ledigingen and their costs).
    """

    verbose_name = "Mijn Afval configuration"
    enable_setting = "mijn_afval_config_enable"
    namespace = "mijn_afval_config"
    config_model = MijnAfvalConfigurationModel

    def execute(self, model: MijnAfvalConfigurationModel) -> None:
        config = MijnAfvalConfig.get_solo()

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

        config.openafval_service = service

        try:
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                f"Something went wrong while saving MijnAfvalConfig: {exc}"
            ) from exc
