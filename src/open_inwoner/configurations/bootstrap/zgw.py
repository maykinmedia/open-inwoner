from django.conf import settings

import requests
from django_setup_configuration.config_settings import ConfigSettings
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import SelfTestFailed
from simple_certmanager.models import Certificate
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from open_inwoner.openzaak.clients import (
    build_catalogi_client,
    build_documenten_client,
    build_forms_client,
    build_zaken_client,
)
from open_inwoner.openzaak.models import OpenZaakConfig, ZGWApiGroupConfig
from open_inwoner.utils.api import ClientError


class ZakenAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required Service to establish a connection with the Zaken API
    """

    verbose_name = "Zaken API configuration"
    config_settings = ConfigSettings(
        enable_setting="ZGW_CONFIG_ENABLE",
        independent=False,
        namespace="ZGW",
        required_settings=[
            "ZGW_ZAAK_SERVICE_CLIENT_ID",
            "ZGW_ZAAK_SERVICE_SECRET",
            "ZGW_ZAAK_SERVICE_API_ROOT",
            "ZGW_SERVER_CERTIFICATE_LABEL",
            "ZGW_SERVER_CERTIFICATE_TYPE",
        ],
        optional_settings=[],
        additional_info={
            "zaak_service_api_root": {
                "variable": "ZGW_ZAAK_SERVICE_API_ROOT",
                "description": "The API root of the zaak service",
                "possible_values": "string (URL)",
            },
            "zaak_service_client_id": {
                "variable": "ZGW_ZAAK_SERVICE_CLIENT_ID",
                "description": "The API root of the zaak service",
                "possible_values": "string (URL)",
            },
            "zaak_service_secret": {
                "variable": "ZGW_ZAAK_SERVICE_SECRET",
                "description": "The secret of the zaak service",
                "possible_values": "string (URL)",
            },
        },
    )

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.ZGW_ZAAK_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        server_certificate, _ = Certificate.objects.get_or_create(
            label=settings.ZGW_SERVER_CERTIFICATE_LABEL,
            defaults={
                "type": settings.ZGW_SERVER_CERTIFICATE_TYPE,
            },
        )

        with open(settings.ZGW_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE) as public_cert:
            server_certificate.public_certificate.save("zgw.crt", public_cert)

        if getattr(settings, "ZGW_CONFIG_SERVER_CERTIFICATE_PRIVATE_KEY", None):
            with open(settings.ZGW_CONFIG_CERTIFICATE_PRIVATE_KEY) as private_key:
                server_certificate.private_key.save("zgw.key", private_key)

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
                "server_certificate": server_certificate,
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
    config_settings = ConfigSettings(
        enable_setting="ZGW_CONFIG_ENABLE",
        independent=False,
        namespace="ZGW",
        required_settings=[
            "ZGW_CATALOGI_SERVICE_CLIENT_ID",
            "ZGW_CATALOGI_SERVICE_SECRET",
            "ZGW_CATALOGI_SERVICE_API_ROOT",
            "ZGW_SERVER_CERTIFICATE_LABEL",
            "ZGW_SERVER_CERTIFICATE_TYPE",
        ],
        optional_settings=[],
        additional_info={
            "catalogi_service_api_root": {
                "variable": "ZGW_CATALOGI_SERVICE_API_ROOT",
                "description": "The API root of the catalogi service",
                "possible_values": "string (URL)",
            },
            "catalogi_service_client_id": {
                "variable": "ZGW_CATALOGI_SERVICE_CLIENT_ID",
                "description": "The API root of the catalogi service",
                "possible_values": "string (URL)",
            },
            "catalogi_service_secret": {
                "variable": "ZGW_CATALOGI_SERVICE_SECRET",
                "description": "The secret of the catalogi service",
                "possible_values": "string (URL)",
            },
        },
    )

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.ZGW_CATALOGI_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        server_certificate, _ = Certificate.objects.get_or_create(
            label=settings.ZGW_SERVER_CERTIFICATE_LABEL,
            defaults={
                "type": settings.ZGW_SERVER_CERTIFICATE_TYPE,
            },
        )

        with open(settings.ZGW_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE) as public_cert:
            server_certificate.public_certificate.save("zgw.crt", public_cert)

        if getattr(settings, "ZGW_CONFIG_SERVER_CERTIFICATE_PRIVATE_KEY", None):
            with open(settings.ZGW_CONFIG_CERTIFICATE_PRIVATE_KEY) as private_key:
                server_certificate.private_key.save("zgw.key", private_key)

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
                "server_certificate": server_certificate,
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
    config_settings = ConfigSettings(
        enable_setting="ZGW_CONFIG_ENABLE",
        independent=False,
        namespace="ZGW",
        required_settings=[
            "ZGW_DOCUMENT_SERVICE_CLIENT_ID",
            "ZGW_DOCUMENT_SERVICE_SECRET",
            "ZGW_DOCUMENT_SERVICE_API_ROOT",
            "ZGW_SERVER_CERTIFICATE_LABEL",
            "ZGW_SERVER_CERTIFICATE_TYPE",
        ],
        optional_settings=[],
        additional_info={
            "documenten_service_api_root": {
                "variable": "ZGW_DOCUMENT_SERVICE_API_ROOT",
                "description": "The API root of the documenten service",
                "possible_values": "string (URL)",
            },
            "documenten_service_client_id": {
                "variable": "ZGW_DOCUMENTEN_SERVICE_CLIENT_ID",
                "description": "The API root of the documenten service",
                "possible_values": "string (URL)",
            },
            "documenten_service_secret": {
                "variable": "ZGW_DOCUMENTEN_SERVICE_SECRET",
                "description": "The secret of the documenten service",
                "possible_values": "string (URL)",
            },
        },
    )

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.ZGW_DOCUMENTEN_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        server_certificate, _ = Certificate.objects.get_or_create(
            label=settings.ZGW_SERVER_CERTIFICATE_LABEL,
            defaults={
                "type": settings.ZGW_SERVER_CERTIFICATE_TYPE,
            },
        )

        with open(settings.ZGW_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE) as public_cert:
            server_certificate.public_certificate.save("zgw.crt", public_cert)

        if getattr(settings, "ZGW_CONFIG_SERVER_CERTIFICATE_PRIVATE_KEY", None):
            with open(settings.ZGW_CONFIG_CERTIFICATE_PRIVATE_KEY) as private_key:
                server_certificate.private_key.save("zgw.key", private_key)

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
                "server_certificate": server_certificate,
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
    config_settings = ConfigSettings(
        enable_setting="ZGW_CONFIG_ENABLE",
        independent=False,
        namespace="ZGW",
        required_settings=[
            "ZGW_FORM_SERVICE_CLIENT_ID",
            "ZGW_FORM_SERVICE_SECRET",
            "ZGW_FORM_SERVICE_API_ROOT",
            "ZGW_SERVER_CERTIFICATE_LABEL",
            "ZGW_SERVER_CERTIFICATE_TYPE",
        ],
        optional_settings=[],
        additional_info={
            "formulieren_service_api_root": {
                "variable": "ZGW_FROMULIEREN_SERVICE_API_ROOT",
                "description": "The API root of the formulieren service",
                "possible_values": "string (URL)",
            },
            "formulieren_service_client_id": {
                "variable": "ZGW_FORMULIEREN_SERVICE_CLIENT_ID",
                "description": "The API root of the formulieren service",
                "possible_values": "string (URL)",
            },
            "formulieren_service_secret": {
                "variable": "ZGW_FORMULIEREN_SERVICE_SECRET",
                "description": "The secret of the formulieren service",
                "possible_values": "string (URL)",
            },
        },
    )

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.ZGW_FORM_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        server_certificate, _ = Certificate.objects.get_or_create(
            label=settings.ZGW_SERVER_CERTIFICATE_LABEL,
            defaults={
                "type": settings.ZGW_SERVER_CERTIFICATE_TYPE,
            },
        )

        with open(settings.ZGW_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE) as public_cert:
            server_certificate.public_certificate.save("zgw.crt", public_cert)

        if getattr(settings, "ZGW_CONFIG_SERVER_CERTIFICATE_PRIVATE_KEY", None):
            with open(settings.ZGW_CONFIG_CERTIFICATE_PRIVATE_KEY) as private_key:
                server_certificate.private_key.save("zgw.key", private_key)

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
                "server_certificate": server_certificate,
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
    config_settings = ConfigSettings(
        enable_setting="ZGW_CONFIG_ENABLE",
        namespace="ZGW",
        models=[OpenZaakConfig],
        related_config_settings=[
            ZakenAPIConfigurationStep.config_settings,
            CatalogiAPIConfigurationStep.config_settings,
            DocumentenAPIConfigurationStep.config_settings,
            FormulierenAPIConfigurationStep.config_settings,
        ],
        required_settings=[],
        optional_settings=[
            "ZGW_ACTION_REQUIRED_DEADLINE_DAYS",
            "ZGW_ALLOWED_FILE_EXTENSIONS",
            "ZGW_DOCUMENT_MAX_CONFIDENTIALITY",
            "ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN",
            "ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN",
            "ZGW_MAX_UPLOAD_SIZE",
            "ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE",
            "ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN",
            "ZGW_TITLE_TEXT",
            "ZGW_ZAAK_MAX_CONFIDENTIALITY",
        ],
    )

    def is_configured(self) -> bool:
        """Verify that at least 1 ZGW API set is configured."""
        zgw_config = OpenZaakConfig.get_solo()
        return ZGWApiGroupConfig.objects.filter(open_zaak_config=zgw_config).exists()

    def configure(self):
        config = OpenZaakConfig.get_solo()
        ZGWApiGroupConfig.objects.create(
            open_zaak_config=config,
            zrc_service=Service.objects.get(
                api_root=settings.ZGW_ZAAK_SERVICE_API_ROOT
            ),
            ztc_service=Service.objects.get(
                api_root=settings.ZGW_CATALOGI_SERVICE_API_ROOT
            ),
            drc_service=Service.objects.get(
                api_root=settings.ZGW_DOCUMENTEN_SERVICE_API_ROOT
            ),
            form_service=Service.objects.get(
                api_root=settings.ZGW_FORM_SERVICE_API_ROOT
            ),
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
        zaken_client = build_zaken_client()
        catalogi_client = build_catalogi_client()
        documenten_client = build_documenten_client()
        forms_client = build_forms_client()

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
