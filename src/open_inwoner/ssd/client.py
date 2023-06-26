import decimal
from datetime import datetime
from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import Callable
from uuid import uuid4

from django.utils import timezone

import requests
from lxml import etree
from requests import Response

from open_inwoner.ssd.models import SSDConfig

BASE_DIR = Path(__file__).absolute().parent / "api"


class SSDBaseClient:
    """
    base class for SSD soap client
    """

    soap_action: str
    request_tpl_path: Path
    data_node_name: str

    def __init__(self):
        self.config = SSDConfig.get_solo()

    def get_headers(self):
        return {
            "Content-type": "text/xml",
        }

    def get_auth_kwargs(self):
        cert = self.config.service.get_cert()
        # auth = self.config.service.get_auth()
        verify = self.config.service.get_verify()
        return {
            "cert": cert,
            # "auth": auth,
            "verify": verify,
        }

    def get_request_base_data(self):
        data = {
            "MessageId": uuid4(),
            "SoapAction": self.soap_action,
            "Bedrijfsnaam": self.config.bedrijfs_naam,
            "Applicatienaam": self.config.applicatie_naam,
            "Gemeentecode": self.config.gemeentecode,
            "Aanmaakdatum": timezone.now(),
            "ApplicatieInformatie": "",
        }
        return data

    def get_request_body(self, data) -> bytes:
        data_tree = self.get_data_tree(self.data_node_name, data)
        request_tree = self.generate_request(data_tree)

        out = BytesIO()
        request_tree.write_output(out)
        data = out.getvalue()
        return data

    @cached_property
    def generate_request(self) -> Callable:
        parser = etree.XMLParser(resolve_entities=False)
        tree = etree.parse(self.request_tpl_path, parser=parser)
        transform = etree.XSLT(tree)
        return transform

    def get_data_tree(self, root_name, data_dict) -> etree.Element:
        """Convert a dictionary into XML"""
        root = etree.Element(root_name)

        for name, value in data_dict.items():
            elem = etree.SubElement(root, name)
            elem.text = self.get_xml_text(value)

        return root

    def get_xml_text(self, value) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float, decimal.Decimal)):
            return str(value)
        elif isinstance(value, datetime):
            return value.isoformat(timespec="seconds")
        else:
            return str(value)

    def execute_request(self, data) -> Response:
        headers = self.get_headers()
        body = self.get_request_body(data)
        auth_kwargs = self.get_auth_kwargs()

        res = requests.post(
            self.config.service.url,
            data=body,
            headers=headers,
            **auth_kwargs,
        )

        # soap can give usable error response as http 500
        if res.status_code not in (200, 500):
            res.raise_for_status()

        # TODO try/except parse errors
        parser = etree.XMLParser(resolve_entities=False)
        xml_tree = etree.parse(BytesIO(res.content), parser=parser)

        # TODO find nicer way to return response/error
        # for now just attach the xml to the response
        res.xml_tree = xml_tree
        return res


class JaaropgaveClient(SSDBaseClient):
    soap_action = "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient-v0300/Aanvraag"
    request_tpl_path = BASE_DIR / "jaaropgave/Request.xslt"
    # this is the root node for the selectors in the XSLT
    data_node_name = "Jaaropgave"

    def get_jaaropgave(self, bsn, year):
        # these keys match with the selectors in the XSLT
        data = self.get_request_base_data()
        data.update(
            {
                "BSN": bsn,
                "Dienstjaar": year,
            }
        )
        return self.execute_request(data)
