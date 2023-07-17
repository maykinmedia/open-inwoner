from pathlib import Path
from uuid import uuid4

from django.template import loader
from django.utils import timezone

import dateutil
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

    def _format_time(self):
        local_time = timezone.localtime(timezone.now())
        formatted_time = local_time.strftime("%Y-%m-%dT%H:%M:%S%z")
        return formatted_time

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

    def _make_request_body(self, **kwargs) -> str:
        context = {**self._get_base_context(), **kwargs}
        return loader.render_to_string(self.request_template, context)

    def templated_request(self, **kwargs) -> Response:
        """Wrap around `requests.post` with headers, auth details, request body"""

        auth_kwargs = self._get_auth_kwargs()
        headers = self._get_headers()
        body = self._make_request_body(**kwargs)

        response = requests.post(
            url=self.config.service.url,
            data=body.encode("utf-8"),
            headers=headers,
            **auth_kwargs,
        )
        return response

    def file_name_to_period(self, file_name):
        dt = dateutil.parser.parse(file_name)
        return dt.strftime("%Y%m")


class JaaropgaveClient(SSDBaseClient):
    """
    SSD client for retrieving yearly reports
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
            "dienstjaar": year,
        }
        response = self.templated_request(**extra_context)
        return response.text

    def get_yearly_report(self, bsn: str = None, dienstjaar: str = None) -> bytes:
        """
        :returns: the yearly benefits report PDF as bytes
        """
        # jaaropgave = self._get_jaaropgave(bsn, dienstjaar)

        # TODO: remove when done testing
        xml_response = "src/open_inwoner/ssd/tests/files/jaaropgave_response.xml"
        with open(xml_response, "r") as file:
            jaaropgave = file.read()

        data = get_jaaropgave_dict(jaaropgave)
        pdf_content = render_pdf(self.html_template, context={**data})

        with open("src/open_inwoner/ssd/tests/files/test.pdf", "bw") as file:
            file.write(pdf_content)

        return pdf_content


class UitkeringClient(SSDBaseClient):
    """
    SSD client for retrieving monthly reports
    """

    html_template = BASE_DIR / "ssd/templates/maandspecificatie.html"
    request_template = BASE_DIR / "soap/templates/ssd/maandspecificatie.xml"
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

        # TODO: remove when done testing
        with open("src/open_inwoner/ssd/tests/files/test.pdf", "wb") as file:
            file.write(pdf_content)

        return pdf_content
