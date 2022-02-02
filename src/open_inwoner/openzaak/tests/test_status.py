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


@requests_mock.Mocker()
class TestListStatusView(WebTest):
    def setUp(self):
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
            zaak=f"{ZAKEN_ROOT}zaken/d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d",
            statustype=f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71fe4",
            datum_status_gezet="2021-01-12",
            statustoelichting="",
        )
        self.status2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c8b22b60083c",
            zaak=f"{ZAKEN_ROOT}zaken/d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d",
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

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )
        m.get(
            f"{ZAKEN_ROOT}statussen",
            json=paginated_response([self.status1, self.status2]),
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71fe4",
            json=self.status_type1,
        )
        m.get(
            f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71",
            json=self.status_type2,
        )

    def test_status_is_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=user,
        )

        status_list = [status.url for status in response.context.get("status_list")]
        status_type_list = [
            status_type.url for status_type in response.context.get("status_type_list")
        ]

        self.assertListEqual(
            status_list,
            [
                f"{ZAKEN_ROOT}statussen/3da89990-c7fc-476a-ad13-c8b22b60083c",
                f"{ZAKEN_ROOT}statussen/3da81560-c7fc-476a-ad13-c8b22b70083c",
            ],
        )
        self.assertListEqual(
            status_type_list,
            [
                f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71fe4",
                f"{CATALOGI_ROOT}statustypen/e3798107-ab27-4c3c-977d-7afb71e71",
            ],
        )

    def test_status_is_not_retrieved_when_user_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )

        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=user,
        )

        self.assertIsNone(response.context.get("status_list"))

    def test_anonymous_user_has_no_access_to_status_page(self, m):
        user = AnonymousUser()
        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=user,
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('accounts:case_status', kwargs={'object_id': 'd3bbdeb7-460f-4ca9-b1ea-77b4730bf67d'})}",
        )

    def test_no_status_is_retrieved_when_http_404(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )
        m.get(
            f"{ZAKEN_ROOT}statussen",
            status_code=404,
        )

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )
        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=user,
        )

        self.assertListEqual(response.context["status_list"], [])

    def test_no_status_is_retrieved_when_http_500(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )
        m.get(
            f"{ZAKEN_ROOT}statussen",
            status_code=500,
        )

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )
        response = self.app.get(
            reverse(
                "accounts:case_status",
                kwargs={"object_id": "d3bbdeb7-460f-4ca9-b1ea-77b4730bf67d"},
            ),
            user=user,
        )

        self.assertListEqual(response.context["status_list"], [])
