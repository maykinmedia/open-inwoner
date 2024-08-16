from django.conf import settings

import requests
from django_setup_configuration.config_settings import ConfigSettings
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import SelfTestFailed
from simple_certmanager.models import Certificate
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

from open_inwoner.openklant.clients import (
    build_contactmomenten_client,
    build_klanten_client,
)
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.utils.api import ClientError


class KlantenAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required Service to establish a connection with the Klanten API
    """

    verbose_name = "Klanten API configuration"
    config_settings = ConfigSettings(
        enable_setting="KIC_CONFIG_ENABLE",
        independent=False,
        namespace="KIC",
        file_name="kic_klanten_service",
        required_settings=[
            "KIC_KLANTEN_SERVICE_API_ROOT",
            "KIC_KLANTEN_SERVICE_CLIENT_ID",
            "KIC_KLANTEN_SERVICE_SECRET",
            "KIC_SERVER_CERTIFICATE_LABEL",
            "KIC_SERVER_CERTIFICATE_TYPE",
        ],
        additional_info={
            "klanten_service_api_root": {
                "variable": "KIC_KLANTEN_SERVICE_API_ROOT",
                "description": "The API root of the klanten service",
                "possible_values": "string (URL)",
            },
            "klanten_service_client_id": {
                "variable": "KIC_KLANTEN_SERVICE_API_CLIENT_ID",
                "description": "The API root of the klanten service",
                "possible_values": "string (URL)",
            },
            "klanten_service_secret": {
                "variable": "KIC_KLANTEN_SERVICE_SECRET",
                "description": "The secret of the klanten service",
                "possible_values": "string (URL)",
            },
        },
    )

    def is_enabled(self):
        return getattr(settings, self.config_settings.enable_setting, False)

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.KIC_KLANTEN_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        if not self.is_enabled():
            return

        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        server_certificate, _ = Certificate.objects.get_or_create(
            label=settings.KIC_SERVER_CERTIFICATE_LABEL,
            defaults={
                "type": settings.KIC_SERVER_CERTIFICATE_TYPE,
            },
        )

        with open(settings.KIC_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE) as public_cert:
            server_certificate.public_certificate.save("kic.crt", public_cert)

        Service.objects.update_or_create(
            api_root=settings.KIC_KLANTEN_SERVICE_API_ROOT,
            defaults={
                "label": "Klanten API",
                "slug": "klanten-api",
                "api_type": APITypes.kc,
                "oas": settings.KIC_KLANTEN_SERVICE_API_ROOT,
                "auth_type": AuthTypes.zgw,
                "client_id": settings.KIC_KLANTEN_SERVICE_API_CLIENT_ID,
                "secret": settings.KIC_KLANTEN_SERVICE_API_SECRET,
                "user_id": settings.KIC_KLANTEN_SERVICE_API_CLIENT_ID,
                "user_representation": org_label,
                "server_certificate": server_certificate,
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
    config_settings = ConfigSettings(
        enable_setting="KIC_CONFIG_ENABLE",
        independent=False,
        namespace="KIC",
        file_name="kic_contactmomenten_service",
        required_settings=[
            "KIC_CONTACTMOMENTEN_SERVICE_API_ROOT",
            "KIC_CONTACTMOMENTEN_SERVICE_CLIENT_ID",
            "KIC_CONTACTMOMENTEN_SERVICE_SECRET",
            "KIC_SERVER_CERTIFICATE_LABEL",
            "KIC_SERVER_CERTIFICATE_TYPE",
        ],
        additional_info={
            "contactmomenten_service_api_root": {
                "variable": "KIC_CONTACTMOMENTEN_SERVICE_API_ROOT",
                "description": "The API root of the klant contactmomenten service",
                "possible_values": "string (URL)",
            },
            "contactmomenten_service_client_id": {
                "variable": "KIC_CONTACTMOMENTEN_SERVICE_API_CLIENT_ID",
                "description": "The client ID of the klant contactmomenten service",
                "possible_values": "string (URL)",
            },
            "contactmomenten_service_secret": {
                "variable": "KIC_CONTACTMOMENTEN_SERVICE_SECRET",
                "description": "The secret of the klant contactmomenten service",
                "possible_values": "string (URL)",
            },
        },
    )

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.KIC_CONTACTMOMENTEN_SERVICE_API_ROOT
        ).exists()

    def configure(self):
        if not getattr(settings, self.config_settings.enable_setting, None):
            return

        organization = settings.OIP_ORGANIZATION or settings.ENVIRONMENT
        org_label = f"Open Inwoner {organization}".strip()

        server_certificate, _ = Certificate.objects.get_or_create(
            label=settings.KIC_SERVER_CERTIFICATE_LABEL,
            defaults={
                "type": settings.KIC_SERVER_CERTIFICATE_TYPE,
            },
        )

        with open(settings.KIC_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE) as public_cert:
            server_certificate.public_certificate.save("zgw.crt", public_cert)

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
                "server_certificate": server_certificate,
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
    config_settings = ConfigSettings(
        enable_setting="KIC_CONFIG_ENABLE",
        namespace="KIC",
        file_name="kic",
        models=[OpenKlantConfig],
        required_settings=[],
        independent=True,
        optional_settings=[
            "KIC_REGISTER_BRONORGANISATIE_RSIN",
            "KIC_REGISTER_CHANNEL",
            "KIC_REGISTER_CONTACT_MOMENT",
            "KIC_REGISTER_CONTACT_MOMENT",
            "KIC_REGISTER_EMAIL",
            "KIC_REGISTER_EMPLOYEE_ID",
            "KIC_REGISTER_TYPE",
            "KIC_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER",
        ],
        related_config_settings=[
            KlantenAPIConfigurationStep.config_settings,
            ContactmomentenAPIConfigurationStep.config_settings,
        ],
    )

    def is_configured(self) -> bool:
        kic_config = OpenKlantConfig.get_solo()
        return bool(kic_config.klanten_service) and bool(
            kic_config.contactmomenten_service
        )

    def configure(self):
        if not getattr(settings, self.config_settings.enable_setting, None):
            return

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
        klanten_client = build_klanten_client()
        contactmoment_client = build_contactmomenten_client()

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
