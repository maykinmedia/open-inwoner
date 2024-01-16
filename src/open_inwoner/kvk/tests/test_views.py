from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse, reverse_lazy

from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import eHerkenningUserFactory
from open_inwoner.kvk.branches import KVK_BRANCH_SESSION_VARIABLE, get_kvk_branch_number
from open_inwoner.kvk.tests.factories import CertificateFactory


class KvKViewsTestCase(TestCase):
    url = reverse_lazy("kvk:branches")

    @classmethod
    def setUpTestData(cls):

        super().setUpTestData()

        cls.user = eHerkenningUserFactory.create(
            kvk="12345678", email="user-12345678@organization"
        )

    def test_get_branches_page_without_kvk_throws_401(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_post_branches_page_without_kvk_unauthenticated_throws_401(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_post_branches_page_with_correct_vestigingsnummer(
        self, mock_solo, mock_kvk
    ):
        mock_kvk.return_value = [
            {"kvkNummer": "12345678"},
            {"kvkNummer": "12345678", "vestigingsnummer": "1234"},
        ]

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        self.client.force_login(user=self.user)

        response = self.client.post(self.url, data={"branch_number": "1234"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_kvk_branch_number(self.client.session), "1234")

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_post_branches_page_with_incorrect_vestigingsnummer(
        self, mock_solo, mock_kvk
    ):
        mock_kvk.return_value = [
            {"kvkNummer": "12345678"},
            {"kvkNummer": "12345678", "vestigingsnummer": "1234"},
        ]

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        self.client.force_login(user=self.user)

        response = self.client.post(self.url, data={"branch_number": "4321"})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(KVK_BRANCH_SESSION_VARIABLE, self.client.session)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_get_branches_page_no_branches_found_sets_default_branch_number(
        self, mock_solo, mock_kvk
    ):
        """
        Regression test for endless redirect: https://taiga.maykinmedia.nl/project/open-inwoner/task/2000
        """
        mock_kvk.return_value = []

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("pages-root"))
        # Branch number should be the KVK number, because no branches were found
        self.assertEqual(get_kvk_branch_number(self.client.session), "12345678")

        response = self.client.get(response.url)

        # Following redirect should not result in endless redirect
        self.assertEqual(response.status_code, 200)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_get_branches_page(self, mock_solo, mock_kvk):
        mock_kvk.return_value = [
            {
                "handelsnaam": "Makers and Shakers",
                "kvkNummer": "12345678",
                "vestigingsnummer": "1234",
            },
            {
                "handelsnaam": "Makers and Shakers",
                "kvkNummer": "12345678",
                "vestigingsnummer": "5678",
            },
        ]

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        self.client.force_login(user=self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        doc = PyQuery(response.content)

        branch_inputs = doc.find("[name='branch_number']")

        # check that pseudo-branch representing company as a whole has been added
        self.assertEqual(len(branch_inputs), 3)

        self.assertEqual(branch_inputs[0], doc.find("[id='branch-12345678']")[0])
        self.assertEqual(branch_inputs[1], doc.find("[id='branch-1234']")[0])
        self.assertEqual(branch_inputs[2], doc.find("[id='branch-5678']")[0])
