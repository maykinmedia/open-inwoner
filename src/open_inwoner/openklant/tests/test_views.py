from datetime import datetime
from uuid import uuid4

from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.tests.data import MockAPIData
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class FetchKlantDataTestCase(ClearCachesMixin, DisableRequestLogMixin, WebTest):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIData.setUpServices()

    def test_list_for_bsn(self, m):
        data = MockAPIData().install_mocks(m)

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={"kcm_uuid": data.klant_contactmoment["uuid"]},
        )
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["contactmomenten"]
        self.assertEqual(len(kcms), 1)

        self.assertEqual(
            kcms[0],
            {
                "registered_date": datetime.fromisoformat(
                    data.contactmoment["registratiedatum"]
                ),
                "channel": data.contactmoment["kanaal"].title(),
                "text": data.contactmoment["tekst"],
                "onderwerp": data.contactmoment["onderwerp"],
                "antwoord": data.contactmoment["antwoord"],
                "identificatie": data.contactmoment["identificatie"],
                "type": data.contactmoment["type"],
                "status": _("Afgehandeld"),
                "url": detail_url,
            },
        )

    def test_show_detail_for_bsn(self, m):
        data = MockAPIData().install_mocks(m)

        detail_url = reverse(
            "cases:contactmoment_detail",
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
                "channel": data.contactmoment["kanaal"].title(),
                "text": data.contactmoment["tekst"],
                "onderwerp": data.contactmoment["onderwerp"],
                "antwoord": data.contactmoment["antwoord"],
                "identificatie": data.contactmoment["identificatie"],
                "type": data.contactmoment["type"],
                "status": _("Afgehandeld"),
                "url": detail_url,
            },
        )

    def test_list_requires_bsn(self, m):
        user = UserFactory()
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=user)
        self.assertRedirects(response, reverse("root"))

    def test_list_requires_login(self, m):
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url)
        self.assertRedirects(response, f"{reverse('login')}?next={list_url}")

    def test_detail_requires_bsn(self, m):
        user = UserFactory()
        url = reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": uuid4()})
        response = self.app.get(url, user=user)
        self.assertRedirects(response, reverse("root"))

    def test_detail_requires_login(self, m):
        url = reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": uuid4()})
        response = self.app.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")
