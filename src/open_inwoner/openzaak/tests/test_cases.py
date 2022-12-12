import datetime
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse, reverse_lazy

import requests_mock
from django_webtest import WebTest
from furl import furl
from timeline_logger.models import TimelineLog
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.accounts.views.cases import CaseListMixin
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from ..models import OpenZaakConfig
from .factories import ServiceFactory

ZAKEN_ROOT = "https://zaken.nl/api/v1/"
CATALOGI_ROOT = "https://catalogi.nl/api/v1/"


class CaseListAccessTests(WebTest):
    urls = [
        reverse_lazy("accounts:my_open_cases"),
        reverse_lazy("accounts:my_closed_cases"),
    ]

    @classmethod
    def setUpTestData(cls):
        # services
        cls.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        cls.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        # openzaak config
        cls.config = OpenZaakConfig.get_solo()
        cls.config.zaak_service = cls.zaak_service
        cls.config.catalogi_service = cls.catalogi_service
        cls.config.save()

    def test_user_is_redirected_to_root_when_not_logged_in_via_digid(self):
        # User's bsn is None when logged in by email (default method)
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        for url in self.urls:
            with self.subTest(url):
                response = self.app.get(url, user=user)

                self.assertRedirects(response, reverse("root"))

    def test_anonymous_user_has_no_access_to_cases_page(self):
        user = AnonymousUser()

        for url in self.urls:
            with self.subTest(url):
                response = self.app.get(url, user=user)

                self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_missing_zaak_client_returns_empty_list(self):
        user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="john@smith.nl"
        )
        self.config.zaak_service = None
        self.config.save()

        for url in self.urls:
            with self.subTest(url):
                response = self.app.get(url, user=user)

                self.assertEquals(response.status_code, 200)
                self.assertListEqual(response.context.get("cases"), [])

    @requests_mock.Mocker()
    def test_no_cases_are_retrieved_when_http_404(self, m):
        user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="john@smith.nl"
        )
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            status_code=404,
        )

        for url in self.urls:
            with self.subTest(url):
                response = self.app.get(url, user=user)

                self.assertEquals(response.status_code, 200)
                self.assertListEqual(response.context.get("cases"), [])

    @requests_mock.Mocker()
    def test_no_cases_are_retrieved_when_http_500(self, m):
        user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="john@smith.nl"
        )
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            status_code=500,
        )

        for url in self.urls:
            with self.subTest(url):
                response = self.app.get(url, user=user)

                self.assertEquals(response.status_code, 200)
                self.assertListEqual(response.context.get("cases"), [])


@requests_mock.Mocker()
class CaseListViewTests(ClearCachesMixin, WebTest):
    url_open = reverse_lazy("accounts:my_open_cases")
    url_closed = reverse_lazy("accounts:my_closed_cases")

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        # services
        cls.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        cls.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        # openzaak config
        cls.config = OpenZaakConfig.get_solo()
        cls.config.zaak_service = cls.zaak_service
        cls.config.catalogi_service = cls.catalogi_service
        cls.config.zaak_max_confidentiality = (
            VertrouwelijkheidsAanduidingen.beperkt_openbaar
        )
        cls.config.save()

        cls.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f",
            omschrijving="Coffee zaaktype",
            catalogus=f"{CATALOGI_ROOT}catalogussen/1b643db-81bb-d71bd5a2317a",
            vertrouwelijkheidaanduiding="openbaar",
        )
        cls.status_type1 = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-777yu878km09",
            zaaktype=cls.zaaktype["url"],
            omschrijving="Initial request",
            volgnummer=1,
            is_eindstatus=False,
        )
        cls.status_type2 = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-744516671fe4",
            zaaktype=cls.zaaktype["url"],
            omschrijving="Finish",
            volgnummer=2,
            is_eindstatus=True,
        )
        # open
        cls.zaak1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            uuid="d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0000000001",
            omschrijving="Coffee zaak 1",
            startdatum="2022-01-02",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c9023450083c",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.status1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=cls.zaak1["status"],
            zaak=cls.zaak1["url"],
            statustype=cls.status_type1["url"],
            datum_status_gezet="2021-01-12",
            statustoelichting="",
        )
        cls.zaak2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            uuid="e4d469b9-6666-4bdd-bf42-b53445298102",
            zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0008800002",
            omschrijving="Coffee zaak 2",
            startdatum="2022-01-12",
            einddatum=None,
            status=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-beu760sle929",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.status2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=cls.zaak2["status"],
            zaak=cls.zaak2["url"],
            statustype=cls.status_type1["url"],
            datum_status_gezet="2021-03-12",
            statustoelichting="",
        )
        # closed
        cls.zaak3 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/6f8de38f-85ea-42d3-978c-845a033335a7",
            uuid="6f8de38f-85ea-42d3-978c-845a033335a7",
            zaaktype=cls.zaaktype["url"],
            identificatie="ZAAK-2022-0001000003",
            omschrijving="Coffee zaak closed",
            startdatum="2021-07-26",
            einddatum="2022-01-16",
            status=f"{ZAKEN_ROOT}statussen/98659876-bbb3-476a-ad13-n3nvcght758js",
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.status3 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=cls.zaak3["status"],
            zaak=cls.zaak3["url"],
            statustype=cls.status_type2["url"],
            datum_status_gezet="2021-03-15",
            statustoelichting="",
        )

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            furl(f"{ZAKEN_ROOT}zaken")
            .add(
                {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": self.user.bsn,
                    "maximaleVertrouwelijkheidaanduiding": VertrouwelijkheidsAanduidingen.beperkt_openbaar,
                }
            )
            .url,
            json=paginated_response([self.zaak1, self.zaak2, self.zaak3]),
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            json=paginated_response([self.status_type1, self.status_type2]),
        )
        for resource in [
            self.zaaktype,
            self.status_type1,
            self.status_type2,
            self.status1,
            self.status2,
            self.status3,
        ]:
            m.get(resource["url"], json=resource)

    def test_list_open_cases(self, m):
        self._setUpMocks(m)

        response = self.app.get(self.url_open, user=self.user)

        self.assertListEqual(
            response.context.get("cases"),
            [
                {
                    "uuid": self.zaak2["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak2["startdatum"]),
                    "end_date": None,
                    "identificatie": self.zaak2["identificatie"],
                    "description": self.zaak2["omschrijving"],
                    "zaaktype_description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type1["omschrijving"],
                },
                {
                    "uuid": self.zaak1["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak1["startdatum"]),
                    "end_date": None,
                    "identificatie": self.zaak1["identificatie"],
                    "description": self.zaak1["omschrijving"],
                    "zaaktype_description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type1["omschrijving"],
                },
            ],
        )
        # don't show closed cases
        self.assertNotContains(response, self.zaak3["identificatie"])
        self.assertNotContains(response, self.zaak3["omschrijving"])

        # check zaken request query parameters
        list_zaken_req = [
            req
            for req in m.request_history
            if req.hostname == "zaken.nl" and req.path == "/api/v1/zaken"
        ][0]
        self.assertEqual(len(list_zaken_req.qs), 2)
        self.assertEqual(
            list_zaken_req.qs,
            {
                "rol__betrokkeneidentificatie__natuurlijkpersoon__inpbsn": [
                    self.user.bsn
                ],
                "maximalevertrouwelijkheidaanduiding": [
                    VertrouwelijkheidsAanduidingen.beperkt_openbaar
                ],
            },
        )

    def test_list_open_cases_logs_displayed_case_ids(self, m):
        self._setUpMocks(m)

        self.app.get(self.url_open, user=self.user)

        # check access logs for displayed cases
        logs = list(TimelineLog.objects.all())

        case_log = [
            l for l in logs if self.zaak1["identificatie"] in l.extra_data["message"]
        ]
        self.assertEqual(len(case_log), 1)
        self.assertEqual(self.user, case_log[0].user)
        self.assertEqual(self.user, case_log[0].content_object)

        case_log = [
            l for l in logs if self.zaak2["identificatie"] in l.extra_data["message"]
        ]
        self.assertEqual(len(case_log), 1)
        self.assertEqual(self.user, case_log[0].user)
        self.assertEqual(self.user, case_log[0].content_object)

        # no logs for non-displayed cases
        for log in logs:
            self.assertNotIn(self.zaak3["identificatie"], log.extra_data["message"])

    def test_list_closed_cases(self, m):
        self._setUpMocks(m)

        response = self.app.get(self.url_closed, user=self.user)

        self.assertListEqual(
            response.context.get("cases"),
            [
                {
                    "uuid": self.zaak3["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak3["startdatum"]),
                    "end_date": datetime.date.fromisoformat(self.zaak3["einddatum"]),
                    "identificatie": self.zaak3["identificatie"],
                    "description": self.zaak3["omschrijving"],
                    "zaaktype_description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type2["omschrijving"],
                },
            ],
        )
        # don't show closed cases
        for open_zaak in [self.zaak1, self.zaak2]:
            self.assertNotContains(response, open_zaak["identificatie"])
            self.assertNotContains(response, open_zaak["omschrijving"])

        # check zaken request query parameters
        list_zaken_req = [
            req
            for req in m.request_history
            if req.hostname == "zaken.nl" and req.path == "/api/v1/zaken"
        ][0]
        self.assertEqual(len(list_zaken_req.qs), 2)
        self.assertEqual(
            list_zaken_req.qs,
            {
                "rol__betrokkeneidentificatie__natuurlijkpersoon__inpbsn": [
                    self.user.bsn
                ],
                "maximalevertrouwelijkheidaanduiding": [
                    VertrouwelijkheidsAanduidingen.beperkt_openbaar
                ],
            },
        )

    def test_list_closed_cases_logs_displayed_case_ids(self, m):
        self._setUpMocks(m)

        self.app.get(self.url_closed, user=self.user)

        # check access logs for displayed cases
        logs = list(TimelineLog.objects.all())

        case_log = [
            l for l in logs if self.zaak3["identificatie"] in l.extra_data["message"]
        ]
        self.assertEqual(len(case_log), 1)
        self.assertEqual(self.user, case_log[0].user)
        self.assertEqual(self.user, case_log[0].content_object)

        # no logs for non-displayed cases
        for log in logs:
            self.assertNotIn(self.zaak1["identificatie"], log.extra_data["message"])
            self.assertNotIn(self.zaak2["identificatie"], log.extra_data["message"])

    @patch.object(CaseListMixin, "paginate_by", 1)
    def test_list_cases_paginated(self, m):
        """
        show only one case and url to the next page
        """
        self._setUpMocks(m)

        # 1. test first page
        response_1 = self.app.get(self.url_open, user=self.user)

        self.assertListEqual(
            response_1.context.get("cases"),
            [
                {
                    "uuid": self.zaak2["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak2["startdatum"]),
                    "end_date": None,
                    "identificatie": self.zaak2["identificatie"],
                    "description": self.zaak2["omschrijving"],
                    "zaaktype_description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type1["omschrijving"],
                },
            ],
        )
        self.assertNotContains(response_1, self.zaak1["identificatie"])
        self.assertNotContains(response_1, self.zaak1["omschrijving"])
        self.assertContains(response_1, "?page=2")

        # 2. test next page
        next_page = f"{self.url_open}?page=2"
        response_2 = self.app.get(next_page, user=self.user)

        self.assertListEqual(
            response_2.context.get("cases"),
            [
                {
                    "uuid": self.zaak1["uuid"],
                    "start_date": datetime.date.fromisoformat(self.zaak1["startdatum"]),
                    "end_date": None,
                    "identificatie": self.zaak1["identificatie"],
                    "description": self.zaak1["omschrijving"],
                    "zaaktype_description": self.zaaktype["omschrijving"],
                    "current_status": self.status_type1["omschrijving"],
                },
            ],
        )
        self.assertNotContains(response_2, self.zaak2["identificatie"])
        self.assertNotContains(response_2, self.zaak2["omschrijving"])
        self.assertContains(response_2, "?page=1")

    @patch.object(CaseListMixin, "paginate_by", 1)
    def test_list_cases_paginated_logs_displayed_case_ids(self, m):
        self._setUpMocks(m)

        # 1. test first page
        response = self.app.get(self.url_open, user=self.user)
        self.assertEqual(response.context.get("cases")[0]["uuid"], self.zaak2["uuid"])

        # check access logs for displayed cases
        logs = list(TimelineLog.objects.all())

        case_log = [
            l for l in logs if self.zaak2["identificatie"] in l.extra_data["message"]
        ]
        self.assertEqual(len(case_log), 1)
        self.assertEqual(self.user, case_log[0].user)
        self.assertEqual(self.user, case_log[0].content_object)

        # no logs for non-displayed cases
        for log in logs:
            self.assertNotIn(self.zaak1["identificatie"], log.extra_data["message"])
            self.assertNotIn(self.zaak3["identificatie"], log.extra_data["message"])

        # clear logs for testing
        TimelineLog.objects.all().delete()

        # 2. test next page
        next_page = f"{self.url_open}?page=2"
        response = self.app.get(next_page, user=self.user)
        self.assertEqual(response.context.get("cases")[0]["uuid"], self.zaak1["uuid"])

        # check access logs for displayed cases
        logs = list(TimelineLog.objects.all())
        case_log = [
            l for l in logs if self.zaak1["identificatie"] in l.extra_data["message"]
        ]
        self.assertEqual(len(case_log), 1)

        # no logs for non-displayed cases (after we cleared just above)
        for log in logs:
            self.assertNotIn(self.zaak2["identificatie"], log.extra_data["message"])
            self.assertNotIn(self.zaak3["identificatie"], log.extra_data["message"])
