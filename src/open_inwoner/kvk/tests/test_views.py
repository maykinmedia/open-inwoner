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

        branch_inputs = doc.find("[name='branch_number']")

        # check that pseudo-branch representing company as a whole has been added
        self.assertEqual(len(branch_inputs), 2)

        self.assertEqual(branch_inputs[0], doc.find("[id='entire-company']")[0])
        self.assertEqual(branch_inputs[1], doc.find("[id='branch-1234']")[0])

        # chack that company name is displayed for every branch
        company_name_displays = doc("h2:Contains('Makers and Shakers')")
        self.assertEqual(len(company_name_displays), 2)

        main_branch_display = doc("p:Contains('Hoofdvestiging')")
        self.assertEqual(len(main_branch_display), 1)

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
