from typing import Optional, Union

from django.db import models
from django.utils.translation import gettext_lazy as _

from simple_certmanager.models import Certificate
from solo.models import SingletonModel

from .validators import validate_api_root


class KvKConfig(SingletonModel):
    api_root = models.CharField(
        verbose_name=_("API root"),
        max_length=128,
        validators=[validate_api_root],
        help_text=_(
            "The root of the API without version number and endpoint "
            "(e.g. https://api.kvk.nl/api/ or https://api.kvk.nl/test/api)."
        ),
    )
    api_key = models.CharField(
        verbose_name=_("API key"),
        max_length=255,
        blank=True,
        help_text=_("The API key to connect to the KvK API."),
    )
    client_certificate = models.ForeignKey(
        Certificate,
        blank=True,
        null=True,
        help_text=_("The SSL certificate file used for client identification."),
        on_delete=models.PROTECT,
        related_name="kvk_service_client",
    )
    server_certificate = models.ForeignKey(
        Certificate,
        blank=True,
        null=True,
        help_text=_("The SSL/TLS certificate of the server."),
        on_delete=models.PROTECT,
        related_name="kvk_service_server",
    )

    class Meta:
        verbose_name = _("KvK configuration")

    @property
    def cert(self) -> Optional[Union[str, tuple[str, str]]]:
        certificate = self.client_certificate
        if not certificate:
            return None

        if certificate.public_certificate and certificate.private_key:
            return (certificate.public_certificate.path, certificate.private_key.path)
        elif certificate.public_certificate:
            return certificate.public_certificate.path

    @property
    def verify(self) -> Union[bool, str]:
        certificate = self.server_certificate
        if certificate:
            return certificate.public_certificate.path
        return True
