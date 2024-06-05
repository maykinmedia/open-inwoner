from django.conf import settings

import requests
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

from .base import ConfigSettingsBase


class KICConfigurationSettings(ConfigSettingsBase):
    model = OpenKlantConfig
    display_name = "Klanten Configuration"
    namespace = "KIC"
    required_fields = (
        "contactmomenten_service_client_id",
        "contactmomenten_service_secret",
        "contactmomenten_service_api_root",
        "klanten_service_client_id",
        "klanten_service_secret",
        "klanten_service_api_root",
        "register_type",
        "register_contact_moment",
    )
    all_fields = required_fields + (
        "register_bronorganisatie_rsin",
        "register_channel",
        "register_contact_moment",
        "register_email",
        "register_employee_id",
        "use_rsin_for_innNnpId_query_parameter",
    )
    excluded_fields = (
        "contactmomenten_service_uuid",
        "klanten_service_uuid",
    )


class KlantenAPIConfigurationStep(BaseConfigurationStep):
    """
    Configure the required Service to establish a connection with the Klanten API
    """

    verbose_name = "Klanten API configuration"
    required_settings = [
        "KIC_KLANTEN_SERVICE_API_ROOT",
        "KIC_KLANTEN_SERVICE_API_CLIENT_ID",
        "KIC_KLANTEN_SERVICE_API_SECRET",
        "KIC_SERVER_CERTIFICATE_LABEL",
        "KIC_SERVER_CERTIFICATE_TYPE",
    ]
    enable_setting = "KIC_ENABLE"

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.KIC_KLANTEN_SERVICE_API_ROOT
        ).exists()

    def configure(self):
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
    required_settings = [
        "KIC_CONTACTMOMENTEN_SERVICE_API_ROOT",
        "KIC_CONTACTMOMENTEN_SERVICE_API_CLIENT_ID",
        "KIC_CONTACTMOMENTEN_SERVICE_API_SECRET",
        "KIC_SERVER_CERTIFICATE_LABEL",
        "KIC_SERVER_CERTIFICATE_TYPE",
    ]
    enable_setting = "KIC_ENABLE"

    def is_configured(self) -> bool:
        return Service.objects.filter(
            api_root=settings.KIC_CONTACTMOMENTEN_SERVICE_API_ROOT
        ).exists()

    def configure(self):
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
    enable_setting = "KIC_ENABLE"

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
