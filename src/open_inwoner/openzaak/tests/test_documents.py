from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

import requests_mock
from django_webtest import WebTest
from zgw_consumers.constants import APITypes
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory

from ...accounts.views.cases import SimpleFile
from ..models import OpenZaakConfig
from .factories import ServiceFactory

CATALOGI_ROOT = "https://catalogi.nl/api/v1/"
DOCUMENTEN_ROOT = "https://documenten.nl/api/v1/"


@requests_mock.Mocker(real_http=False)
class TestDocumentDownloadView(WebTest):
    def setUp(self):
        self.maxDiff = None

    @classmethod
    def setUpTestData(self):
        super().setUpTestData()

        self.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="johm@smith.nl"
        )
        self.config = OpenZaakConfig.get_solo()
        self.document_service = ServiceFactory(
            api_root=DOCUMENTEN_ROOT, api_type=APITypes.drc
        )
        self.config.document_service = self.document_service
        self.config.save()

        self.informatie_object_content = "my document content".encode("utf8")
        self.informatie_object = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            uuid="014c38fe-b010-4412-881c-3000032fb812",
            url=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            inhoud=f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            informatieobjecttype=f"{CATALOGI_ROOT}informatieobjecttype/014c38fe-b010-4412-881c-3000032fb321",
            status="in_bewerking",
            formaat="text/plain",
            bestandsnaam="my_document.txt",
            bestandsomvang=len(self.informatie_object_content),
        )
        self.informatie_object_file = SimpleFile(
            name="my_document.txt",
            size=len(self.informatie_object_content),
            url=reverse(
                "accounts:case_document_download",
                kwargs={
                    "object_id": self.informatie_object["uuid"],
                },
            ),
        )

    def _setUpMocks(self, m):
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            json=self.informatie_object,
        )
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            content=self.informatie_object_content,
        )

    def test_document_content_is_retrieved_when_user_logged_in_via_digid(self, m):
        self._setUpMocks(m)
        response = self.app.get(self.informatie_object_file.url, user=self.user)

        self.assertEqual(response.body, self.informatie_object_content)
        self.assertIn("Content-Disposition", response.headers)
        self.assertEqual(
            response.headers["Content-Disposition"],
            f'attachment; filename="my_document.txt"',
        )
        self.assertIn("Content-Type", response.headers)
        self.assertEqual(response.headers["Content-Type"], "text/plain")
        self.assertIn("Content-Length", response.headers)
        self.assertEqual(
            response.headers["Content-Length"], str(len(self.informatie_object_content))
        )

    def test_user_is_redirected_to_root_when_not_logged_in_via_digid(self, m):
        self._setUpMocks(m)

        user = UserFactory(
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.default,
        )
        response = self.app.get(self.informatie_object_file.url, user=user)

        self.assertRedirects(response, reverse("root"))

    def test_anonymous_user_has_no_access_to_download_page(self, m):
        self._setUpMocks(m)
        user = AnonymousUser()
        response = self.app.get(
            self.informatie_object_file.url,
            user=user,
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={self.informatie_object_file.url}",
        )

    def test_no_data_is_retrieved_when_info_object_http_404(self, m):
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            status_code=404,
        )
        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_info_object_http_500(self, m):
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            status_code=500,
        )
        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_document_download_data_http_404(self, m):
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            json=self.informatie_object,
        )
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            status_code=404,
        )
        self.app.get(self.informatie_object_file.url, user=self.user, status=404)

    def test_no_data_is_retrieved_when_document_download_data_http_500(self, m):
        mock_service_oas_get(m, DOCUMENTEN_ROOT, "drc")
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812",
            json=self.informatie_object,
        )
        m.get(
            f"{DOCUMENTEN_ROOT}enkelvoudiginformatieobjecten/014c38fe-b010-4412-881c-3000032fb812/download",
            status_code=500,
        )
        self.app.get(self.informatie_object_file.url, user=self.user, status=404)
