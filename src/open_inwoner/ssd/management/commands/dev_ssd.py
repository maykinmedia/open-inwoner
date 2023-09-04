from pathlib import Path

from django.core.management import BaseCommand

from lxml import etree
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from open_inwoner.ssd.service.jaaropgave import (
    JaarOpgaveClientPortTypeSendJaarOpgaveClientOutput,
    JaarOpgaveInfoResponse,
)
from open_inwoner.ssd.service.uitkering import UitkeringsSpecificatieInfoResponse


class Command(BaseCommand):
    help = "Hack dev code"

    def handle(self, *args, **options):
        print("yo")

        _path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "files"
            / "jaaropgave_response.xml"
        )
        with open(_path, "rb") as f:
            tree = etree.parse(f)
            node = tree.find(
                "//{http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400}JaarOpgaveInfoResponse"
            )
            parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
            res = parser.parse(node, JaarOpgaveInfoResponse)

        print(res)

        _path = (
            Path(__file__).parent.parent.parent
            / "tests"
            / "files"
            / "uitkering_response_basic.xml"
        )
        with open(_path, "rb") as f:
            tree = etree.parse(f)
            node = tree.find(
                "//{http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600}UitkeringsSpecificatieInfoResponse"
            )
            parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
            res = parser.parse(node, UitkeringsSpecificatieInfoResponse)

        print(res)
