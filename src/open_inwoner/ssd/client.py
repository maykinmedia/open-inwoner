import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from django.template import loader
from django.template.defaultfilters import date as django_date
from django.utils import timezone

import requests
from requests import Response

from ..utils.export import render_pdf
from .models import SSDConfig
from .xml import get_jaaropgaven, get_uitkeringen

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).absolute().parent.parent


class SSDBaseClient(ABC):
    """Base class for SSD SOAP client"""

    html_template: Path
    request_template: Path
    soap_action: str
    endpoint: property  # str

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

        try:
            response = requests.post(
                url=self.config.service.url + self.endpoint,
                data=body.encode("utf-8"),
                headers=headers,
                **auth_kwargs,
            )
        except requests.exceptions.RequestException:
            logger.exception("Requests exception")
            raise

        return response

    @abstractmethod
    def format_report_date(self, report_date: str) -> str:
        """
        :returns: formatted date string for SOAP request
        """

    @abstractmethod
    def format_file_name(self, report_date: str) -> str:
        """
        :returns: formatted string for PDF name
        """

    @abstractmethod
    def get_reports(self, bsn: str, report_date: str, base_url: str) -> Optional[bytes]:
        """
        :param bsn: the BSN number of the client making the request
        :param report_date: the date of the requested report
        :param base_url: the absolute URI of the request, allows the use of
        relative URLs in templates used to generate PDFs
        :returns: a yearly/monthly benefits report PDF (bytes) if the request to
        the client's SOAP service is successful, `None` otherwise
        """

    @property
    def endpoint(self) -> str:
        return ""


class JaaropgaveClient(SSDBaseClient):
    """
    SSD client for retrieving yearly reports
    """

    html_template = BASE_DIR / "ssd/templates/jaaropgave.html"
    request_template = BASE_DIR / "soap/templates/ssd/jaaropgave.xml"
    soap_action = (
        "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient-v0400/JaarOpgaveInfo"
    )

    def format_report_date(self, report_date: str) -> str:
        """
        1995-12-24 -> 1985
        """
        return datetime.strptime(report_date, "%Y-%m-%d").strftime("%Y")

    def format_file_name(self, report_date: str) -> str:
        """
        1985 -> Jaaropgave 1985
        """
        return f"Jaaropgave {report_date}"

    def get_reports(
        self, bsn: str, report_date: str, request_base_url: str
    ) -> Optional[bytes]:

        response = self.templated_request(bsn=bsn, dienstjaar=report_date)

        if response.status_code != 200:
            return None

        jaaropgaven = get_jaaropgaven(response)

        if not jaaropgaven:
            return None

        for report_data in jaaropgaven:
            report_data.update(
                {
                    "logo": self.config.logo,
                    "jaaropgave_comments": self.config.jaaropgave_comments,
                }
            )
        pdf = render_pdf(
            self.html_template,
            context={"reports": jaaropgaven},
            base_url=request_base_url,
        )
        return pdf

    @property
    def endpoint(self) -> str:
        return self.config.jaaropgave_endpoint


class UitkeringClient(SSDBaseClient):
    """
    SSD client for retrieving monthly reports
    """

    html_template = BASE_DIR / "ssd/templates/maandspecificatie.html"
    request_template = BASE_DIR / "soap/templates/ssd/maandspecificatie.xml"
    soap_action = "http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient-v0600/UitkeringsSpecificatieInfo"

    def format_report_date(self, report_date: str) -> str:
        """
        1985-12-24 -> 198512
        """
        return datetime.strptime(report_date, "%Y-%m-%d").strftime("%Y%m")

    def format_file_name(self, report_date: str) -> str:
        """
        198506 -> Maandspecificatie juni 1985
        """
        dt = datetime.strptime(report_date, "%Y%m")
        dt_formatted = django_date(dt, "F Y").lower()
        return f"Maandspecificatie {dt_formatted}"

    def get_reports(
        self, bsn: str, report_date: str, request_base_url: str
    ) -> Optional[bytes]:

        response = self.templated_request(bsn=bsn, period=report_date)

        if response.status_code != 200:
            return None

        uitkeringen = get_uitkeringen(response)

        if not uitkeringen:
            return None

        for report_data in uitkeringen:
            report_data.update(
                {
                    "logo": self.config.logo,
                }
            )
        pdf = render_pdf(
            self.html_template,
            context={"reports": uitkeringen},
            base_url=request_base_url,
        )
        return pdf

    @property
    def endpoint(self) -> str:
        return self.config.maandspecificatie_endpoint
