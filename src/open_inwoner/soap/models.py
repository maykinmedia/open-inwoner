from typing import Optional, Union

from django.db import models
from django.utils.translation import gettext_lazy as _

from simple_certmanager.models import Certificate


class SoapService(models.Model):
    label = models.CharField(
        _("label"),
        max_length=100,
        help_text=_("Human readable label to identify services"),
    )
    url = models.URLField(
        _("URL"),
        blank=True,
        help_text=_("Base URL of the service to connect to."),
    )

    client_certificate = models.ForeignKey(
        Certificate,
        blank=True,
        null=True,
        help_text=_(
            "The SSL certificate file used for client identification. If left empty, mutual TLS is disabled."
        ),
        on_delete=models.PROTECT,
        related_name="soap_services_client",
    )
    server_certificate = models.ForeignKey(
        Certificate,
        blank=True,
        null=True,
        help_text=_("The SSL/TLS certificate of the server"),
        on_delete=models.PROTECT,
        related_name="soap_services_server",
    )

    class Meta:
        verbose_name = _("SOAP service")
        verbose_name_plural = _("SOAP services")

    def __str__(self):
        return self.label

    def get_cert(self) -> Optional[Union[str, tuple[str, str]]]:
        certificate = self.client_certificate
        if not certificate:
            return None

        if certificate.public_certificate and certificate.private_key:
            return (certificate.public_certificate.path, certificate.private_key.path)

        if certificate.public_certificate:
            return certificate.public_certificate.path

    def get_verify(self) -> Union[bool, str]:
        certificate = self.server_certificate
        if certificate:
            return certificate.public_certificate.path
        return True
