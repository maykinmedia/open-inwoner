from django.conf import settings

import requests
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import SelfTestFailed
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from open_inwoner.openzaak.clients import build_client
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.utils.api import ClientError


# TODO split into two steps? or split per service?
class ZGWAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required services to establish a connection with ZGW APIs and set
    any feature flags or other options if specified

    1. Create service for Zaken API
    2. Create service for Catalogi API
    3. Create service for Documenten API
    4. Create service for Formulieren API (eSuite)
    5. Set up configuration for ZGW APIs
    """

    verbose_name = "ZGW APIs configuration"
    required_settings = [
        "ZAKEN_API_ROOT",
        "ZAKEN_API_CLIENT_ID",
        "ZAKEN_API_SECRET",
        "CATALOGI_API_ROOT",
        "CATALOGI_API_CLIENT_ID",
        "CATALOGI_API_SECRET",
        "DOCUMENTEN_API_ROOT",
        "DOCUMENTEN_API_CLIENT_ID",
        "DOCUMENTEN_API_SECRET",
        "FORMULIEREN_API_ROOT",
        "FORMULIEREN_API_CLIENT_ID",
        "FORMULIEREN_API_SECRET",
    ]
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
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        # 1. Create Zaken API service
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

        # 2. Create Catalogi API service
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

        # 3. Create Documenten API service
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

        # 4. Create Formulieren API service
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

        # 5. Set up configuration
        config = OpenZaakConfig.get_solo()
        config.zaak_service = zaak_service
        config.catalogi_service = catalogi_service
        config.document_service = document_service
        config.form_service = form_service

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
