from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

import requests_mock
from django_webtest import WebTest
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.utils.test import paginated_response

from ..models import OpenZaakConfig
from .factories import ServiceFactory

ZAKEN_ROOT = "https://zaken.nl/api/v1/"
CATALOGI_ROOT = "https://catalogi.nl/api/v1/"
DOCUMENTEN_ROOT = "https://documenten.nl/api/v1/"


@requests_mock.Mocker()
class TestListStatusView(WebTest):
    def setUp(self):
        self.user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )
        self.config = OpenZaakConfig.get_solo()
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.config.zaak_service = self.zaak_service
        self.catalogi_service = ServiceFactory(
            api_root=CATALOGI_ROOT, api_type=APITypes.ztc
        )
        self.config.catalogi_service = self.catalogi_service
        self.config.save()
        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
        )
        self.status1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-c8b22b70083c",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71fe4",
            datum_status_gezet="2021-01-12",
            statustoelichting="",
        )
        self.status2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c8b22b60083c",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71",
            datum_status_gezet="2021-03-12",
            statustoelichting="",
        )
        self.status_type1 = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71fe4",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-8ff7e6a73c2c",
            omschrijving="Initial request",
            omschrijving_generiek="",
            statustekst="",
            volgnummer=1,
            is_eindstatus=False,
        )
        self.status_type2 = generate_oas_component(
            "ztc",
            "schemas/StatusType",
            url=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71",
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/53340e34-7581-4b04-884f-8ff7e6a73c2c",
            omschrijving="Second request",
            omschrijving_generiek="",
            statustekst="",
            volgnummer=1,
            is_eindstatus=False,
        )
        self.zaak_informatie_object = generate_oas_component(
            "zrc",
            "schemas/ZaakInformatieObject",
            url=f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
            informatieobject=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            zaak=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            aard_relatie_weergave="Hoort bij, omgekeerd: kent",
            titel="",
            beschrijving="",
            registratiedatum="2021-01-12",
        )

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            json=[self.zaak_informatie_object],
        )
        m.get(
            f"{ZAKEN_ROOT}statussen",
            json=paginated_response([self.status1, self.status2]),
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            json=paginated_response([self.status_type1, self.status_type2]),
        )

    def test_status_is_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )

        statuses = [
            status.url for status in response.context.get("case", {}).get("statuses")
        ]
        status_types = [
            status.statustype.url
            for status in response.context.get("case", {}).get("statuses")
        ]

        self.assertListEqual(
            statuses,
            [
                f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c8b22b60083c",
                f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-c8b22b70083c",
            ],
        )

        self.assertListEqual(
            status_types,
            [
                f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71",
                f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71fe4",
            ],
        )

    def test_current_status_in_context_is_the_most_recent_one(self, m):
        self._setUpMocks(m)

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )
        current_status = response.context.get("case", {}).get("current_status")

        self.assertEquals(
            current_status.url,
            f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c8b22b60083c",
        )

    def test_case_information_objects_are_retrieved_when_user_logged_in_via_digid(
        self, m
    ):
        self._setUpMocks(m)

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )

        self.assertEquals(
            response.context.get("case", {}).get("info", {}).get("count"), 1
        )
        self.assertEquals(
            response.context.get("case", {}).get("info", {}).get("objects")[0].url,
            f"{ZAKEN_ROOT}zaakinformatieobjecten/e55153aa-ad2c-4a07-ae75-15add57d6",
        )

    def test_user_is_redirected_to_root_when_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=user,
        )

        self.assertRedirects(response, reverse("root"))

    def test_anonymous_user_has_no_access_to_status_page(self, m):
        self._setUpMocks(m)
        user = AnonymousUser()
        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=user,
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('accounts:case_status', kwargs={'object_id': 'd8bbdeb7-770f-4ca9-b1ea-77b4730bf67d'})}",
        )

    def test_missing_catalogi_client_returns_statustype_none(self, m):
        self._setUpMocks(m)

        self.config.catalogi_service = None
        self.config.save()

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )

        self.assertIsNone(
            response.context.get("case", {}).get("current_status").statustype
        )

    def test_no_status_is_retrieved_when_http_404(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            status_code=404,
        )
        m.get(
            f"{ZAKEN_ROOT}statussen",
            status_code=404,
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            status_code=404,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )

        self.assertListEqual(response.context.get("case", {}).get("statuses"), [])

    def test_no_status_is_retrieved_when_http_500(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )
        m.get(
            f"{ZAKEN_ROOT}zaakinformatieobjecten?zaak={self.zaak['url']}",
            status_code=500,
        )
        m.get(
            f"{ZAKEN_ROOT}statussen",
            status_code=500,
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen",
            status_code=500,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=self.user,
        )

        self.assertListEqual(response.context.get("case", {}).get("statuses"), [])
