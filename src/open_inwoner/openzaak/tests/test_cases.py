from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

import requests_mock
from django_webtest import WebTest
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.cases import fetch_specific_case
from open_inwoner.utils.test import paginated_response

from ..models import OpenZaakConfig
from .factories import ServiceFactory

ZAKEN_ROOT = "https://zaken.nl/api/v1/"
CATALOGI_ROOT = "https://catalogi.nl/api/v1/"


@requests_mock.Mocker()
class TestListCasesView(WebTest):
    def setUp(self):
        self.config = OpenZaakConfig.get_solo()
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.config.zaak_service = self.zaak_service
        self.config.save()

        self.zaak1 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
        )
        self.zaak2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            identificatie="ZAAK-2022-0008800024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-12",
            einddatum=None,
        )
        self.zaak3 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/6f8de38f-85ea-42d3-978c-845a033335a7",
            identificatie="ZAAK-2022-0001000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2021-07-26",
            einddatum="2022-01-16",
        )

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            json=paginated_response([self.zaak1, self.zaak2, self.zaak3]),
        )

        self.zaak1 = generate_oas_component(
            "openapi",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            identificatie="ZAAK-2022-0000000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-02",
            einddatum=None,
        )
        self.zaak2 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
            identificatie="ZAAK-2022-0008800024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2022-01-12",
            einddatum=None,
        )
        self.zaak3 = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/6f8de38f-85ea-42d3-978c-845a033335a7",
            identificatie="ZAAK-2022-0001000024",
            omschrijving="Zaak naar aanleiding van ingezonden formulier",
            startdatum="2021-07-26",
            einddatum="2022-01-16",
        )

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            json=paginated_response([self.zaak1, self.zaak2, self.zaak3]),
        )

    def test_sorted_cases_are_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )
        response = self.app.get(reverse("accounts:my_cases"), user=user)
        open_cases = [case.url for case in response.context.get("open_cases")]
        closed_cases = [case.url for case in response.context.get("closed_cases")]

        self.assertListEqual(
            open_cases,
            [
                f"{ZAKEN_ROOT}zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
                f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            ],
        )
        self.assertListEqual(
            closed_cases,
            [f"{ZAKEN_ROOT}zaken/6f8de38f-85ea-42d3-978c-845a033335a7"],
        )

    def test_no_cases_are_retrieved_when_user_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        # User's bsn is None when logged in by email (default method)
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        response = self.app.get(reverse("accounts:my_cases"), user=user)

        self.assertListEqual(response.context.get("open_cases"), [])
        self.assertListEqual(response.context.get("closed_cases"), [])

    def test_anonymous_user_has_no_access_to_cases_page(self, m):
        user = AnonymousUser()
        response = self.app.get(reverse("accounts:my_cases"), user=user)

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('accounts:my_cases')}"
        )

    def test_no_cases_are_retrieved_when_http_404(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            status_code=404,
        )

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )
        response = self.app.get(reverse("accounts:my_cases"), user=user)

        self.assertEquals(response.status_code, 200)
        self.assertListEqual(response.context.get("open_cases"), [])
        self.assertListEqual(response.context.get("closed_cases"), [])

    def test_no_cases_are_retrieved_when_http_500(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            status_code=500,
        )

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )
        response = self.app.get(reverse("accounts:my_cases"), user=user)

        self.assertEquals(response.status_code, 200)
        self.assertListEqual(response.context.get("open_cases"), [])
        self.assertListEqual(response.context.get("closed_cases"), [])


@requests_mock.Mocker()
class TestFetchSpecificCase(WebTest):
    def setUp(self):
        self.config = OpenZaakConfig.get_solo()
        self.zaak_service = ServiceFactory(api_root=ZAKEN_ROOT, api_type=APITypes.zrc)
        self.config.zaak_service = self.zaak_service
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

    def _setUpMocks(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            json=self.zaak,
        )

    def test_specific_case_is_retrieved_when_user_is_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )

        case = fetch_specific_case(user, "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertEquals(str(case.uuid), "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

    def test_specific_case_is_not_retrieved_when_user_is_not_logged_in_via_digid(
        self, m
    ):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )

        case = fetch_specific_case(user, "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertIsNone(case)

    def test_no_case_is_retrieved_when_http_404(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            status_code=404,
        )

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )
        case = fetch_specific_case(user, "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertIsNone(case)

    def test_no_case_is_retrieved_when_http_500(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{ZAKEN_ROOT}zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            status_code=500,
        )

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
            bsn="900222086",
        )
        case = fetch_specific_case(user, "d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d")

        self.assertIsNone(case)
