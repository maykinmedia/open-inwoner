from lxml import etree
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.handlers import LxmlEventHandler


def mock_get_report_info(path, info_response_node, info_type):  # pragma: no cover
    """
    Mock SOAP response content by retrieving XML data from files
    """
    with open(path, "rb") as f:
        tree = etree.parse(f)  # nosec
        node = tree.find(info_response_node)
        parser = XmlParser(context=XmlContext(), handler=LxmlEventHandler)
        res = parser.parse(node, info_type)
    return res


def get_component_value(componenthistorie, omschrijving):  # pragma: no cover
    """
    Retrieve the value ("waarde_bedrag") of a component from the
    componenthistorie by `omschrijving'
    """
    return next(
        (item for item in componenthistorie if item.omschrijving == omschrijving)
    ).bedrag.waarde_bedrag
