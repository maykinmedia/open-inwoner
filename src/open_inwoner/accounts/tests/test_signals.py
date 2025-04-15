from unittest.mock import patch

from django.contrib.auth.signals import user_logged_in
from django.test import RequestFactory, TestCase

from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin

from .factories import (
    DigidUserFactory,
    UserFactory,
    eHerkenningUserFactory,
    eHerkenningVestigingUserFactory,
)


class PostLoginSignalEHerkenningUserTestCase(TestCase, AssertTimelineLogMixin):
    def test_update_eherkenning_user_from_kvk_api_is_only_invoked_for_eherkenning_users(
        self,
    ):

        for user, expected_mock_call in (
            (eHerkenningUserFactory(), True),
            (eHerkenningVestigingUserFactory(), True),
            (DigidUserFactory(), False),
            (UserFactory(), False),
        ):
            with self.subTest(f"{user=} {expected_mock_call=}"), patch(
                "open_inwoner.accounts.signals._update_eherkenning_user_from_kvk_api"
            ) as mock_update_eherkenning_user_from_kvk:
                request = request = RequestFactory().get("/")
                request.user = user

                user_logged_in.send(sender=None, request=request, user=user)

                if expected_mock_call:
                    mock_update_eherkenning_user_from_kvk.assert_called_with(user=user)
                else:
                    mock_update_eherkenning_user_from_kvk.assert_not_called()

                self.assertNotIn(
                    "user attributes were updated from KvK API:",
                    self.getTimelineLogDump(),
                )

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.get_vestigingsprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_vestiging_name_updated_from_specific_vestiging_for_vestiging_user(
        self,
        mock_retrieve_rsin_with_kvk,
        mocck_get_vestigingsprofiel,
        mock_get_basisprofiel,
    ):
        mock_get_basisprofiel.return_value = {"naam": "AcmeCorp Ltd"}
        mocck_get_vestigingsprofiel.return_value = {
            "eersteHandelsnaam": "AcmeCorp vestiging"
        }
        user = eHerkenningVestigingUserFactory(rsin="12345")
        request = request = RequestFactory().get("/")
        request.user = user

        user_logged_in.send(sender=None, request=request, user=user)

        self.assertEqual(user.company_name, "AcmeCorp Ltd")
        self.assertEqual(user.branch_name, "AcmeCorp vestiging")
        mock_get_basisprofiel.assert_called_with(kvk=user.kvk)
        mocck_get_vestigingsprofiel.assert_called_with(vestiging=user.vestiging)
        mock_retrieve_rsin_with_kvk.assert_not_called()

        self.assertTimelineLog(
            "user attributes were updated from KvK API: company_name, branch_name"
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.get_vestigingsprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_vestiging_name_not_updated_from_headquarters_for_kvk_user(
        self,
        mock_retrieve_rsin_with_kvk,
        mocck_get_vestigingsprofiel,
        mock_get_basisprofiel,
    ):
        mock_get_basisprofiel.return_value = {
            "naam": "AcmeCorp Ltd",
            "handelsnamen": [{"naam": "AcmeCorp hoofdvestiging", "volgorde": 0}],
        }
        user = eHerkenningUserFactory(rsin="12345")
        request = request = RequestFactory().get("/")
        request.user = user

        user_logged_in.send(sender=None, request=request, user=user)

        self.assertEqual(user.company_name, "AcmeCorp Ltd")
        self.assertEqual(user.branch_name, "")
        mock_get_basisprofiel.assert_called_with(kvk=user.kvk)
        mocck_get_vestigingsprofiel.assert_not_called()
        mock_retrieve_rsin_with_kvk.assert_not_called()

        self.assertTimelineLog(
            "user attributes were updated from KvK API: company_name"
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.get_vestigingsprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_missing_rsin_set_for_kvk_user(
        self,
        mock_retrieve_rsin_with_kvk,
        mocck_get_vestigingsprofiel,
        mock_get_basisprofiel,
    ):
        mock_retrieve_rsin_with_kvk.return_value = "12345"
        mock_get_basisprofiel.return_value = {
            "naam": "AcmeCorp Ltd",
            "handelsnamen": [{"naam": "AcmeCorp hoofdvestiging", "volgorde": 0}],
        }
        user = eHerkenningUserFactory(rsin="", branch_name="AcmeCorp hoofdvestiging")
        request = request = RequestFactory().get("/")
        request.user = user

        user_logged_in.send(sender=None, request=request, user=user)

        self.assertEqual(user.rsin, "12345")
        mocck_get_vestigingsprofiel.assert_not_called()
        mock_get_basisprofiel.assert_called_with(kvk=user.kvk)
        mock_retrieve_rsin_with_kvk.assert_called_with(kvk=user.kvk)

        self.assertTimelineLog(
            "user attributes were updated from KvK API: company_name, rsin"
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.get_vestigingsprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_missing_rsin_set_for_vestiging_user(
        self,
        mock_retrieve_rsin_with_kvk,
        mocck_get_vestigingsprofiel,
        mock_get_basisprofiel,
    ):
        mock_get_basisprofiel.return_value = {}
        mocck_get_vestigingsprofiel.return_value = {}
        mock_retrieve_rsin_with_kvk.return_value = "12345"
        user = eHerkenningVestigingUserFactory(rsin="")
        request = request = RequestFactory().get("/")
        request.user = user

        user_logged_in.send(sender=None, request=request, user=user)

        self.assertEqual(user.rsin, "12345")
        mocck_get_vestigingsprofiel.assert_called_with(vestiging=user.vestiging)
        mock_get_basisprofiel.assert_called_with(kvk=user.kvk)
        mock_retrieve_rsin_with_kvk.assert_called_with(kvk=user.kvk)

        self.assertTimelineLog("user attributes were updated from KvK API: rsin")

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.get_vestigingsprofiel")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_rsin_not_retrieved_if_known(
        self,
        mock_retrieve_rsin_with_kvk,
        mocck_get_vestigingsprofiel,
        mock_get_basisprofiel,
    ):
        mock_get_basisprofiel.return_value = {}
        mocck_get_vestigingsprofiel.return_value = {}
        for user in (
            eHerkenningUserFactory(rsin="12345"),
            eHerkenningVestigingUserFactory(rsin="12345"),
        ):
            with self.subTest(user):
                request = request = RequestFactory().get("/")
                request.user = user

                user_logged_in.send(sender=None, request=request, user=user)

                mock_retrieve_rsin_with_kvk.assert_not_called()

        self.assertNotIn(
            "user attributes were updated from KvK API:", self.getTimelineLogDump()
        )
