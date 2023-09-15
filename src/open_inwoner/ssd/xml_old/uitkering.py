from pathlib import Path

from lxml import etree
from requests import Response
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler

from ..service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)

UITKERING_INFO_RESPONSE_NODE = (
    "//{http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600}UitkeringsSpecificatieInfoResponse"
)


# TODO: remove
path1 = Path(__file__).parent.parent / "tests" / "files" / "uitkering_response_basic.xml"
path2 = Path(__file__).parent.parent / "tests" / "files" / "uitkering_response_extra_report.xml"
path3 = Path(__file__).parent.parent / "tests" / "files" / "uitkering_response_extra_report2.xml"


# TODO: remove
def get_uitkering_data(path, info_type):
    with open(path, "rb") as f:
        tree = etree.parse(f)
        node = tree.find(UITKERING_INFO_RESPONSE_NODE)
        parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
        res = parser.parse(node, info_type)
    return res


# fmt: off
def get_uitkeringen(response: Response) -> list[dict]:
    uitkeringen_info = get_uitkering_data(path3, UitkeringInfoResponse)

    uitkeringsinstantie = uitkeringen_info.uitkerings_specificatie_client\
                                          .uitkeringsspecificatie[0]\
                                          .uitkeringsinstantie
    client = uitkeringen_info.uitkerings_specificatie_client.client
    dossierhistorien = uitkeringen_info.uitkerings_specificatie_client\
                                       .uitkeringsspecificatie[0]\
                                       .dossierhistorie
    uitkeringen = []
    for historie in dossierhistorien:
        uitkeringen.append(
            {
                "uitkeringsinstantie": uitkeringsinstantie,
                "client": client,
                "dossierhistorie": historie,
                "details": historie.componenthistorie,
            }
        )

    return uitkeringen
