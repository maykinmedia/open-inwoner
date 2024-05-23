from django.conf import settings

import requests
from django_setup_configuration.base import ConfigSettingsModel
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import SelfTestFailed
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from open_inwoner.openzaak.clients import build_client
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.utils.api import ClientError


class ZakenAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required Service to establish a connection with the Zaken API
    """

    verbose_name = "Zaken API configuration"
    required_settings = [
        "ZGW_ZAAK_SERVICE_API_ROOT",
        "ZGW_ZAAK_SERVICE_API_CLIENT_ID",
        "ZGW_ZAAK_SERVICE_API_SECRET",
    ]

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.ZGW_ZAAK_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        Service.objects.update_or_create(
            api_root=settings.ZGW_ZAAK_SERVICE_API_ROOT,
            defaults={
                "label": "Zaken API",
                "api_type": APITypes.zrc,
                "oas": settings.ZGW_ZAAK_SERVICE_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.ZGW_ZAAK_SERVICE_API_CLIENT_ID,
                "secret": settings.ZGW_ZAAK_SERVICE_API_SECRET,
                "user_id": settings.ZGW_ZAAK_SERVICE_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )

    def test_configuration(self):
        """
        actual testing is done in final step
        """


class CatalogiAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required Service to establish a connection with the Catalogi API
    """

    verbose_name = "Catalogi API configuration"
    required_settings = [
        "ZGW_CATALOGI_SERVICE_API_ROOT",
        "ZGW_CATALOGI_SERVICE_API_CLIENT_ID",
        "ZGW_CATALOGI_SERVICE_API_SECRET",
    ]

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.ZGW_CATALOGI_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        Service.objects.update_or_create(
            api_root=settings.ZGW_CATALOGI_SERVICE_API_ROOT,
            defaults={
                "label": "Catalogi API",
                "api_type": APITypes.ztc,
                "oas": settings.ZGW_CATALOGI_SERVICE_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.ZGW_CATALOGI_SERVICE_API_CLIENT_ID,
                "secret": settings.ZGW_CATALOGI_SERVICE_API_SECRET,
                "user_id": settings.ZGW_CATALOGI_SERVICE_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )

    def test_configuration(self):
        """
        actual testing is done in final step
        """


class DocumentenAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required Service to establish a connection with the Documenten API
    """

    verbose_name = "Documenten API configuration"
    required_settings = [
        "ZGW_DOCUMENTEN_SERVICE_API_ROOT",
        "ZGW_DOCUMENTEN_SERVICE_API_CLIENT_ID",
        "ZGW_DOCUMENTEN_SERVICE_API_SECRET",
    ]

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.ZGW_DOCUMENTEN_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        Service.objects.update_or_create(
            api_root=settings.ZGW_DOCUMENTEN_SERVICE_API_ROOT,
            defaults={
                "label": "Documenten API",
                "api_type": APITypes.drc,
                "oas": settings.ZGW_DOCUMENTEN_SERVICE_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.ZGW_DOCUMENTEN_SERVICE_API_CLIENT_ID,
                "secret": settings.ZGW_DOCUMENTEN_SERVICE_API_SECRET,
                "user_id": settings.ZGW_DOCUMENTEN_SERVICE_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )

    def test_configuration(self):
        """
        actual testing is done in final step
        """


class FormulierenAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required Service to establish a connection with the Formulieren API
    """

    verbose_name = "Formulieren APIs configuration"
    required_settings = [
        "ZGW_FORM_SERVICE_API_ROOT",
        "ZGW_FORM_SERVICE_API_CLIENT_ID",
        "ZGW_FORM_SERVICE_API_SECRET",
    ]

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.ZGW_FORM_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        Service.objects.update_or_create(
            api_root=settings.ZGW_FORM_SERVICE_API_ROOT,
            defaults={
                "label": "Formulieren API",
                "api_type": APITypes.orc,
                "oas": settings.ZGW_FORM_SERVICE_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.ZGW_FORM_SERVICE_API_CLIENT_ID,
                "secret": settings.ZGW_FORM_SERVICE_API_SECRET,
                "user_id": settings.ZGW_FORM_SERVICE_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )

    def test_configuration(self):
        """
        actual testing is done in final step
        """


class ZGWAPIsConfigurationStep(BaseConfigurationStep):
    """
    Configure the ZGW settings and set any feature flags or other options if specified
    """

    verbose_name = "ZGW APIs configuration"
    enable_setting = "ZGW_CONFIG_ENABLE"
    required_settings = [
        "ZGW_CATALOGI_SERVICE_CLIENT_ID",
        "ZGW_CATALOGI_SERVICE_SECRET",
        "ZGW_CATALOGI_SERVICE_API_ROOT",
        "ZGW_DOCUMENT_SERVICE_CLIENT_ID",
        "ZGW_DOCUMENT_SERVICE_SECRET",
        "ZGW_DOCUMENT_SERVICE_API_ROOT",
        "ZGW_FORM_SERVICE_CLIENT_ID",
        "ZGW_FORM_SERVICE_SECRET",
        "ZGW_FORM_SERVICE_API_ROOT",
        "ZGW_ZAAK_SERVICE_CLIENT_ID",
        "ZGW_ZAAK_SERVICE_SECRET",
        "ZGW_ZAAK_SERVICE_API_ROOT",
    ]
    config_settings = ConfigSettingsModel(
        models=[OpenZaakConfig],
        namespace="ZGW",
        file_name="zgw",
        excluded_fields=(
            "id",
            "api_type",
            "auth_type",
            "client_certificate",
            "header_key",
            "header_value",
            "label",
            "nlx",
            "oas",
            "oas_file",
            "server_certificate",
            "user_id",
            "user_representation",
            "uuid",
        ),
    )

    def is_configured(self) -> bool:
        zgw_config = OpenZaakConfig.get_solo()
        return (
            bool(zgw_config.zaak_service)
            and bool(zgw_config.catalogi_service)
            and bool(zgw_config.document_service)
            and bool(zgw_config.form_service)
        )

    def configure(self):
        config = OpenZaakConfig.get_solo()
        config.zaak_service = Service.objects.get(
            api_root=settings.ZGW_ZAAK_SERVICE_API_ROOT
        )
        config.catalogi_service = Service.objects.get(
            api_root=settings.ZGW_CATALOGI_SERVICE_API_ROOT
        )
        config.document_service = Service.objects.get(
            api_root=settings.ZGW_DOCUMENTEN_SERVICE_API_ROOT
        )
        config.form_service = Service.objects.get(
            api_root=settings.ZGW_FORM_SERVICE_API_ROOT
        )

        # General config options
        if settings.ZGW_ZAAK_MAX_CONFIDENTIALITY:
            config.zaak_max_confidentiality = settings.ZGW_ZAAK_MAX_CONFIDENTIALITY
        if settings.ZGW_DOCUMENT_MAX_CONFIDENTIALITY:
            config.document_max_confidentiality = (
                settings.ZGW_DOCUMENT_MAX_CONFIDENTIALITY
            )
        if settings.ZGW_ACTION_REQUIRED_DEADLINE_DAYS:
            config.action_required_deadline_days = (
                settings.ZGW_ACTION_REQUIRED_DEADLINE_DAYS
            )
        if settings.ZGW_ALLOWED_FILE_EXTENSIONS:
            config.allowed_file_extensions = settings.ZGW_ALLOWED_FILE_EXTENSIONS
        if settings.ZGW_MIJN_AANVRAGEN_TITLE_TEXT:
            config.title_text = settings.ZGW_MIJN_AANVRAGEN_TITLE_TEXT

        # Feature flags
        if settings.ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN is not None:
            config.enable_categories_filtering_with_zaken = (
                settings.ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN
            )

        # eSuite specific options
        if settings.ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN is not None:
            config.skip_notification_statustype_informeren = (
                settings.ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN
            )
        if settings.ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE is not None:
            config.reformat_esuite_zaak_identificatie = (
                settings.ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE
            )
        if settings.ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN is not None:
            config.fetch_eherkenning_zaken_with_rsin = (
                settings.ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN
            )

        config.save()

    def test_configuration(self):
        """
        make requests to each API and verify that a connection can be made
        """
        zaken_client = build_client("zaak")
        catalogi_client = build_client("catalogi")
        documenten_client = build_client("document")
        forms_client = build_client("form")

        try:
            response = zaken_client.get("statussen")
            response.raise_for_status()
        except (ClientError, requests.RequestException) as exc:
            raise SelfTestFailed(
                "Could not retrieve list of statussen from Zaken API."
            ) from exc

        try:
            response = catalogi_client.get("zaaktypen")
            response.raise_for_status()
        except (ClientError, requests.RequestException) as exc:
            raise SelfTestFailed(
                "Could not retrieve list of zaaktypen from Catalogi API."
            ) from exc

        try:
            response = documenten_client.get("objectinformatieobjecten")
            response.raise_for_status()
        except (ClientError, requests.RequestException) as exc:
            raise SelfTestFailed(
                "Could not retrieve list of ObjectInformatieObjecten from Documenten API."
            ) from exc

        try:
            response = forms_client.get(
                "openstaande-inzendingen", params={"bsn": "000000000"}
            )
            response.raise_for_status()
        except (ClientError, requests.RequestException) as exc:
            raise SelfTestFailed(
                "Could not retrieve list of open submissions from Formulieren API."
            ) from exc
