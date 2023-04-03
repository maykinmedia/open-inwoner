from datetime import datetime
from uuid import uuid4

from django.urls import reverse

import requests_mock
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.tests.data import MockAPIData
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin


@requests_mock.Mocker()
class FetchKlantDataTestCase(ClearCachesMixin, DisableRequestLogMixin, WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIData.setUpServices()

    def test_list_for_bsn(self, m):
        data = MockAPIData().install_mocks(m)

        detail_url = reverse(
            "accounts:contactmoment_detail",
            kwargs={"kcm_uuid": data.klant_contactmoment["uuid"]},
        )
        list_url = reverse("accounts:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["contactmomenten"]
        self.assertEqual(len(kcms), 1)

        self.assertEqual(
            kcms[0],
            {
                "registered_date": datetime.fromisoformat(
                    data.contactmoment["registratiedatum"]
                ),
                "channel": data.contactmoment["kanaal"],
                "text": data.contactmoment["tekst"],
                "url": detail_url,
            },
        )

    def test_show_detail_for_bsn(self, m):
        data = MockAPIData().install_mocks(m)

        detail_url = reverse(
            "accounts:contactmoment_detail",
            kwargs={"kcm_uuid": data.klant_contactmoment["uuid"]},
        )
        response = self.app.get(detail_url, user=data.user)

        kcm = response.context["contactmoment"]
        self.assertEqual(
            kcm,
            {
                "registered_date": datetime.fromisoformat(
                    data.contactmoment["registratiedatum"]
                ),
                "channel": data.contactmoment["kanaal"],
                "text": data.contactmoment["tekst"],
                "url": detail_url,
            },
        )

    def test_list_requires_bsn(self, m):
        user = UserFactory()
        list_url = reverse("accounts:contactmoment_list")
        response = self.app.get(list_url, user=user)
        self.assertRedirects(response, reverse("root"))

    def test_list_requires_login(self, m):
        list_url = reverse("accounts:contactmoment_list")
        response = self.app.get(list_url)
        self.assertRedirects(response, f"{reverse('login')}?next={list_url}")

    def test_detail_requires_bsn(self, m):
        user = UserFactory()
        url = reverse("accounts:contactmoment_detail", kwargs={"kcm_uuid": uuid4()})
        response = self.app.get(url, user=user)
        self.assertRedirects(response, reverse("root"))

    def test_detail_requires_login(self, m):
        url = reverse("accounts:contactmoment_detail", kwargs={"kcm_uuid": uuid4()})
        response = self.app.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")
