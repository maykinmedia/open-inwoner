from django.conf import settings

import requests
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import SelfTestFailed
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from open_inwoner.openklant.clients import build_client
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.utils.api import ClientError


# TODO split into two steps? or split per service?
class KICAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required services to establish a connection with KIC APIs and set
    any feature flags or other options if specified

    1. Create service for Klanten API
    2. Create service for Contactmomenten API
    3. Set up configuration for KIC APIs
    """

    verbose_name = "Klantinteractie APIs configuration"
    required_settings = [
        "KLANTEN_API_ROOT",
        "KLANTEN_API_CLIENT_ID",
        "KLANTEN_API_SECRET",
        "CONTACTMOMENTEN_API_ROOT",
        "CONTACTMOMENTEN_API_CLIENT_ID",
        "CONTACTMOMENTEN_API_SECRET",
    ]
    enable_setting = "KIC_API_CONFIG_ENABLE"

    def is_configured(self) -> bool:
        kic_config = OpenKlantConfig.get_solo()
        return bool(kic_config.klanten_service) and bool(
            kic_config.contactmomenten_service
        )

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        # 1. Create Klanten API service
        klanten_service, created = Service.objects.update_or_create(
            api_root=settings.KLANTEN_API_ROOT,
            defaults={
                "label": "Klanten API",
                "api_type": APITypes.kc,
                "oas": settings.KLANTEN_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.KLANTEN_API_CLIENT_ID,
                "secret": settings.KLANTEN_API_SECRET,
                "user_id": settings.KLANTEN_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )
        if not created:
            klanten_service.oas = settings.KLANTEN_API_ROOT
            klanten_service.client_id = settings.KLANTEN_API_CLIENT_ID
            klanten_service.secret = settings.KLANTEN_API_SECRET
            klanten_service.user_id = settings.KLANTEN_API_CLIENT_ID
            klanten_service.user_representation = org_label
            klanten_service.save()

        # 2. Create Contactmomenten API service
        contactmomenten_service, created = Service.objects.update_or_create(
            api_root=settings.CONTACTMOMENTEN_API_ROOT,
            defaults={
                "label": "Contactmomenten API",
                "api_type": APITypes.cmc,
                "oas": settings.CONTACTMOMENTEN_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.CONTACTMOMENTEN_API_CLIENT_ID,
                "secret": settings.CONTACTMOMENTEN_API_SECRET,
                "user_id": settings.CONTACTMOMENTEN_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )
        if not created:
            contactmomenten_service.oas = settings.CONTACTMOMENTEN_API_ROOT
            contactmomenten_service.client_id = settings.CONTACTMOMENTEN_API_CLIENT_ID
            contactmomenten_service.secret = settings.CONTACTMOMENTEN_API_SECRET
            contactmomenten_service.user_id = settings.CONTACTMOMENTEN_API_CLIENT_ID
            contactmomenten_service.user_representation = org_label
            contactmomenten_service.save()

        # 3. Set up configuration
        config = OpenKlantConfig.get_solo()
        config.klanten_service = klanten_service
        config.contactmomenten_service = contactmomenten_service

        if settings.KIC_REGISTER_EMAIL:
            config.register_email = settings.KIC_REGISTER_EMAIL
        if settings.KIC_REGISTER_CONTACT_MOMENT is not None:
            config.register_contact_moment = settings.KIC_REGISTER_CONTACT_MOMENT
        if settings.KIC_REGISTER_BRONORGANISATIE_RSIN:
            config.register_bronorganisatie_rsin = (
                settings.KIC_REGISTER_BRONORGANISATIE_RSIN
            )
        if settings.KIC_REGISTER_CHANNEL:
            config.register_channel = settings.KIC_REGISTER_CHANNEL
        if settings.KIC_REGISTER_TYPE:
            config.register_type = settings.KIC_REGISTER_TYPE
        if settings.KIC_REGISTER_EMPLOYEE_ID:
            config.register_employee_id = settings.KIC_REGISTER_EMPLOYEE_ID
        if settings.KIC_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER is not None:
            config.use_rsin_for_innNnpId_query_parameter = (
                settings.KIC_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER
            )

        config.save()

    def test_configuration(self):
        """
        make requests to each API and verify that a connection can be made
        """
        klanten_client = build_client("klanten")
        contactmomenten_client = build_client("contactmomenten")

        try:
            response = klanten_client.get(
                "klanten", params={"subjectNatuurlijkPersoon__inpBsn": "000000000"}
            )
            response.raise_for_status()
        except (ClientError, requests.RequestException) as exc:
            raise SelfTestFailed(
                "Could not retrieve list of klanten from Klanten API."
            ) from exc

        try:
            response = contactmomenten_client.get(
                "contactmomenten", params={"identificatie": "00000"}
            )
            response.raise_for_status()
        except (ClientError, requests.RequestException) as exc:
            raise SelfTestFailed(
                "Could not retrieve list of objectcontactmomenten from Contactmomenten API."
            ) from exc
