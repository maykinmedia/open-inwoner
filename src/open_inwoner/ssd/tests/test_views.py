from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.accounts.tests.factories import UserFactory

from .mocks import mock_report

FILES_DIR = Path(__file__).parent.resolve() / "files"


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestDownloadBenefitsReportView(TestCase):
    """Smoke tests for the download of monthly/yearly benefits reports

    The tests check that the views are login-protected and that download
    works. The content of the request template is tested in `test_client.py`,
    the parsing of response contents is tested in `test_xml_parsing.py`
    """

    @classmethod
    def setUp(self):
        self.user = UserFactory()
        self.user.set_password("12345")
        self.user.email = "test@email.com"
        self.user.save()

    @patch(
        "open_inwoner.ssd.client.UitkeringClient._get_maandspecificatie",
        return_value=mock_report(str(FILES_DIR / "uitkering_response.xml")),
    )
    def test_download_monthly_report(self, mock_report):
        url = reverse(
            "profile:download_monthly_benefits", kwargs={"file_name": "May 2023"}
        )

        # request with anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # request with user logged in
        self.client.login(email=self.user.email, password="12345")

        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(
        "open_inwoner.ssd.client.JaaropgaveClient._get_jaaropgave",
        return_value=mock_report(str(FILES_DIR / "jaaropgave_response.xml")),
    )
    def test_download_yearly_report(self, mock_report):
        url = reverse("profile:download_yearly_benefits", kwargs={"file_name": "2023"})

        # request with anonymous user
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        # request with user logged in
        self.client.login(email=self.user.email, password="12345")

        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
