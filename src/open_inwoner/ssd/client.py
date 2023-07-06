from pathlib import Path
from uuid import uuid4

from django.template import loader
from django.utils import timezone

import requests
from requests import Response

from ..utils.export import render_pdf
from .models import SSDConfig
from .xml import get_jaaropgave_dict, get_uitkering_dict

BASE_DIR = Path(__file__).absolute().parent.parent


class SSDBaseClient:
    """Base class for SSD SOAP client"""

    html_template: Path
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
        """Wrap around `requests.post` with headers and auth details"""

        auth_kwargs = self._get_auth_kwargs()
        headers = self._get_headers()

        response = requests.post(
            url=self.config.service.url,
            data=body.encode("utf-8"),
            headers=headers,
            **auth_kwargs,
        )
        return response

    def templated_request(self, **kwargs) -> Response:
        """Perform SOAP request with XML request template"""

        context = {**self._get_base_context(), **kwargs}

        body = loader.render_to_string(self.request_template, context)

        return self._request(body)


class JaaropgaveClient(SSDBaseClient):
    """
    SSD client for retrieving yearly reports

    Values for `bsn` and `dienst_jaar` in the main function are
    retrieved and supplied from the call site (the view)
    """

    html_template = BASE_DIR / "ssd/templates/jaaropgave.html"
    request_template = BASE_DIR / "soap/templates/ssd/jaaropgave.xml"
    soap_action = (
        "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient-v0400/JaarOpgaveInfo"
    )

    def _get_jaaropgave(self, bsn: str, year: str) -> str:
        """
        :returns: XML containing the yearly benefits report
        """
        extra_context = {
            "bsn": bsn,
            "dienst_jaar": year,
        }
        response = self.templated_request(**extra_context)
        return response.text

    def get_yearly_report(self, bsn: str, dienst_jaar: str) -> bytes:
        """
        :returns: the yearly benefits report PDF as bytes
        """
        jaaropgave = self._get_jaaropgave(bsn, dienst_jaar)
        data = get_jaaropgave_dict(jaaropgave)
        pdf_content = render_pdf(self.html_template, context={**data})
        return pdf_content


class UitkeringClient(SSDBaseClient):
    """
    SSD client for retrieving monthly reports

    Values for `bsn` and `period` (= year + month) in the main function are
    retrieved and supplied from the call site (the view)
    """

    html_template = BASE_DIR / "ssd/templates/maandspecificatie.html"
    request_template = BASE_DIR / "soap/templates/ssd/maandspecificaties.xml"
    soap_action = "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient-v0600/UitkeringsSpecificatieInfo"

    def _get_maandspecificatie(self, bsn: str, period: str) -> str:
        """
        :returns: XML containing the monthly benefits report
        """
        extra_context = {
            "bsn": bsn,
            "period": period,
        }
        response = self.templated_request(**extra_context)
        return response.text

    def get_monthly_report(self, bsn: str = None, period: str = None) -> bytes:
        """
        :returns: the monthly benefits report PDF as bytes
        """
        # maandspecificatie = self._get_maandspecificatie(bsn, period)

        # TODO: remove when done testing
        xml_response = "src/open_inwoner/ssd/tests/files/uitkering_response.xml"
        with open(xml_response, "r") as file:
            maandspecificatie = file.read()

        data = get_uitkering_dict(maandspecificatie)
        pdf_content = render_pdf(self.html_template, context={**data})
        # return pdf_content

        # TODO: remove when done testing
        pdf_path = "src/open_inwoner/ssd/tests/files/test.pdf"
        with open(pdf_path, "bw") as file:
            file.write(pdf_content)
