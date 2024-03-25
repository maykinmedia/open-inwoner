from django.conf import settings

import requests
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
        "ZAKEN_API_ROOT",
        "ZAKEN_API_CLIENT_ID",
        "ZAKEN_API_SECRET",
    ]
    enable_setting = "ZGW_API_CONFIG_ENABLE"

    def is_configured(self) -> bool:
        return bool(Service.objects.filter(api_root=settings.ZAKEN_API_ROOT))

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        zaak_service, created = Service.objects.update_or_create(
            api_root=settings.ZAKEN_API_ROOT,
            defaults={
                "label": "Zaken API",
                "api_type": APITypes.zrc,
                "oas": settings.ZAKEN_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.ZAKEN_API_CLIENT_ID,
                "secret": settings.ZAKEN_API_SECRET,
                "user_id": settings.ZAKEN_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )
        if not created:
            zaak_service.oas = settings.ZAKEN_API_ROOT
            zaak_service.client_id = settings.ZAKEN_API_CLIENT_ID
            zaak_service.secret = settings.ZAKEN_API_SECRET
            zaak_service.user_id = settings.ZAKEN_API_CLIENT_ID
            zaak_service.user_representation = org_label
            zaak_service.save()

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
        "CATALOGI_API_ROOT",
        "CATALOGI_API_CLIENT_ID",
        "CATALOGI_API_SECRET",
    ]
    enable_setting = "ZGW_API_CONFIG_ENABLE"

    def is_configured(self) -> bool:
        return bool(Service.objects.filter(api_root=settings.CATALOGI_API_ROOT))

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        catalogi_service, created = Service.objects.update_or_create(
            api_root=settings.CATALOGI_API_ROOT,
            defaults={
                "label": "Catalogi API",
                "api_type": APITypes.ztc,
                "oas": settings.CATALOGI_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.CATALOGI_API_CLIENT_ID,
                "secret": settings.CATALOGI_API_SECRET,
                "user_id": settings.CATALOGI_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )
        if not created:
            catalogi_service.oas = settings.CATALOGI_API_ROOT
            catalogi_service.client_id = settings.CATALOGI_API_CLIENT_ID
            catalogi_service.secret = settings.CATALOGI_API_SECRET
            catalogi_service.user_id = settings.CATALOGI_API_CLIENT_ID
            catalogi_service.user_representation = org_label
            catalogi_service.save()

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
        "DOCUMENTEN_API_ROOT",
        "DOCUMENTEN_API_CLIENT_ID",
        "DOCUMENTEN_API_SECRET",
    ]
    enable_setting = "ZGW_API_CONFIG_ENABLE"

    def is_configured(self) -> bool:
        return bool(Service.objects.filter(api_root=settings.DOCUMENTEN_API_ROOT))

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        document_service, created = Service.objects.update_or_create(
            api_root=settings.DOCUMENTEN_API_ROOT,
            defaults={
                "label": "Documenten API",
                "api_type": APITypes.drc,
                "oas": settings.DOCUMENTEN_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.DOCUMENTEN_API_CLIENT_ID,
                "secret": settings.DOCUMENTEN_API_SECRET,
                "user_id": settings.DOCUMENTEN_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )
        if not created:
            document_service.oas = settings.DOCUMENTEN_API_ROOT
            document_service.client_id = settings.DOCUMENTEN_API_CLIENT_ID
            document_service.secret = settings.DOCUMENTEN_API_SECRET
            document_service.user_id = settings.DOCUMENTEN_API_CLIENT_ID
            document_service.user_representation = org_label
            document_service.save()

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
        "FORMULIEREN_API_ROOT",
        "FORMULIEREN_API_CLIENT_ID",
        "FORMULIEREN_API_SECRET",
    ]
    enable_setting = "ZGW_API_CONFIG_ENABLE"

    def is_configured(self) -> bool:
        return bool(Service.objects.filter(api_root=settings.FORMULIEREN_API_ROOT))

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        form_service, created = Service.objects.update_or_create(
            api_root=settings.FORMULIEREN_API_ROOT,
            defaults={
                "label": "Formulieren API",
                "api_type": APITypes.orc,
                "oas": settings.FORMULIEREN_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.FORMULIEREN_API_CLIENT_ID,
                "secret": settings.FORMULIEREN_API_SECRET,
                "user_id": settings.FORMULIEREN_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )
        if not created:
            form_service.oas = settings.FORMULIEREN_API_ROOT
            form_service.client_id = settings.FORMULIEREN_API_CLIENT_ID
            form_service.secret = settings.FORMULIEREN_API_SECRET
            form_service.user_id = settings.FORMULIEREN_API_CLIENT_ID
            form_service.user_representation = org_label
            form_service.save()

    def test_configuration(self):
        """
        actual testing is done in final step
        """


class ZGWAPIsConfigurationStep(BaseConfigurationStep):
    """
    Configure the ZGW settings and set any feature flags or other options if specified
    """

    verbose_name = "ZGW APIs configuration"
    enable_setting = "ZGW_API_CONFIG_ENABLE"

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
        config.zaak_service = Service.objects.get(api_root=settings.ZAKEN_API_ROOT)
        config.catalogi_service = Service.objects.get(
            api_root=settings.CATALOGI_API_ROOT
        )
        config.document_service = Service.objects.get(
            api_root=settings.DOCUMENTEN_API_ROOT
        )
        config.form_service = Service.objects.get(
            api_root=settings.FORMULIEREN_API_ROOT
        )

        # General config options
        if settings.ZAAK_MAX_CONFIDENTIALITY:
            config.zaak_max_confidentiality = settings.ZAAK_MAX_CONFIDENTIALITY
        if settings.DOCUMENT_MAX_CONFIDENTIALITY:
            config.document_max_confidentiality = settings.DOCUMENT_MAX_CONFIDENTIALITY
        if settings.ACTION_REQUIRED_DEADLINE_DAYS:
            config.action_required_deadline_days = (
                settings.ACTION_REQUIRED_DEADLINE_DAYS
            )
        if settings.ALLOWED_FILE_EXTENSIONS:
            config.allowed_file_extensions = settings.ALLOWED_FILE_EXTENSIONS
        if settings.MIJN_AANVRAGEN_TITLE_TEXT:
            config.title_text = settings.MIJN_AANVRAGEN_TITLE_TEXT

        # Feature flags
        if settings.ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN is not None:
            config.enable_categories_filtering_with_zaken = (
                settings.ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN
            )

        # eSuite specific options
        if settings.SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN is not None:
            config.skip_notification_statustype_informeren = (
                settings.SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN
            )
        if settings.REFORMAT_ESUITE_ZAAK_IDENTIFICATIE is not None:
            config.reformat_esuite_zaak_identificatie = (
                settings.REFORMAT_ESUITE_ZAAK_IDENTIFICATIE
            )
        if settings.FETCH_EHERKENNING_ZAKEN_WITH_RSIN is not None:
            config.fetch_eherkenning_zaken_with_rsin = (
                settings.FETCH_EHERKENNING_ZAKEN_WITH_RSIN
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
