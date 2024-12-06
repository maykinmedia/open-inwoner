from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from zgw_consumers.models import Service

from open_inwoner.configurations.bootstrap.utils import get_service
from open_inwoner.openzaak.models import OpenZaakConfig, ZGWApiGroupConfig


class ZGWAPIGroup(ConfigurationModel):
    zaken_api_identifier: str
    documenten_api_identifier: str
    catalogi_api_identifier: str
    form_api_identifier: str | None = None


class OpenZaakConfigurationModel(ConfigurationModel):
    api_groups: list[ZGWAPIGroup]
    allowed_file_extensions: list[str] = DjangoModelRef(
        OpenZaakConfig, "allowed_file_extensions"
    )

    class Meta:
        django_model_refs = {
            OpenZaakConfig: [
                "zaak_max_confidentiality",
                "document_max_confidentiality",
                "max_upload_size",
                "skip_notification_statustype_informeren",
                "reformat_esuite_zaak_identificatie",
                "fetch_eherkenning_zaken_with_rsin",
                "use_zaak_omschrijving_as_title",
                "order_statuses_by_date_set",
                "title_text",
                "enable_categories_filtering_with_zaken",
                "action_required_deadline_days",
                "zaken_filter_enabled",
            ]
        }


class OpenZaakConfigurationStep(BaseConfigurationStep):
    """
    Configure the ZGW settings and set any feature flags or other options if specified
    """

    verbose_name = "Openzaak configuration"
    enable_setting = "openzaak_config_enable"
    namespace = "openzaak_config"
    config_model = OpenZaakConfigurationModel

    def execute(self, model: OpenZaakConfigurationModel):
        if len(model.api_groups) < 1:
            raise ConfigurationRunFailed("Configure at least one `api_groups` item")

        config = OpenZaakConfig.get_solo()

        for api_group in model.api_groups:

            try:
                zrc_service = get_service(
                    api_group.zaken_api_identifier,
                )
                ztc_service = get_service(
                    api_group.catalogi_api_identifier,
                )
                drc_service = get_service(
                    api_group.documenten_api_identifier,
                )
                # Not required
                form_service = (
                    get_service(
                        api_group.form_api_identifier,
                    )
                    if api_group.form_api_identifier
                    else None
                )
            except Service.DoesNotExist as exc:
                raise ConfigurationRunFailed(
                    "You must first ensure all the ZGW Services referenced in this "
                    f"step have been created:\n{str(exc)}"
                )

            ZGWApiGroupConfig.objects.get_or_create(
                open_zaak_config=config,
                zrc_service=zrc_service,
                ztc_service=ztc_service,
                drc_service=drc_service,
                form_service=form_service,
                defaults={"name": "Auto-configured by django-setup-configuration"},
            )

        general_settings = model.model_dump(exclude={"api_groups"})
        for field, val in general_settings.items():
            setattr(config, field, val)

        config.full_clean()
        config.save()
