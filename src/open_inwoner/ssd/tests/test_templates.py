from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from pyquery import PyQuery

from ..client import UitkeringClient
from ..service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)
from ..xml import get_uitkeringen
from .utils import get_total_component_value, mock_get_report_info, render_html

UITKERING_INFO_RESPONSE_NODE = (
    "//{http://www.centric.nl/GWS/Diensten/UitkeringsSpecificatieClient/v0600}"
    "UitkeringsSpecificatieInfoResponse"
)

FILES_DIR = Path(__file__).parent.resolve() / "files"


class UitkeringTemplateTest(TestCase):
    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_template_uitkering_basic(self, m):
        """
        Validate uitkering template for basic response
        """
        ssd_client = UitkeringClient()
        uitkering_path = FILES_DIR / "uitkering_response_basic.xml"
        m.return_value = mock_get_report_info(
            uitkering_path, UITKERING_INFO_RESPONSE_NODE, UitkeringInfoResponse
        )

        uitkeringen = get_uitkeringen(None)

        html = render_html(ssd_client.html_template, context={"reports": uitkeringen})

        doc = PyQuery(html)

        components = doc.find(".monthly-report__td")
        # remove empty columns to make rows + values contiguous
        filtered = [item for item in components if item.text]

        kd_norm = get_total_component_value(filtered, "KD norm tot AOW")
        gekorte_inkomsten = get_total_component_value(
            filtered, "TOTAAL GEKORTE INKOMSTEN"
        )
        reserving_vakantiegeld = get_total_component_value(
            filtered, "RESERVERING VAKANTIEGELD"
        )
        totaal_netto = get_total_component_value(filtered, "TOTAAL NETTO BIJSTAND")

        # check totaal_netto
        self.assertEqual(
            totaal_netto, round(kd_norm - gekorte_inkomsten - reserving_vakantiegeld, 2)
        )

        aflossing_vordering = get_total_component_value(filtered, "Aflossing vordering")
        uit_te_betalen = get_total_component_value(filtered, "UIT TE BETALEN BEDRAG")

        # check uit_te_betalen
        self.assertEqual(uit_te_betalen, round(totaal_netto - aflossing_vordering, 2))

    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_template_uitkering_extra_row(self, m):
        """
        Validate uitkering template for response with additional row "KD norm tot AOW"
        """
        ssd_client = UitkeringClient()
        uitkering_path = FILES_DIR / "uitkering_response_extra_row.xml"
        m.return_value = mock_get_report_info(
            uitkering_path, UITKERING_INFO_RESPONSE_NODE, UitkeringInfoResponse
        )

        uitkeringen = get_uitkeringen(None)

        html = render_html(ssd_client.html_template, context={"reports": uitkeringen})

        doc = PyQuery(html)

        components = doc.find(".monthly-report__td")
        # remove empty columns to make rows + values contiguous
        filtered = [item for item in components if item.text]

        kd_norm = get_total_component_value(filtered, "KD norm tot AOW")
        gekorte_inkomsten = get_total_component_value(
            filtered, "TOTAAL GEKORTE INKOMSTEN"
        )
        reserving_vakantiegeld = get_total_component_value(
            filtered, "RESERVERING VAKANTIEGELD"
        )
        uitbetaling_vakantiegeld = get_total_component_value(
            filtered, "Uitbetaling vakantiegeld"
        )
        totaal_netto = get_total_component_value(filtered, "TOTAAL NETTO BIJSTAND")

        self.assertEqual(
            totaal_netto,
            round(
                kd_norm
                - gekorte_inkomsten
                - reserving_vakantiegeld
                + uitbetaling_vakantiegeld,
                2,
            ),
        )

        aflossing_vordering = get_total_component_value(filtered, "Aflossing vordering")
        overige_reserveringen = get_total_component_value(
            filtered, "Overige reserveringen"
        )
        uit_te_betalen = get_total_component_value(filtered, "UIT TE BETALEN BEDRAG")

        # check uit te betalen
        self.assertEqual(
            uit_te_betalen,
            round(totaal_netto - aflossing_vordering - overige_reserveringen, 2),
        )
