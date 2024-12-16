from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse, reverse_lazy

from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import eHerkenningUserFactory
from open_inwoner.kvk.branches import (
    KVK_BRANCH_SESSION_VARIABLE,
    get_kvk_branch_number,
    kvk_branch_selected_done,
)
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
    @patch("open_inwoner.kvk.client.KvKClient.get_vestiging")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_post_branches_page_with_correct_vestigingsnummer(
        self, mock_solo, mock_vestiging, mock_kvk
    ):
        mock_kvk_value = {
            "kvkNummer": "12345678",
            "naam": "Test BV Donald",
            "adres": {
                "binnenlandsAdres": {
                    "plaats": "Lollum",
                    "postcode": "1234",
                    "straatnaam": "Fantasielaan",
                }
            },
        }
        mock_kvk_value_vestiging = {
            "kvkNummer": "12345678",
            "vestigingsnummer": "1234",
            "naam": "Test BV Donald Nevenvestiging",
            "adres": {
                "binnenlandsAdres": {
                    "plaats": "Lollum Dollum",
                    "postcode": "4321",
                    "straatnaam": "Hizzaarderlaan",
                }
            },
        }
        mock_kvk.return_value = [mock_kvk_value, mock_kvk_value_vestiging]
        mock_vestiging.return_value = mock_kvk_value_vestiging

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        self.client.force_login(user=self.user)

        response = self.client.post(self.url, data={"branch_number": "1234"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(kvk_branch_selected_done(self.client.session), True)
        self.assertEqual(get_kvk_branch_number(self.client.session), "1234")

        # check result of company_branch_selected signal
        self.user.refresh_from_db()
        self.assertEqual(self.user.company_name, "Test BV Donald Nevenvestiging")
        self.assertEqual(self.user.city, "Lollum Dollum")
        self.assertEqual(self.user.postcode, "4321")
        self.assertEqual(self.user.street, "Hizzaarderlaan")

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch("open_inwoner.kvk.client.KvKClient.get_vestiging")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_post_branches_page_with_empty_vestigingsnummer(
        self, mock_solo, mock_get_vestiging, mock_kvk
    ):
        mock_kvk_value = {
            "kvkNummer": "12345678",
            "naam": "Test BV Donald",
            "adres": {
                "binnenlandsAdres": {
                    "plaats": "Lollum",
                    "postcode": "1234",
                    "straatnaam": "Fantasielaan",
                }
            },
        }
        mock_kvk_value_vestiging = {
            "kvkNummer": "12345678",
            "vestigingsnummer": "1234",
            "naam": "Test BV Donald Nevenvestiging",
            "adres": {
                "binnenlandsAdres": {
                    "plaats": "Lollum Dollum",
                    "postcode": "4321",
                    "straatnaam": "Hizzaarderlaan",
                }
            },
        }
        mock_kvk.return_value = [mock_kvk_value, mock_kvk_value_vestiging]
        mock_get_vestiging.return_value = mock_kvk_value_vestiging

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        self.client.force_login(user=self.user)

        response = self.client.post(self.url, data={"branch_number": ""})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(kvk_branch_selected_done(self.client.session), True)
        self.assertEqual(get_kvk_branch_number(self.client.session), "")

        # check result of company_branch_selected signal (should only get name)
        self.user.refresh_from_db()
        self.assertEqual(self.user.company_name, "Test BV Donald Nevenvestiging")
        self.assertEqual(self.user.city, "Lollum Dollum")
        self.assertEqual(self.user.postcode, "4321")
        self.assertEqual(self.user.street, "Hizzaarderlaan")

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
        self.assertEqual(kvk_branch_selected_done(self.client.session), False)
        self.assertNotIn(KVK_BRANCH_SESSION_VARIABLE, self.client.session)

        doc = PyQuery(response.content)
        branch_inputs = doc.find("[name='branch_number']")

        # check that pseudo-branch representing company as a whole has been added
        self.assertEqual(len(branch_inputs), 3)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_get_branches_page_no_branches_found_sets_branch_check_done(
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
        # Because no branches were found, the branch check should be skipped in the future
        # and no branch number should be set
        self.assertEqual(kvk_branch_selected_done(self.client.session), True)
        self.assertEqual(get_kvk_branch_number(self.client.session), None)

        response = self.client.get(response.url)

        # Following redirect should not result in endless redirect
        self.assertEqual(response.status_code, 200)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_get_branches_page_one_branch_found_sets_branch_check_done(
        self, mock_solo, mock_kvk
    ):
        """
        Regression test for endless redirect: https://taiga.maykinmedia.nl/project/open-inwoner/task/2000
        """
        mock_kvk.return_value = [
            {"kvkNummer": "12345678", "vestigingsnummer": "1234"},
        ]

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        self.client.force_login(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("pages-root"))
        # Because no branches were found, the branch check should be skipped in the future
        # and no branch number should be set
        self.assertEqual(kvk_branch_selected_done(self.client.session), True)
        self.assertEqual(get_kvk_branch_number(self.client.session), None)

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
                "naam": "Makers and Shakers",
                "kvkNummer": "12345678",
                "vestigingsnummer": "1234",
                "type": "hoofdvestiging",
            },
            {
                "naam": "Makers and Shakers",
                "kvkNummer": "12345678",
                "vestigingsnummer": "5678",
                "type": "nevenvestiging",
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

        self.assertEqual(branch_inputs[0], doc.find("[id='entire-company']")[0])
        self.assertEqual(branch_inputs[1], doc.find("[id='branch-1234']")[0])
        self.assertEqual(branch_inputs[2], doc.find("[id='branch-5678']")[0])

        # chack that company name is displayed for every branch
        company_name_displays = doc("h2:Contains('Makers and Shakers')")
        self.assertEqual(len(company_name_displays), 3)

        main_branch_display = doc("p:Contains('Hoofdvestiging')")
        self.assertEqual(len(main_branch_display), 1)
