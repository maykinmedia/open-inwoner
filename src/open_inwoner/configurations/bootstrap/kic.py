from django.conf import settings

import requests
from django_setup_configuration import ConfigSettingsModel
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import SelfTestFailed
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from open_inwoner.openklant.clients import build_client
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.utils.api import ClientError


class KlantenAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required Service to establish a connection with the Klanten API
    """

    verbose_name = "Klanten API configuration"
    required_settings = [
        "KIC_KLANTEN_SERVICE_API_ROOT",
        "KIC_KLANTEN_SERVICE_API_CLIENT_ID",
        "KIC_KLANTEN_SERVICE_API_SECRET",
    ]

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.KIC_KLANTEN_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        Service.objects.update_or_create(
            api_root=settings.KIC_KLANTEN_SERVICE_API_ROOT,
            defaults={
                "label": "Klanten API",
                "api_type": APITypes.kc,
                "oas": settings.KIC_KLANTEN_SERVICE_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.KIC_KLANTEN_SERVICE_API_CLIENT_ID,
                "secret": settings.KIC_KLANTEN_SERVICE_API_SECRET,
                "user_id": settings.KIC_KLANTEN_SERVICE_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )

    def test_configuration(self):
        """
        actual testing is done in final step
        """


class ContactmomentenAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required Service to establish a connection with the Contactmomenten API
    """

    verbose_name = "Contactmomenten API configuration"
    required_settings = [
        "KIC_CONTACTMOMENTEN_SERVICE_API_ROOT",
        "KIC_CONTACTMOMENTEN_SERVICE_API_CLIENT_ID",
        "KIC_CONTACTMOMENTEN_SERVICE_API_SECRET",
    ]

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.KIC_CONTACTMOMENTEN_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        Service.objects.update_or_create(
            api_root=settings.KIC_CONTACTMOMENTEN_SERVICE_API_ROOT,
            defaults={
                "label": "Contactmomenten API",
                "api_type": APITypes.cmc,
                "oas": settings.KIC_CONTACTMOMENTEN_SERVICE_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.KIC_CONTACTMOMENTEN_SERVICE_API_CLIENT_ID,
                "secret": settings.KIC_CONTACTMOMENTEN_SERVICE_API_SECRET,
                "user_id": settings.KIC_CONTACTMOMENTEN_SERVICE_API_CLIENT_ID,
                "user_representation": org_label,
            },
        )

    def test_configuration(self):
        """
        actual testing is done in final step
        """


class KICAPIsConfigurationStep(BaseConfigurationStep):
    """
    Configure the KIC settings and set any feature flags or other options if specified
    """

    verbose_name = "Klantinteractie APIs configuration"
    enable_setting = "KIC_CONFIG_ENABLE"
    required_settings = [
        "KIC_CONTACTMOMENTEN_SERVICE_CLIENT_ID",
        "KIC_CONTACTMOMENTEN_SERVICE_SECRET",
        "KIC_CONTACTMOMENTEN_SERVICE_API_ROOT",
        "KIC_KLANTEN_SERVICE_CLIENT_ID",
        "KIC_KLANTEN_SERVICE_SECRET",
        "KIC_KLANTEN_SERVICE_API_ROOT",
        "KIC_REGISTER_TYPE",
        "KIC_REGISTER_CONTACT_MOMENT",
    ]
    config_settings = ConfigSettingsModel(
        models=[OpenKlantConfig],
        namespace="KIC",
        file_name="kic",
        excluded_fields=(
            "id",
            "api_type",
            "auth_type",
            "client_certificate",
            "confirmation",
            "header_key",
            "header_value",
            "label",
            "nlx",
            "oas",
            "oas_file",
            "send_email_confirmation",
            "server_certificate",
            "user_id",
            "user_representation",
            "uuid",
        ),
    )

    def is_configured(self) -> bool:
        kic_config = OpenKlantConfig.get_solo()
        return bool(kic_config.klanten_service) and bool(
            kic_config.contactmomenten_service
        )

    def configure(self):
        config = OpenKlantConfig.get_solo()
        config.klanten_service = Service.objects.get(
            api_root=settings.KIC_KLANTEN_SERVICE_API_ROOT
        )
        config.contactmomenten_service = Service.objects.get(
            api_root=settings.KIC_CONTACTMOMENTEN_SERVICE_API_ROOT
        )

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
        make requests to the APIs and verify that a connection can be made
        """
        klanten_client = build_client("klanten")
        contactmoment_client = build_client("contactmomenten")

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
            response = contactmoment_client.get(
                "contactmomenten", params={"identificatie": "00000"}
            )
            response.raise_for_status()
        except (ClientError, requests.RequestException) as exc:
            raise SelfTestFailed(
                "Could not retrieve list of objectcontactmomenten from Contactmomenten API."
            ) from exc
