from hashlib import md5
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, modify_settings, override_settings
from django.urls import reverse

import requests_mock
from furl import furl
from mozilla_django_oidc_db.models import OpenIDConnectConfig

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)

from ..choices import LoginTypeChoices
from .factories import DigidUserFactory, UserFactory, eHerkenningUserFactory

User = get_user_model()


class OIDCFlowTests(TestCase):
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.mixins.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True),
    )
    def test_existing_email_updates_user(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        # set up a user with a colliding email address
        # sub is the oidc_id field in our db
        mock_get_userinfo.return_value = {
            "email": "existing_user@example.com",
            "sub": "some_username",
        }
        user = UserFactory.create(email="existing_user@example.com")
        self.assertEqual(user.oidc_id, "")
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        user.refresh_from_db()

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=False
        )
        self.assertTrue(User.objects.filter(oidc_id="some_username").exists())
        self.assertEqual(user.oidc_id, "some_username")

        db_user = User.objects.filter(oidc_id="some_username").first()

        self.assertEqual(db_user.id, user.id)
        self.assertEqual(db_user.login_type, LoginTypeChoices.oidc)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.mixins.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True),
    )
    def test_existing_case_sensitive_email_updates_user(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        # set up a user with a colliding email address
        # sub is the oidc_id field in our db
        mock_get_userinfo.return_value = {
            "email": "Existing_user@example.com",
            "sub": "some_username",
        }
        user = UserFactory.create(
            email="existing_user@example.com", login_type=LoginTypeChoices.default
        )
        self.assertEqual(user.oidc_id, "")
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        user.refresh_from_db()

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=False
        )
        self.assertTrue(User.objects.filter(oidc_id="some_username").exists())
        self.assertEqual(user.oidc_id, "some_username")

        db_user = User.objects.filter(oidc_id="some_username").first()

        self.assertEqual(db_user.id, user.id)
        self.assertEqual(db_user.login_type, LoginTypeChoices.oidc)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.mixins.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True),
    )
    def test_new_user_is_created_when_new_email(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {
            "email": "new_user@example.com",
            "sub": "some_username",
        }
        UserFactory.create(email="existing_user@example.com")
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=False
        )
        new_user = User.objects.filter(email="new_user@example.com")

        self.assertTrue(new_user.exists())
        self.assertEqual(new_user.get().oidc_id, "some_username")
        self.assertEqual(new_user.get().login_type, LoginTypeChoices.oidc)

    def test_error_page_direct_access_forbidden(self):
        error_url = reverse("admin-oidc-error")

        response = self.client.get(error_url)

        self.assertEqual(response.status_code, 403)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.mixins.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True),
    )
    def test_error_first_cleared_after_succesful_login(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "email": "nocollision@example.com",
            "sub": "some_username",
        }
        session = self.client.session
        session["oidc-error"] = "some error"
        session.save()
        error_url = reverse("admin-oidc-error")

        with self.subTest("with error"):
            response = self.client.get(error_url)

            self.assertEqual(response.status_code, 200)

        with self.subTest("after succesful login"):
            session["oidc_states"] = {"mock": {"nonce": "nonce"}}
            session.save()
            callback_url = reverse("oidc_authentication_callback")

            # enter the login flow
            callback_response = self.client.get(
                callback_url, {"code": "mock", "state": "mock"}
            )

            self.assertRedirects(
                callback_response, reverse("pages-root"), fetch_redirect_response=False
            )

            with self.subTest("check error page again"):
                response = self.client.get(error_url)

                self.assertEqual(response.status_code, 403)


class DigiDOIDCFlowTests(TestCase):
    @patch("open_inwoner.haalcentraal.signals.update_brp_data_in_db")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(id=1, enabled=True),
    )
    def test_existing_bsn_creates_no_new_user(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_brp,
    ):
        # set up a user with a colliding email address
        # sub is the oidc_id field in our db
        mock_get_userinfo.return_value = {
            "email": "existing_user@example.com",
            "sub": "some_username",
            "bsn": "123456782",
        }
        user = DigidUserFactory.create(
            first_name="John",
            last_name="Doe",
            bsn="123456782",
            email="user-123456782@localhost",
            is_prepopulated=True,
        )
        self.assertEqual(user.oidc_id, "")
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("digid_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        user.refresh_from_db()

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=False
        )
        self.assertEqual(User.objects.count(), 1)

        db_user = User.objects.get()

        # User data was prepopulated, so this should not be called
        mock_brp.assert_not_called()
        self.assertEqual(db_user.id, user.id)
        self.assertEqual(db_user.bsn, "123456782")
        self.assertEqual(db_user.login_type, LoginTypeChoices.digid)
        self.assertEqual(db_user.first_name, "John")
        self.assertEqual(db_user.last_name, "Doe")

    @patch("open_inwoner.haalcentraal.signals.update_brp_data_in_db")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(id=1, enabled=True),
    )
    def test_new_user_is_created_when_new_bsn(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_brp,
    ):
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {"sub": "some_username", "bsn": "000000000"}
        DigidUserFactory.create(bsn="123456782", email="existing_user@example.com")
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("digid_oidc:callback")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=False
        )
        new_user = User.objects.get(bsn="000000000")

        mock_brp.assert_called_with(new_user)
        salt = "generate_email_from_bsn"
        hashed_bsn = md5(
            (salt + "000000000").encode(), usedforsecurity=False
        ).hexdigest()
        self.assertEqual(new_user.email, f"{hashed_bsn}@localhost")
        self.assertEqual(new_user.login_type, LoginTypeChoices.digid)

    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(
            id=1, enabled=True, oidc_op_logout_endpoint="http://localhost:8080/logout"
        ),
    )
    def test_logout(self, mock_get_solo):
        # set up a user with a non existing email address
        user = DigidUserFactory.create(
            bsn="123456782", email="existing_user@example.com"
        )
        self.client.force_login(user)
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session["oidc_id_token"] = "foo"
        session.save()
        logout_url = reverse("digid_oidc:logout")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the logout flow
        with requests_mock.Mocker() as m:
            logout_endpoint_url = str(
                furl("http://localhost:8080/logout").set(
                    {
                        "id_token_hint": "foo",
                    }
                )
            )
            m.get(logout_endpoint_url)
            logout_response = self.client.get(logout_url)

            self.assertEqual(len(m.request_history), 1)
            self.assertEqual(m.request_history[0].url, logout_endpoint_url)

        self.assertRedirects(
            logout_response, reverse("login"), fetch_redirect_response=False
        )

        self.assertNotIn("oidc_states", self.client.session)
        self.assertNotIn("oidc_id_token", self.client.session)

    def test_error_page_direct_access_forbidden(self):
        error_url = reverse("oidc-error")

        response = self.client.get(error_url)

        self.assertEqual(response.status_code, 403)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(id=1, enabled=True),
    )
    def test_error_first_cleared_after_succesful_login(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "bsn": "123456782",
        }
        session = self.client.session
        session["oidc-error"] = "some error"
        session.save()
        error_url = reverse("admin-oidc-error")

        with self.subTest("with error"):
            response = self.client.get(error_url)

            self.assertEqual(response.status_code, 200)

        with self.subTest("after succesful login"):
            session["oidc_states"] = {"mock": {"nonce": "nonce"}}
            session.save()
            callback_url = reverse("digid_oidc:callback")

            # enter the login flow
            callback_response = self.client.get(
                callback_url, {"code": "mock", "state": "mock"}
            )

            self.assertRedirects(
                callback_response, reverse("pages-root"), fetch_redirect_response=False
            )

            with self.subTest("check error page again"):
                response = self.client.get(error_url)

                self.assertEqual(response.status_code, 403)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class eHerkenningOIDCFlowTests(TestCase):
    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch("open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(id=1, enabled=True),
    )
    def test_existing_kvk_creates_no_new_user(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_retrieve_rsin_with_kvk,
        mock_kvk,
    ):
        mock_kvk.return_value = [
            {"vestigingsnummer": "1234"},
        ]

        mock_retrieve_rsin_with_kvk.return_value = "123456789"
        # set up a user with a colliding email address
        # sub is the oidc_id field in our db
        mock_get_userinfo.return_value = {
            "email": "existing_user@example.com",
            "sub": "some_username",
            "kvk": "12345678",
        }
        user = eHerkenningUserFactory.create(
            first_name="John",
            last_name="Doe",
            kvk="12345678",
            email="user-12345678@localhost",
            is_prepopulated=True,
        )
        self.assertEqual(user.oidc_id, "")
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("eherkenning_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        user.refresh_from_db()

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=False
        )
        self.assertEqual(User.objects.count(), 1)

        db_user = User.objects.get()

        # User data was prepopulated, so this should not be called
        mock_retrieve_rsin_with_kvk.assert_not_called()
        self.assertEqual(db_user.id, user.id)
        self.assertEqual(db_user.kvk, "12345678")
        self.assertEqual(db_user.login_type, LoginTypeChoices.eherkenning)
        self.assertEqual(db_user.first_name, "John")
        self.assertEqual(db_user.last_name, "Doe")

    @patch("open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(id=1, enabled=True),
    )
    def test_new_user_is_created_when_new_kvk(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_retrieve_rsin_with_kvk,
    ):
        mock_retrieve_rsin_with_kvk.return_value = "123456789"
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {"sub": "some_username", "kvk": "00000000"}
        eHerkenningUserFactory.create(kvk="12345678", email="existing_user@example.com")
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("eherkenning_oidc:callback")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=False
        )
        new_user = User.objects.get(kvk="00000000")

        mock_retrieve_rsin_with_kvk.assert_called_with("00000000")
        salt = "generate_email_from_bsn"
        hashed_bsn = md5(
            (salt + "00000000").encode(), usedforsecurity=False
        ).hexdigest()
        self.assertEqual(new_user.email, f"{hashed_bsn}@localhost")
        self.assertEqual(new_user.rsin, "123456789")
        self.assertEqual(new_user.login_type, LoginTypeChoices.eherkenning)

    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(
            id=1, enabled=True, oidc_op_logout_endpoint="http://localhost:8080/logout"
        ),
    )
    def test_logout(self, mock_get_solo):
        # set up a user with a non existing email address
        user = eHerkenningUserFactory.create(
            kvk="12345678", email="existing_user@example.com"
        )
        self.client.force_login(user)
        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session["oidc_id_token"] = "foo"
        session["KVK_BRANCH_NUMBER"] = "1234"
        session.save()
        logout_url = reverse("eherkenning_oidc:logout")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the logout flow
        with requests_mock.Mocker() as m:
            logout_endpoint_url = str(
                furl("http://localhost:8080/logout").set(
                    {
                        "id_token_hint": "foo",
                    }
                )
            )
            m.get(logout_endpoint_url)
            logout_response = self.client.get(logout_url, follow=False)

            self.assertEqual(len(m.request_history), 1)
            self.assertEqual(m.request_history[0].url, logout_endpoint_url)

        self.assertRedirects(
            logout_response, reverse("login"), fetch_redirect_response=False
        )

        self.assertNotIn("oidc_states", self.client.session)
        self.assertNotIn("oidc_id_token", self.client.session)

    @modify_settings(
        MIDDLEWARE={"remove": ["open_inwoner.kvk.middleware.KvKLoginMiddleware"]}
    )
    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(id=1, enabled=True),
    )
    def test_error_first_cleared_after_succesful_login(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_kvk,
    ):
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }
        mock_kvk.return_value = [{"vestigingsnummber": "1234"}]

        session = self.client.session
        session["oidc-error"] = "some error"
        session.save()
        error_url = reverse("admin-oidc-error")

        with self.subTest("with error"):
            response = self.client.get(error_url)

            self.assertEqual(response.status_code, 200)

        with self.subTest("after succesful login"):
            session["oidc_states"] = {"mock": {"nonce": "nonce"}}
            session.save()
            callback_url = reverse("eherkenning_oidc:callback")

            # enter the login flow
            callback_response = self.client.get(
                callback_url, {"code": "mock", "state": "mock"}
            )

            self.assertRedirects(
                callback_response, reverse("pages-root"), fetch_redirect_response=False
            )

            with self.subTest("check error page again"):
                response = self.client.get(error_url)

                self.assertEqual(response.status_code, 403)
