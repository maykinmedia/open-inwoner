import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse, reverse_lazy

from pyquery import PyQuery

from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext
from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
    eHerkenningVestigingUserFactory,
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

    def test_post_as_non_eherkenning_user_throws_401(self):
        self.client.force_login(DigidUserFactory())
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)

    def test_post_as_branch_restricted_user_throws_401(self):
        self.client.force_login(eHerkenningVestigingUserFactory())

        # Note: we have to persist the session in a separate variable because every
        # property access on self.client insantiates a new session
        session = self.client.session
        session.update(
            {EHerkenningSessionContext.KVK_BRANCH_RESTRICTION_SESSION_KEY: True}
        )
        session.save()

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

        self.client.force_login(
            user=self.user,
            backend=EHerkenningSessionContext._expected_auth_backends()[0],
        )

        vestiging = "1234"
        self.assertEqual(
            User.eherkenning_objects.filter_by_kvk_and_vestiging(
                kvk=self.user.kvk, vestiging=vestiging
            ).count(),
            0,
        )
        response = self.client.post(self.url, data={"branch_number": vestiging})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            EHerkenningSessionContext(
                response.wsgi_request
            ).is_initial_branch_selection_done()
        )

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_post_branches_page_with_empty_or_missing_vestigingsnummer(
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

        vestiging_user = eHerkenningVestigingUserFactory(kvk=self.user.kvk)
        self.client.force_login(
            user=vestiging_user,
            backend=EHerkenningSessionContext._expected_auth_backends()[0],
        )

        for data in ({"branch_number": ""}, None):
            with self.subTest(data):
                response = self.client.post(self.url, data=data)

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.wsgi_request.user,
                    self.user,
                    msg="Empty branch number interpreted as a change to the legal entity user",
                )
                self.assertEqual(response.wsgi_request.user.vestiging, "")
                self.assertTrue(
                    EHerkenningSessionContext(
                        response.wsgi_request
                    ).is_initial_branch_selection_done()
                )

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

        self.client.force_login(
            user=self.user,
            backend=EHerkenningSessionContext._expected_auth_backends()[0],
        )
        response = self.client.post(self.url, data={"branch_number": "4321"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.wsgi_request.user,
            self.user,
            msg="Branch matched existing user, no user change required",
        )

        doc = PyQuery(response.content)

        # Verify JSON data structure embedded in script tag for React component
        # React reads branch data from this JSON rather than parsing DOM elements
        branch_data_script = doc.find("script#branch-data")
        self.assertEqual(len(branch_data_script), 1)

        branch_data = json.loads(branch_data_script.text())
        branch_items = branch_data.get("items", [])

        # Should have 3 items: entire company + 2 branches
        self.assertEqual(len(branch_data["items"]), 3)

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

        self.client.force_login(
            user=self.user,
            backend=EHerkenningSessionContext._expected_auth_backends()[0],
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("pages-root"))
        # Because no branches were found, the branch check should be skipped in the future
        # and no branch number should be set
        self.assertEqual(response.wsgi_request.user, self.user)
        self.assertTrue(
            EHerkenningSessionContext(
                response.wsgi_request
            ).is_initial_branch_selection_done()
        )

        response = self.client.get(response.url)

        # Following redirect should not result in endless redirect
        self.assertEqual(response.status_code, 200)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch(
        "open_inwoner.kvk.models.KvKConfig.get_solo",
    )
    def test_get_branches_page_one_branch_found(self, mock_solo, mock_kvk):
        """
        The branch selection page should be displayed, and the vestigingsnummer stored in the
        session, even if only one branch is found.

        Taiga: https://taiga.maykinmedia.nl/project/open-inwoner/task/2946

        We previously skipped the branch selection for single-branch companies because of problems
        with our redirect middleware: https://taiga.maykinmedia.nl/project/open-inwoner/task/2000
        """
        mock_kvk.return_value = [
            {
                "kvkNummer": "12345678",
                "vestigingsnummer": "1234",
                "naam": "Makers and Shakers",
                "type": "hoofdvestiging",
            },
        ]

        mock_solo.return_value.api_key = "123"
        mock_solo.return_value.api_root = "http://foo.bar/api/v1/"
        mock_solo.return_value.client_certificate = CertificateFactory()
        mock_solo.return_value.server_certificate = CertificateFactory()

        self.client.force_login(
            user=self.user,
            backend=EHerkenningSessionContext._expected_auth_backends()[0],
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        doc = PyQuery(response.content)

        # Verify branch data is properly serialized as JSON for React consumption
        branch_data_script = doc.find("script#branch-data")
        self.assertEqual(len(branch_data_script), 1)

        branch_data = json.loads(branch_data_script.text())
        branch_items = branch_data.get("items", [])

        # Should have 2 items: entire company + 1 branch
        self.assertEqual(len(branch_data["items"]), 2)

        # Verify the structure - first should be entire company, second should be the branch
        self.assertEqual(branch_items[0]["id"], "rechtspersoon")
        self.assertEqual(branch_items[1]["id"], "1234")

        # Verify company name appears in both entries
        self.assertEqual(branch_items[0]["label"], "Makers and Shakers")
        self.assertEqual(branch_items[1]["label"], "Makers and Shakers")

        # Verify the entire company has rechtspersoon indicator
        self.assertEqual(
            branch_items[0]["rechtspersoonInfo"],
            "Selecteer de rechtspersoon (geen vestiging)",
        )

        # Verify the branch has vestiging info with hoofdvestiging indicator
        self.assertIn("Hoofdvestiging", branch_items[1]["vestigingInfo"])
        self.assertIn("1234", branch_items[1]["vestigingInfo"])

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

        self.client.force_login(
            user=self.user,
            backend=EHerkenningSessionContext._expected_auth_backends()[0],
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        doc = PyQuery(response.content)

        # Check for React component data instead of DOM inputs
        branch_data_script = doc.find("script#branch-data")
        self.assertEqual(len(branch_data_script), 1)

        branch_data = json.loads(branch_data_script.text())
        branch_items = branch_data.get("items", [])

        # Should have 3 items: entire company + 2 branches
        self.assertEqual(len(branch_data["items"]), 3)

        # Verify the structure
        self.assertEqual(branch_items[0]["id"], "rechtspersoon")
        self.assertEqual(branch_items[1]["id"], "1234")  # hoofdvestiging
        self.assertEqual(branch_items[2]["id"], "5678")  # nevenvestiging

        # Verify company name appears in all entries
        for item in branch_items:
            self.assertEqual(item["label"], "Makers and Shakers")

        # Verify the entire company has rechtspersoon indicator
        self.assertEqual(
            branch_items[0]["rechtspersoonInfo"],
            "Selecteer de rechtspersoon (geen vestiging)",
        )

        # Verify the main branch has hoofdvestiging indicator in vestigingInfo
        self.assertIn("Hoofdvestiging", branch_items[1]["vestigingInfo"])
        self.assertIn("1234", branch_items[1]["vestigingInfo"])

        # Verify the second branch has vestiging number but no hoofdvestiging indicator
        self.assertIn("5678", branch_items[2]["vestigingInfo"])
        self.assertNotIn("Hoofdvestiging", branch_items[2]["vestigingInfo"])
