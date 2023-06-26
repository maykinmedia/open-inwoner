from io import BytesIO
from pathlib import Path

from django.test import SimpleTestCase

from lxml import etree

from open_inwoner.ssd.client import JaaropgaveClient, SSDClient

TEST_FILES_DIR = Path(__file__).resolve().parent / "files"


class HAckAndDevRenderTest(SimpleTestCase):
    """
    some code for hacking and development
    """

    def test_xpath(self):
        soap_path = TEST_FILES_DIR / "jaaropgave-testresponse.xml"
        # soap_path = TEST_FILES_DIR / "JaarOpgaveClient_v0400_respons.xml"
        with open(soap_path, "rb") as f:
            soap_doc = etree.parse(f)

        namespaces = {
            "SOAP-ENV": "http://schemas.xmlsoap.org/soap/envelope/",
            "gwsd": "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0400",
            "ns3": "http://www.centric.nl/GWS/Header/v0201",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "wsa": "http://www.w3.org/2005/08/addressing",
            "gwsh": "http://www.centric.nl/GWS/Header/v0201",
            "gwsb": "http://www.centric.nl/GWS/Diensten/JaarOpgaveClient/v0300",
        }

        value = soap_doc.xpath(
            "SOAP-ENV:Body/gwsd:Response/JaarOpgaveClient/Client/BurgerServiceNr",
            namespaces=namespaces,
        )
        print(value)
        self.assertNotEqual(value, [])

    def test_custom_functions(self):
        # https://stackoverflow.com/questions/51452779/is-it-possible-to-use-lxml-extension-functions-in-xpath-predicates-in-xslt-style

        root = etree.XML('<a><b class="true">Haegar</b><b class="false">Baegar</b></a>')
        doc = etree.ElementTree(root)

        def match_class(context, arg):
            return (
                "class" in context.context_node.attrib
                and context.context_node.attrib["class"] == arg
            )

        ns = etree.FunctionNamespace("http://example.com/myother/functions")
        ns.prefix = "css"
        ns["class"] = match_class

        result = root.xpath("//*[css:class('true')]")
        assert result[0].text == "Haegar"

        xslt = etree.XSLT(
            etree.XML(
                """\
           <stylesheet version="1.0"
                  xmlns="http://www.w3.org/1999/XSL/Transform"
                  xmlns:css="http://example.com/myother/functions">
             <output method="text" encoding="ASCII"/>
             <template match="/">
                <apply-templates select="//*[css:class('true')]"/>
             </template>
           </stylesheet>
        """
            )
        )

        result = xslt(doc)
        assert str(result) == "Haegar"
        print(str(result))

    def test_render_xslt_with_params(self):
        xslt_tree = etree.XML(
            """
        <xsl:stylesheet version="1.0"
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
            <xsl:param name="a" />
            <xsl:template match="/">
                <foo><xsl:value-of select="$a" /></foo>
            </xsl:template>
        </xsl:stylesheet>"""
        )

        transform = etree.XSLT(xslt_tree)
        doc_root = etree.XML("<dummy></dummy>")
        result = transform(doc_root, a=str(123))

        print(str(result))

    def test_render_xslt_from_simple_data_tree(self):
        # add data to simple XML tree
        root = etree.Element("root")
        bsn = etree.SubElement(root, "bsn")
        bsn.text = "123456789"

        print(etree.tostring(root))

        xslt_tree = etree.XML(
            """
        <xsl:stylesheet version="1.0"
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
            <xsl:output method="xml" version="1.0" encoding="utf-8" omit-xml-declaration="no" indent="yes"/>
            <xsl:template match="/root">
                <foo><xsl:value-of select="bsn"/></foo>
            </xsl:template>
        </xsl:stylesheet>"""
        )

        # generate more complex
        transform = etree.XSLT(xslt_tree)
        result = transform(root)

        print(str(result))

        out = BytesIO()
        result.write_output(out)
        data = out.getvalue()
        print(data.decode("utf8"))

    def test_client(self):
        client = JaaropgaveClient()
        req = client.get_jaaropgave(123456789, 2022)
        print(req.decode("utf8"))
