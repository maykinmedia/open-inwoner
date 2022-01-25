import json
import os

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

import requests_mock
from django_webtest import WebTest

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory

from ..cases import fetch_cases
from ..models import OpenZaakConfig
from .factories import ServiceFactory


def load_json_mock(name):
    path = os.path.join(os.path.dirname(__file__), "files", name)
    with open(path, "r") as f:
        return json.loads(f.read())


def load_binary_mock(name):
    path = os.path.join(os.path.dirname(__file__), "files", name)
    with open(path, "rb") as f:
        return f.read()


@requests_mock.Mocker()
class TestFetchingCases(WebTest):
    def _setUp_mocks(self, m):
        m.get(
            "https://zaken/api/v1/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("openapi.yaml"),
        )
        m.get(
            "https://zaken/api/v1/zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
            status_code=200,
            json=load_json_mock("zaken.900222086.json"),
        )

    def setUp(self):
        self.config = OpenZaakConfig.get_solo()
        self.service = ServiceFactory(
            api_root="https://zaken/api/v1/",
            oas="https://zaken/api/v1/schema/openapi.yaml",
        )
        self.config.service = self.service
        self.config.save()

    def test_sorted_cases_are_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUp_mocks(m)

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
                "https: //openzaak.nl/zaken/api/v1/zaken/e4d469b9-6666-4bdd-bf42-b53445298102",
                "https: //openzaak.nl/zaken/api/v1/zaken/d8bbdeb7-770f-4ca9-b1ea-77b4730bf67d",
            ],
        )
        self.assertListEqual(
            closed_cases,
            [
                "https: //openzaak.nl/zaken/api/v1/zaken/6f8de38f-85ea-42d3-978c-845a033335a7"
            ],
        )

    def test_no_cases_are_retrieved_when_user_not_logged_in_via_digid(self, m):
        self._setUp_mocks(m)

        # User's bsn is None when logged in by email (default method)
        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        cases = fetch_cases(user)

        self.assertListEqual(cases, [])

    def test_anonymous_user_has_no_access_to_cases_page(self, m):
        user = AnonymousUser()
        response = self.app.get(reverse("accounts:my_cases"), user=user)

        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('accounts:my_cases')}"
        )

    def test_no_cases_are_retrieved_when_http_404(self, m):
        m.get(
            "https://zaken/api/v1/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("openapi.yaml"),
        )
        m.get(
            "https://zaken/api/v1/zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
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
        m.get(
            "https://zaken/api/v1/schema/openapi.yaml?v=3",
            status_code=200,
            content=load_binary_mock("openapi.yaml"),
        )
        m.get(
            "https://zaken/api/v1/zaken?rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=900222086",
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
