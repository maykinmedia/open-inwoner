from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.templatetags.static import static
from django.test import TestCase, override_settings

import weasyprint
from maykin_common.pdf import UrlFetcher
from pyquery import PyQuery

from open_inwoner.ssd.client import JaaropgaveClient, UitkeringClient
from open_inwoner.ssd.models import SSDConfig
from open_inwoner.ssd.service.jaaropgave import JaarOpgaveInfoResponse
from open_inwoner.ssd.service.uitkering import (
    UitkeringsSpecificatieInfoResponse as UitkeringInfoResponse,
)
from open_inwoner.ssd.xml import (
    JAAROPGAVE_INFO_RESPONSE_NODE,
    get_jaaropgaven,
    get_uitkeringen,
)
from open_inwoner.utils.export import render_pdf
from open_inwoner.utils.url import build_absolute_url

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

        config = SSDConfig.get_solo()
        # Set ProsemirrorModelField with JSON data
        config.maandspecificatie_pdf_comments = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Lorem ipsum dolor sit amet..."}
                    ],
                }
            ],
        }
        config.save()

        # Reload config to get ProsemirrorFieldDocument
        config = SSDConfig.get_solo()
        comments_html = config.maandspecificatie_pdf_comments.html

        uitkeringen = get_uitkeringen(None)

        html = render_html(
            ssd_client.html_template,
            context={
                "reports": uitkeringen,
                "comments": comments_html,
            },
        )

        self.assertIn("Lorem ipsum dolor sit amet...", html)

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


@override_settings(STATIC_ROOT=settings.STATICFILES_DIRS[0])
class ReportStylesheetTest(TestCase):
    """
    The SSD templates don't extend `base_pdf.html`, so they must link the PDF
    stylesheets themselves for them to be picked up by the PDF renderer.

    `collectstatic` isn't run before the tests, so `STATIC_ROOT` points at the
    project's static directory, where the frontend build puts the bundles. (Not
    `DEBUG=True`, which would make maykin-common use the staticfiles finders, but
    also resets Django's template engines and breaks later tests.)
    """

    def assertStylesheetsResolvedLocally(self, template, reports):
        with (
            patch.object(
                UrlFetcher, "fetch", autospec=True, side_effect=UrlFetcher.fetch
            ) as fetch,
            # maykin-common falls back to WeasyPrint's (network) fetcher for any
            # URL it cannot resolve to a local file
            patch.object(weasyprint.URLFetcher, "fetch") as network_fetch,
        ):
            render_pdf(template, context={"reports": reports})

        fetched_stylesheets = [
            call.args[1]
            for call in fetch.call_args_list
            if call.args[1].endswith(".css")
        ]
        self.assertEqual(
            fetched_stylesheets,
            [
                build_absolute_url(static("bundles/pdf-p.css")),
                build_absolute_url(static("bundles/open_inwoner-css.css")),
            ],
        )
        network_fetch.assert_not_called()

    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_jaaropgave_stylesheets(self, m):
        m.return_value = mock_get_report_info(
            FILES_DIR / "jaaropgave_response.xml",
            JAAROPGAVE_INFO_RESPONSE_NODE,
            JaarOpgaveInfoResponse,
        )

        self.assertStylesheetsResolvedLocally(
            JaaropgaveClient.html_template, get_jaaropgaven(None)
        )

    @patch("open_inwoner.ssd.xml._get_report_info")
    def test_maandspecificatie_stylesheets(self, m):
        m.return_value = mock_get_report_info(
            FILES_DIR / "uitkering_response_basic.xml",
            UITKERING_INFO_RESPONSE_NODE,
            UitkeringInfoResponse,
        )

        self.assertStylesheetsResolvedLocally(
            UitkeringClient.html_template, get_uitkeringen(None)
        )
