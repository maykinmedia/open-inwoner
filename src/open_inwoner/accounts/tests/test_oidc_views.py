from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from mozilla_django_oidc_db.models import OpenIDConnectConfig

from ..choices import LoginTypeChoices
from .factories import UserFactory

User = get_user_model()


class OIDCFlowTests(TestCase):
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.mixins.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(enabled=True),
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
            callback_response, reverse("root"), fetch_redirect_response=False
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
        return_value=OpenIDConnectConfig(enabled=True),
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
            callback_response, reverse("root"), fetch_redirect_response=False
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
        return_value=OpenIDConnectConfig(enabled=True),
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
            callback_response, reverse("root"), fetch_redirect_response=False
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
        return_value=OpenIDConnectConfig(enabled=True),
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
                callback_response, reverse("root"), fetch_redirect_response=False
            )

            with self.subTest("check error page again"):
                response = self.client.get(error_url)

                self.assertEqual(response.status_code, 403)
