from pathlib import Path
from uuid import uuid4

from django.template import loader
from django.utils import timezone

import requests
from requests import Response

from open_inwoner.ssd.models import SSDConfig

BASE_DIR = Path(__file__).absolute().parent.parent


class SSDBaseClient:
    """Base class for SSD soap client"""

    request_template: Path
    soap_action: str

    def __init__(self):
        self.config = SSDConfig.get_solo()

    def _get_headers(self) -> dict[str, str]:
        return {
            "Content-type": "text/xml",
        }

    def _get_auth_kwargs(self) -> dict:
        cert = self.config.service.get_cert()
        verify = self.config.service.get_verify()
        return {
            "cert": cert,
            "verify": verify,
        }

    def _format_time(self):
        local_time = timezone.localtime(timezone.now())
        formatted_time = local_time.strftime("%Y-%m-%dT%H:%M:%S%z")
        return formatted_time

    def _get_base_context(self) -> dict:
        data = {
            "message_id": uuid4().urn,
            "soap_action": self.soap_action,
            "applicatie_naam": self.config.applicatie_naam,
            "bedrijfs_naam": self.config.bedrijfs_naam,
            "gemeentecode": self.config.gemeentecode,
            "dat_tijd_request": self._format_time(),
        }
        return data

    def _request(self, body: str) -> Response:
        auth_kwargs = self._get_auth_kwargs()
        headers = self._get_headers()

        response = requests.post(
            url=self.config.service.url,
            body=body.encode("utf-8"),
            headers=headers,
            **auth_kwargs,
        )
        return response

    def templated_request(self, **kwargs) -> str:
        context = {**self._get_base_context(), **kwargs}

        body = loader.render_to_string(self.request_template, context)

        return self._request(body)


class JaaropgaveClient(SSDBaseClient):
    """
    SSD client for retrieving yearly reports

    Values for `bsn` and `dienst_jaar` in the main function are
    retrieved and supplied from the call site (the view)
    """

    request_template = BASE_DIR / "soap/templates/ssd/jaaropgave.xml"
    soap_action = (
        "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient-v0400/JaarOpgaveInfo"
    )

    # TODO: remove hard-coded values for params
    def get_jaaropgave(self, bsn: str, year: str) -> str:
        extra_context = {
            "bsn": bsn,
            "dienst_jaar": year,
        }
        response = self.templated_request(**extra_context)
        return response.text


class UitkeringClient(SSDBaseClient):
    """
    SSD client for retrieving monthly reports

    Values for `bsn` and `period` (= year + month) in the main function are
    retrieved and supplied from the call site (the view)
    """

    request_template = BASE_DIR / "soap/templates/ssd/maandspecificaties.xml"
    soap_action = "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient-v0600/UitkeringsSpecificatieInfo"

    # TODO: remove hard-coded values for params
    def get_maandspecificatie(self, bsn: str, period: str) -> str:
        extra_context = {
            "bsn": bsn,
            "period": period,
        }
        response = self.templated_request(**extra_context)
        return response.text
