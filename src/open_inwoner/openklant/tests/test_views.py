from datetime import datetime
from uuid import uuid4

from django.test import modify_settings, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.tests.data import MockAPIReadData
from open_inwoner.utils.test import (
    ClearCachesMixin,
    DisableRequestLogMixin,
    set_kvk_branch_number_in_session,
)


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@modify_settings(
    MIDDLEWARE={"remove": ["open_inwoner.kvk.middleware.KvKLoginMiddleware"]}
)
class FetchKlantDataTestCase(ClearCachesMixin, DisableRequestLogMixin, WebTest):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIReadData.setUpServices()

    def test_list_for_bsn(self, m):
        data = MockAPIReadData().install_mocks(m)

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

    def test_list_for_kvk_or_rsin(self, m):
        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                data = MockAPIReadData().install_mocks(m)

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={"kcm_uuid": data.klant_contactmoment2["uuid"]},
                )
                list_url = reverse("cases:contactmoment_list")
                response = self.app.get(list_url, user=data.eherkenning_user)

                kcms = response.context["contactmomenten"]
                self.assertEqual(len(kcms), 1)

                self.assertEqual(
                    kcms[0],
                    {
                        "registered_date": datetime.fromisoformat(
                            data.contactmoment2["registratiedatum"]
                        ),
                        "channel": data.contactmoment2["kanaal"].title(),
                        "text": data.contactmoment2["tekst"],
                        "onderwerp": data.contactmoment2["onderwerp"],
                        "antwoord": data.contactmoment2["antwoord"],
                        "identificatie": data.contactmoment2["identificatie"],
                        "type": data.contactmoment2["type"],
                        "status": _("Afgehandeld"),
                        "url": detail_url,
                    },
                )

    @set_kvk_branch_number_in_session("1234")
    def test_list_for_vestiging(self, m):
        data = MockAPIReadData().install_mocks(m)
        self.client.force_login(user=data.eherkenning_user)

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={"kcm_uuid": data.klant_contactmoment4["uuid"]},
                )
                list_url = reverse("cases:contactmoment_list")

                response = self.client.get(list_url)

                kcms = response.context["contactmomenten"]
                self.assertEqual(len(kcms), 1)

                self.assertEqual(
                    kcms[0],
                    {
                        "registered_date": datetime.fromisoformat(
                            data.contactmoment_vestiging["registratiedatum"]
                        ),
                        "channel": data.contactmoment_vestiging["kanaal"].title(),
                        "text": data.contactmoment_vestiging["tekst"],
                        "onderwerp": data.contactmoment_vestiging["onderwerp"],
                        "antwoord": data.contactmoment_vestiging["antwoord"],
                        "identificatie": data.contactmoment_vestiging["identificatie"],
                        "type": data.contactmoment_vestiging["type"],
                        "status": _("Afgehandeld"),
                        "url": detail_url,
                    },
                )

    def test_show_detail_for_bsn(self, m):
        data = MockAPIReadData().install_mocks(m)

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

    def test_show_detail_for_kvk_or_rsin(self, m):
        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                data = MockAPIReadData().install_mocks(m)

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={"kcm_uuid": data.klant_contactmoment2["uuid"]},
                )
                response = self.app.get(detail_url, user=data.eherkenning_user)

                kcm = response.context["contactmoment"]
                self.assertEqual(
                    kcm,
                    {
                        "registered_date": datetime.fromisoformat(
                            data.contactmoment2["registratiedatum"]
                        ),
                        "channel": data.contactmoment2["kanaal"].title(),
                        "text": data.contactmoment2["tekst"],
                        "onderwerp": data.contactmoment2["onderwerp"],
                        "antwoord": data.contactmoment2["antwoord"],
                        "identificatie": data.contactmoment2["identificatie"],
                        "type": data.contactmoment2["type"],
                        "status": _("Afgehandeld"),
                        "url": detail_url,
                    },
                )

    @set_kvk_branch_number_in_session("1234")
    def test_show_detail_for_vestiging(self, m):
        data = MockAPIReadData().install_mocks(m)
        self.client.force_login(user=data.eherkenning_user)

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={"kcm_uuid": data.klant_contactmoment4["uuid"]},
                )
                response = self.client.get(detail_url)

                kcm = response.context["contactmoment"]
                self.assertEqual(
                    kcm,
                    {
                        "registered_date": datetime.fromisoformat(
                            data.contactmoment_vestiging["registratiedatum"]
                        ),
                        "channel": data.contactmoment_vestiging["kanaal"].title(),
                        "text": data.contactmoment_vestiging["tekst"],
                        "onderwerp": data.contactmoment_vestiging["onderwerp"],
                        "antwoord": data.contactmoment_vestiging["antwoord"],
                        "identificatie": data.contactmoment_vestiging["identificatie"],
                        "type": data.contactmoment_vestiging["type"],
                        "status": _("Afgehandeld"),
                        "url": detail_url,
                    },
                )

    @set_kvk_branch_number_in_session("1234")
    def test_cannot_access_detail_for_hoofdvestiging_as_vestiging(self, m):
        data = MockAPIReadData().install_mocks(m)
        self.client.force_login(user=data.eherkenning_user)

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={"kcm_uuid": data.klant_contactmoment2["uuid"]},
                )
                response = self.client.get(detail_url)

                self.assertEqual(response.status_code, 404)

    def test_list_requires_bsn_or_kvk(self, m):
        user = UserFactory()
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=user)
        self.assertRedirects(response, reverse("pages-root"))

    def test_list_requires_login(self, m):
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url)
        self.assertRedirects(response, f"{reverse('login')}?next={list_url}")

    def test_detail_requires_bsn_or_kvk(self, m):
        user = UserFactory()
        url = reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": uuid4()})
        response = self.app.get(url, user=user)
        self.assertRedirects(response, reverse("pages-root"))

    def test_detail_requires_login(self, m):
        url = reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": uuid4()})
        response = self.app.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")
