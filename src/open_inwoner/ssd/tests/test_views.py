"""
Tests for the Form views

The tests check that the views are login-protected, redirects work,
and appropriate errors are displayed. The *content* of the request
templates is tested in `test_client.py`, the parsing of response
contents is tested in `test_xml_parsing.py`
"""

from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from freezegun import freeze_time
from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import UserFactory

from ..client import UitkeringClient
from .mocks import mock_report

FILES_DIR = Path(__file__).parent.resolve() / "files"


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestMonthlyBenefitsFormView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ssd_client = UitkeringClient()

    def setUp(self):
        self.user = UserFactory()
        self.user.set_password("12345")
        self.user.email = "test@email.com"
        self.user.save()

    def test_uitkering_get(self):
        url = reverse("ssd:monthly_benefits_index")

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            response.url,
            "/accounts/login/?next=/uitkeringen/maandspecificaties/",
        )

        # request with user logged in
        self.client.login(email=self.user.email, password="12345")

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

        doc = PyQuery(response.content)

        breadcrumbs = doc.find(".breadcrumbs__list-item")

        self.assertEqual(len(breadcrumbs), 2)
        self.assertIn(_("Mijn uitkeringen"), breadcrumbs[1].find("a").text)

    @patch(
        "open_inwoner.ssd.client.UitkeringClient.get_reports",
        return_value=mock_report(str(FILES_DIR / "uitkering_response_basic.xml")),
    )
    @freeze_time("1985-12-25")
    def test_uitkering_post_success(self, mock_report):
        url = reverse("ssd:monthly_benefits_index")
        self.client.login(email=self.user.email, password="12345")

        response = self.client.post(url, data={"report_date": "1985-12-25"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.headers["content-type"], "application/pdf")

    @patch(
        "open_inwoner.ssd.client.UitkeringClient.get_reports",
        return_value=None,
    )
    @freeze_time("1985-12-25")
    def test_uitkering_post_fail(self, mock_report):
        url = reverse("ssd:monthly_benefits_index")
        self.client.login(email=self.user.email, password="12345")

        response = self.client.post(url, data={"report_date": "1985-12-25"})

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        response = self.client.get(response.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertContains(
            response, "Geen uitkeringsspecificatie gevonden voor december 1985"
        )

    @patch(
        "open_inwoner.ssd.client.UitkeringClient.get_reports",
        return_value=None,
    )
    @freeze_time("1985-12-25")
    def test_uitkering_post_bad_input(self, mock_report):
        url = reverse("ssd:monthly_benefits_index")
        self.client.login(email=self.user.email, password="12345")

        with self.assertRaises(ValueError):
            self.client.post(url, data={"report_date": "bad-user-input"})

    @patch("open_inwoner.ssd.models.SSDConfig.get_solo")
    def test_uitkering_get_reports_not_enabled(self, mock_solo):
        mock_solo.return_value.maandspecificatie_enabled = False

        url = reverse("ssd:monthly_benefits_index")

        self.client.login(email=self.user.email, password="12345")

        response = self.client.get(url)

        self.assertContains(
            response, "Downloaden van maandoverzichten wordt niet ondersteund."
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestYearlyBenefitsFormView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.user.set_password("12345")
        self.user.email = "test@email.com"
        self.user.save()

    def test_jaaropgave_get(self):

        # request with anonymous user
        url = reverse("ssd:yearly_benefits_index")
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            response.url, "/accounts/login/?next=/uitkeringen/jaaropgaven/"
        )

        # request with user logged in
        self.client.login(email=self.user.email, password="12345")

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    @patch(
        "open_inwoner.ssd.client.JaaropgaveClient.get_reports",
        return_value=mock_report(str(FILES_DIR / "jaaropgave_response.xml")),
    )
    @freeze_time("1985-12-25")
    def test_jaaropgave_post_success(self, mock_report):
        url = reverse("ssd:yearly_benefits_index")
        self.client.login(email=self.user.email, password="12345")

        response = self.client.post(url, data={"report_date": "1984-12-1"})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.headers["content-type"], "application/pdf")

    @patch(
        "open_inwoner.ssd.client.JaaropgaveClient.get_reports",
        return_value=None,
    )
    @freeze_time("1985-12-25")
    def test_jaaropgave_post_fail(self, mock_report):
        url = reverse("ssd:yearly_benefits_index")
        self.client.login(email=self.user.email, password="12345")

        response = self.client.post(url, data={"report_date": "1984-12-25"})

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        response = self.client.get(response.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertContains(response, "Geen uitkeringsspecificatie gevonden voor 1984")

    @patch("open_inwoner.ssd.forms.SSDConfig.get_solo")
    def test_jaaropgave_get_reports_not_enabled(self, mock_solo):
        mock_solo.return_value.jaaropgave_enabled = False

        url = reverse("ssd:yearly_benefits_index")

        self.client.login(email=self.user.email, password="12345")

        response = self.client.get(url)

        self.assertContains(
            response, "Downloaden van jaaroverzichten wordt niet ondersteund."
        )
