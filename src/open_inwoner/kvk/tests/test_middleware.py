from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from open_inwoner.accounts.tests.factories import eHerkenningUserFactory
from open_inwoner.kvk.tests.factories import CertificateFactory


class KvKLoginMiddlewareTestCase(TestCase):
    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_middleware_skip_redirect_for_media_files(self, mock_solo, mock_kvk):
        mock_kvk.return_value = [
            {"kvkNummer": "12345678"},
            {"kvkNummer": "12345678", "vestigingsnummer": "1234"},
        ]

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        user = eHerkenningUserFactory.create()

        self.client.force_login(user=user)

        response = self.client.get(f"{settings.MEDIA_URL}filer_public/some_image.png/")

        self.assertEqual(response.status_code, 404)
