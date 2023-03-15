from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_webtest import WebTest
from zgw_consumers.constants import APITypes
from zgw_consumers.test import mock_service_oas_get

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.formapi import fetch_open_submissions
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.openzaak.tests.shared import FORMS_ROOT
from open_inwoner.utils.test import ClearCachesMixin


class ESuiteData:
    def __init__(self):
        self.submission_1 = {
            "url": "https://dmidoffice2.esuite-development.net/formulieren-provider/api/v1/8e3ae29c-7bc5-4f7d-a27c-b0c83c13328e",
            "uuid": "8e3ae29c-7bc5-4f7d-a27c-b0c83c13328e",
            "naam": "Melding openbare ruimte",
            "vervolgLink": "https://dloket2.esuite-development.net/formulieren-nieuw/formulier/start/8e3ae29c-7bc5-4f7d-a27c-b0c83c13328e",
            "datumLaatsteWijziging": "2023-02-13T14:02:00.999+01:00",
            "eindDatumGeldigheid": "2023-05-14T14:02:00.999+02:00",
        }
        self.submission_2 = {
            "url": "https://dmidoffice2.esuite-development.net/formulieren-provider/api/v1/d14658b0-dcb4-4d3c-a61c-fd7d0c78f296",
            "uuid": "d14658b0-dcb4-4d3c-a61c-fd7d0c78f296",
            "naam": "Indienen bezwaarschrift",
            "vervolgLink": "https://dloket2.esuite-development.net/formulieren-nieuw/formulier/start/d14658b0-dcb4-4d3c-a61c-fd7d0c78f296",
            "datumLaatsteWijziging": "2023-02-13T14:10:26.197+01:00",
            "eindDatumGeldigheid": "2023-05-14T14:10:26.197+02:00",
        }
        # note this is a weird esuite response without pagination links
        self.response = {
            "count": 2,
            "results": [
                self.submission_1,
                self.submission_2,
            ],
        }

    def setUpOASMocks(self, m):
        mock_service_oas_get(m, FORMS_ROOT, "esuite-submissions")

    def install_mocks(self, m):
        self.setUpOASMocks(m)
        m.get(
            f"{FORMS_ROOT}openstaande-inzendingen",
            json=self.response,
        )
        return self


@requests_mock.Mocker()
class FormAPITest(ClearCachesMixin, WebTest):
    config: OpenZaakConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.config = OpenZaakConfig.get_solo()
        cls.config.form_service = ServiceFactory(
            api_root=FORMS_ROOT, api_type=APITypes.orc
        )
        cls.config.save()

        cls.user = UserFactory(bsn="900222086")
        cls.submissions_url = reverse("accounts:open_submissions")

    def test_api_fetch(self, m):
        data = ESuiteData().install_mocks(m)

        res = fetch_open_submissions(self.user.bsn)

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].url, data.submission_1["url"])

    def test_page_shows_open_submissions(self, m):
        data = ESuiteData().install_mocks(m)

        response = self.app.get(self.submissions_url, user=self.user)

        self.assertContains(response, data.submission_1["naam"])
        self.assertContains(response, data.submission_1["vervolgLink"])

        self.assertContains(response, data.submission_2["naam"])
        self.assertContains(response, data.submission_2["vervolgLink"])

    def test_page_shows_zero_submissions(self, m):
        data = ESuiteData()
        data.response["results"] = []
        data.response["count"] = 0
        data.install_mocks(m)

        response = self.app.get(self.submissions_url, user=self.user)

        self.assertContains(response, _("Er zijn geen openstaande formulieren."))

    def test_requires_auth(self, m):
        response = self.app.get(self.submissions_url)
        self.assertRedirects(
            response, f"{reverse('login')}?next={self.submissions_url}"
        )

    def test_requires_bsn(self, m):
        response = self.app.get(self.submissions_url, user=UserFactory(bsn=""))
        self.assertRedirects(response, reverse("root"))
