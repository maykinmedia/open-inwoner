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

    @patch("open_inwoner.accounts.signals.KvKClient.get_vestiging")
    @patch("open_inwoner.accounts.signals.KvKClient.get_company_headquarters")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_vestiging_name_updated_from_specific_vestiging_for_vestiging_user(
        self,
        mock_retrieve_rsin_with_kvk,
        mock_get_company_headquarters,
        mock_get_vestiging,
    ):
        mock_get_vestiging.return_value = {"naam": "AcmeCorp Ltd"}
        user = eHerkenningVestigingUserFactory(rsin="12345")
        request = request = RequestFactory().get("/")
        request.user = user

        user_logged_in.send(sender=None, request=request, user=user)

        self.assertEqual(user.company_name, "AcmeCorp Ltd")
        mock_get_vestiging.assert_called_with(vestiging=user.vestiging)
        mock_get_company_headquarters.assert_not_called()
        mock_retrieve_rsin_with_kvk.assert_not_called()

        self.assertTimelineLog(
            "user attributes were updated from KvK API: company_name"
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_vestiging")
    @patch("open_inwoner.accounts.signals.KvKClient.get_company_headquarters")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_vestiging_name_not_updated_if_no_diff_with_kvk_result(
        self,
        mock_retrieve_rsin_with_kvk,
        mock_get_company_headquarters,
        mock_get_vestiging,
    ):
        mock_get_vestiging.return_value = {"naam": "AcmeCorp Ltd"}
        user = eHerkenningVestigingUserFactory(
            rsin="12345", company_name="AcmeCorp Ltd"
        )
        request = request = RequestFactory().get("/")
        request.user = user

        with patch("open_inwoner.accounts.signals.User.save") as mock_user_model_save:
            user_logged_in.send(sender=None, request=request, user=user)

        # user.save() should not be called for company_name update, only for last_login
        # which is set by Django.
        mock_user_model_save.assert_called_once_with(
            update_fields=["last_login"],
        )
        self.assertEqual(user.company_name, "AcmeCorp Ltd")
        mock_get_vestiging.assert_called_with(vestiging=user.vestiging)
        mock_get_company_headquarters.assert_not_called()
        mock_retrieve_rsin_with_kvk.assert_not_called()

        self.assertNotIn(
            "user attributes were updated from KvK API",
            self.getTimelineLogDump(),
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_vestiging")
    @patch("open_inwoner.accounts.signals.KvKClient.get_company_headquarters")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_vestiging_name_updated_from_headquarters_for_kvk_user(
        self,
        mock_retrieve_rsin_with_kvk,
        mock_get_company_headquarters,
        mock_get_vestiging,
    ):
        mock_get_company_headquarters.return_value = {"naam": "AcmeCorp Ltd"}
        user = eHerkenningUserFactory(rsin="12345")
        request = request = RequestFactory().get("/")
        request.user = user

        user_logged_in.send(sender=None, request=request, user=user)

        self.assertEqual(user.company_name, "AcmeCorp Ltd")
        mock_get_vestiging.assert_not_called()
        mock_get_company_headquarters.assert_called_with(kvk=user.kvk)
        mock_retrieve_rsin_with_kvk.assert_not_called()

        self.assertTimelineLog(
            "user attributes were updated from KvK API: company_name"
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_vestiging")
    @patch("open_inwoner.accounts.signals.KvKClient.get_company_headquarters")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_missing_rsin_set_for_kvk_user(
        self,
        mock_retrieve_rsin_with_kvk,
        mock_get_company_headquarters,
        mock_get_vestiging,
    ):
        mock_retrieve_rsin_with_kvk.return_value = "12345"
        mock_get_company_headquarters.return_value = {"naam": "AcmeCorp Ltd"}
        user = eHerkenningUserFactory(rsin="")
        request = request = RequestFactory().get("/")
        request.user = user

        user_logged_in.send(sender=None, request=request, user=user)

        self.assertEqual(user.rsin, "12345")
        mock_get_vestiging.assert_not_called()
        mock_get_company_headquarters.assert_called_with(kvk=user.kvk)
        mock_retrieve_rsin_with_kvk.assert_called_with(user.kvk)

        self.assertTimelineLog(
            "user attributes were updated from KvK API: company_name, rsin"
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_vestiging")
    @patch("open_inwoner.accounts.signals.KvKClient.get_company_headquarters")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_missing_rsin_set_for_vestiging_user(
        self,
        mock_retrieve_rsin_with_kvk,
        mock_get_company_headquarters,
        mock_get_vestiging,
    ):
        mock_retrieve_rsin_with_kvk.return_value = "12345"
        mock_get_vestiging.return_value = {"naam": "AcmeCorp Ltd"}
        user = eHerkenningVestigingUserFactory(rsin="")
        request = request = RequestFactory().get("/")
        request.user = user

        user_logged_in.send(sender=None, request=request, user=user)

        self.assertEqual(user.rsin, "12345")
        mock_get_vestiging.assert_called_with(vestiging=user.vestiging)
        mock_get_company_headquarters.assert_not_called()
        mock_retrieve_rsin_with_kvk.assert_called_with(user.kvk)

        self.assertTimelineLog(
            "user attributes were updated from KvK API: company_name, rsin"
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_vestiging")
    @patch("open_inwoner.accounts.signals.KvKClient.get_company_headquarters")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    def test_rsin_not_retrieved_if_known(
        self,
        mock_retrieve_rsin_with_kvk,
        mock_get_company_headquarters,
        mock_get_vestiging,
    ):
        mock_get_company_headquarters.return_value = {}
        mock_get_vestiging.return_value = {}
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
