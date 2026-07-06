from hashlib import md5
from typing import Literal
from unittest import skip
from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, modify_settings, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import requests
import requests_mock
from django_webtest import DjangoTestApp, DjangoWebtestResponse, WebTest
from furl import furl
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.tests.mixins import OIDCMixin
from pyquery import PyQuery

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.eherkenning_session import EHerkenningSessionContext
from open_inwoner.accounts.oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
)
from open_inwoner.accounts.views.auth_oidc import (
    GENERIC_DIGID_ERROR_MSG,
    GENERIC_EHERKENNING_ERROR_MSG,
)
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.choices import OpenIDDisplayChoices
from open_inwoner.configurations.models import SiteConfiguration

from .factories import (
    DigidUserFactory,
    UserFactory,
    eHerkenningUserFactory,
    eHerkenningVestigingUserFactory,
)
from .oidc_factories import OIDCClientFactory

User = get_user_model()


def perform_oidc_login(
    app: DjangoTestApp,
    login_type: Literal["digid", "eherkenning"],
    redirect_url: str = None,
) -> DjangoWebtestResponse:
    """
    Perform the full OIDC login flow for DigiD or eHerkenning
    """
    login_url = furl(reverse("login"))
    if redirect_url:
        login_url.set({"next": redirect_url})

    login_response = app.get(login_url)

    doc = PyQuery(login_response.content)
    login_link = doc.find(f".link--{login_type}")
    init_url = login_link.attr("href")

    init_response = app.get(init_url)

    # Should redirect to identity provider
    assert init_response.status_code == 302

    callback_url = reverse(f"{login_type}_oidc:callback")

    with requests_mock.Mocker() as m:
        callback_url = (
            furl(f"http://testserver{callback_url}")
            .set(
                {
                    "state": list(app.session["oidc_states"].keys())[0],
                    "code": "mock",
                }
            )
            .url
        )
        # Posting to the identity provider endpoint should redirect us to the callback
        m.post(init_response.url, status_code=302, headers={"Location": callback_url})

        auth_response_redirect = requests.post(init_response.url, allow_redirects=False)

    callback_response = app.get(auth_response_redirect.headers["location"])

    return callback_response


class OIDCFlowTests(OIDCMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProfileApphook)
        cls._infra_user_pks = set(User.objects.values_list("pk", flat=True))

    @property
    def regular_users(self):
        return User.objects.exclude(pk__in=self._infra_user_pks)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.admin),
    )
    def test_existing_email_updates_admin_user(
        self,
        mock_config_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_admin=True)
        # set up a user with a colliding email address
        # sub is the oidc_id field in our db
        mock_get_userinfo.return_value = {
            "email": "existing_user@example.com",
            "sub": "some_username",
        }
        user = UserFactory.create(email="existing_user@example.com")
        self.assertEqual(user.oidc_id, "")
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_ADMIN_CONFIG_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("admin:index"), fetch_redirect_response=True
        )

        self.assertEqual(self.regular_users.count(), 1)

        user.refresh_from_db()

        self.assertEqual(user.oidc_id, "some_username")
        self.assertEqual(user.login_type, LoginTypeChoices.oidc)
        self.assertEqual(user.is_staff, True)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_existing_email_updates_regular_user(
        self,
        mock_config_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_admin=True, make_users_staff=False)
        # set up a user with a colliding email address
        # sub is the oidc_id field in our db
        mock_get_userinfo.return_value = {
            "email": "existing_user@example.com",
            "sub": "some_username",
        }
        user = UserFactory.create(email="existing_user@example.com")
        self.assertEqual(user.oidc_id, "")
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_ADMIN_CONFIG_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=True
        )

        self.assertEqual(self.regular_users.count(), 1)

        user.refresh_from_db()

        self.assertEqual(user.oidc_id, "some_username")
        self.assertEqual(user.login_type, LoginTypeChoices.oidc)
        self.assertEqual(user.is_staff, False)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_existing_oidc_id_updates_regular_user(
        self,
        mock_config_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(
            with_admin=True, make_users_staff=False, first_name_claim=["first_name"]
        )
        # set up a user with a colliding email address
        # sub is the oidc_id field in our db
        mock_get_userinfo.return_value = {
            "email": "existing_user@example.com",
            "sub": "some_username",
            "first_name": "bar",
        }
        user = UserFactory.create(
            oidc_id="some_username", first_name="Foo", login_type=LoginTypeChoices.oidc
        )
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_ADMIN_CONFIG_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=True
        )

        self.assertEqual(self.regular_users.count(), 1)

        user.refresh_from_db()

        self.assertEqual(user.oidc_id, "some_username")
        self.assertEqual(user.first_name, "bar")
        self.assertEqual(user.is_staff, False)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_existing_case_sensitive_email_updates_user(
        self,
        mock_config_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_admin=True, make_users_staff=False)
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_ADMIN_CONFIG_IDENTIFIER,
            }
        }
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
        self.assertEqual(db_user.is_staff, False)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.admin),
    )
    def test_new_admin_user_is_created_when_new_email(
        self,
        mock_config_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_admin=True)
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {
            "email": "new_user@example.com",
            "sub": "some_username",
        }
        UserFactory.create(email="existing_user@example.com")
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_ADMIN_CONFIG_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("admin:index"), fetch_redirect_response=True
        )

        new_user = User.objects.get(email="new_user@example.com")

        self.assertEqual(new_user.oidc_id, "some_username")
        self.assertEqual(new_user.login_type, LoginTypeChoices.oidc)
        self.assertEqual(new_user.is_staff, True)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_new_regular_user_is_created_when_new_email(
        self,
        mock_config_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_admin=True, make_users_staff=False)
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {
            "email": "new_user@example.com",
            "sub": "some_username",
        }
        UserFactory.create(email="existing_user@example.com")
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_ADMIN_CONFIG_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("oidc_authentication_callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("pages-root"), fetch_redirect_response=True
        )

        new_user = User.objects.get(email="new_user@example.com")

        self.assertEqual(new_user.oidc_id, "some_username")
        self.assertEqual(new_user.login_type, LoginTypeChoices.oidc)
        self.assertEqual(new_user.is_staff, False)

    def test_error_page_direct_access_forbidden(self):
        error_url = reverse("admin-oidc-error")

        response = self.client.get(error_url)

        self.assertEqual(response.status_code, 403)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_error_first_cleared_after_succesful_login(
        self,
        mock_config_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_admin=True)
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
            session["oidc_states"] = {
                "mock": {
                    "nonce": "nonce",
                    "config_identifier": OIDC_ADMIN_CONFIG_IDENTIFIER,
                }
            }
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


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class DigiDOIDCFlowTests(OIDCMixin, WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProfileApphook)
        cls._infra_user_pks = set(User.objects.values_list("pk", flat=True))

    @property
    def regular_users(self):
        return User.objects.exclude(pk__in=self._infra_user_pks)

    @patch("open_inwoner.accounts.signals._update_user_from_brp")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_existing_bsn_creates_no_new_user(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_brp,
    ):
        OIDCClientFactory(with_digid=True, bsn_claim=["sub"])
        # set up a user with a colliding email address
        # sub is the oidc_id field in our db
        mock_get_userinfo.return_value = {
            "email": "existing_user@example.com",
            "sub": "123456782",
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_DIGID_IDENTIFIER,
            }
        }
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
        self.assertEqual(self.regular_users.count(), 1)

        db_user = self.regular_users.get()

        # User data was prepopulated, so this should not be called
        mock_brp.assert_not_called()
        self.assertEqual(db_user.id, user.id)
        self.assertEqual(db_user.bsn, "123456782")
        self.assertEqual(db_user.login_type, LoginTypeChoices.digid)
        self.assertEqual(db_user.first_name, "John")
        self.assertEqual(db_user.last_name, "Doe")

    @patch("open_inwoner.accounts.signals._update_user_from_brp")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_new_user_is_created_when_new_bsn(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_brp,
    ):
        OIDCClientFactory(with_digid=True, bsn_claim=["sub"])
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {"sub": "000000000"}
        DigidUserFactory.create(bsn="123456782", email="existing_user@example.com")
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_DIGID_IDENTIFIER,
            }
        }
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

    def test_frontend_logout_redirects_to_correct_url_with_optional_hints(self):
        OIDCClientFactory(
            with_digid=True,
            oidc_provider__oidc_op_logout_endpoint="http://localhost:8080/logout",
        )
        # set up a user with a non existing email address
        user = DigidUserFactory.create(
            bsn="123456782", email="existing_user@example.com"
        )

        for logout_with_hints in (True, False):
            with (
                self.subTest(logout_with_hints=logout_with_hints),
                override_settings(OIDC_FRONTEND_LOGOUT_WITH_HINTS=logout_with_hints),
            ):
                self.client.force_login(user)
                session = self.client.session
                session["oidc_states"] = {
                    "mock": {
                        "nonce": "nonce",
                        "config_identifier": OIDC_DIGID_IDENTIFIER,
                    }
                }
                session["oidc_id_token"] = "foo"
                session.save()
                logout_url = reverse("digid_oidc:logout")

                # enter the logout flow
                logout_response = self.client.get(logout_url)

                expected_redirect_url = "http://localhost:8080/logout"
                if logout_with_hints:
                    params = urlencode(
                        dict(
                            id_token_hint="foo",
                            post_logout_redirect_uri=f"http://testserver{settings.LOGOUT_REDIRECT_URL}",
                        )
                    )
                    expected_redirect_url += f"?{params}"

                self.assertRedirects(
                    logout_response,
                    expected_redirect_url,
                    fetch_redirect_response=False,
                )

                self.assertNotIn("oidc_states", self.client.session)
                self.assertNotIn("oidc_id_token", self.client.session)
                self.assertFalse(logout_response.wsgi_request.user.is_authenticated)

    def test_logout_without_sso_logout_configured(self):
        OIDCClientFactory(with_digid=True, oidc_provider__oidc_op_logout_endpoint="")
        # set up a user with a non existing email address
        user = DigidUserFactory.create(
            bsn="123456782", email="existing_user@example.com"
        )
        self.client.force_login(user)
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_DIGID_IDENTIFIER,
            }
        }
        session["oidc_id_token"] = "foo"
        session.save()
        logout_url = reverse("digid_oidc:logout")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the logout flow
        logout_response = self.client.get(logout_url)

        self.assertRedirects(
            logout_response,
            settings.LOGOUT_REDIRECT_URL,
            fetch_redirect_response=False,
        )

        self.assertNotIn("oidc_states", self.client.session)
        self.assertNotIn("oidc_id_token", self.client.session)
        self.assertFalse(logout_response.wsgi_request.user.is_authenticated)

    def test_logout_falls_back_to_local_logout_when_client_disabled(self):
        # A DigiD login_type can also be obtained via SAML, in which case the OIDC
        # client is disabled. Even with a logout endpoint configured we must not try
        # to sign out at the IdP, but just kill our own session.
        OIDCClientFactory(
            with_digid=True,
            enabled=False,
            oidc_provider__oidc_op_logout_endpoint="http://localhost:8080/logout",
        )
        user = DigidUserFactory.create(bsn="123456782")
        self.client.force_login(user)

        logout_response = self.client.get(reverse("digid_oidc:logout"))

        self.assertRedirects(
            logout_response,
            settings.LOGOUT_REDIRECT_URL,
            fetch_redirect_response=False,
        )
        self.assertFalse(logout_response.wsgi_request.user.is_authenticated)

    def test_logout_falls_back_to_local_logout_when_client_missing(self):
        # No OIDC client exists for the identifier (e.g. never provisioned); logout
        # must still succeed locally instead of raising a 400.
        user = DigidUserFactory.create(bsn="123456782")
        self.client.force_login(user)

        logout_response = self.client.get(reverse("digid_oidc:logout"))

        self.assertRedirects(
            logout_response,
            settings.LOGOUT_REDIRECT_URL,
            fetch_redirect_response=False,
        )
        self.assertFalse(logout_response.wsgi_request.user.is_authenticated)

    def test_error_page_direct_access(self):
        error_url = reverse("oidc-error")

        response = self.client.get(error_url)

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_error_first_cleared_after_succesful_login(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_digid=True)
        user = DigidUserFactory.create(bsn="123456782")
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
            session["oidc_states"] = {
                "mock": {
                    "nonce": "nonce",
                    "config_identifier": OIDC_DIGID_IDENTIFIER,
                }
            }
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

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_login_error_message_mapped_in_config(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_digid=True)
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "bsn": "123456782",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_DIGID_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("digid_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url,
            {
                "error": "access_denied",
                "error_description": "The user cancelled",
                "state": "mock",
            },
        )

        self.assertRedirects(
            callback_response, reverse("oidc-error"), fetch_redirect_response=False
        )

        error_response = self.client.get(callback_response.url)

        self.assertRedirects(
            error_response, reverse("login"), fetch_redirect_response=False
        )

        login_response = self.client.get(error_response.url)
        doc = PyQuery(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, "U heeft het inloggen met DigiD geannuleerd.")

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_login_error_message_not_mapped_in_config(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_digid=True)
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "bsn": "123456782",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_DIGID_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("digid_oidc:callback")

        # enter the login flow with an unmapped error code
        callback_response = self.client.get(
            callback_url,
            {
                "error": "server_error",
                "error_description": "",
                "state": "mock",
            },
        )

        self.assertRedirects(
            callback_response, reverse("oidc-error"), fetch_redirect_response=False
        )

        error_response = self.client.get(callback_response.url)

        self.assertRedirects(
            error_response, reverse("login"), fetch_redirect_response=False
        )

        login_response = self.client.get(error_response.url)
        doc = PyQuery(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, str(GENERIC_DIGID_ERROR_MSG))

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_login_validation_error(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_digid=True)
        mock_verify_token.side_effect = ValidationError("Something went wrong")
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "bsn": "123456782",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_DIGID_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("digid_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("oidc-error"), fetch_redirect_response=False
        )

        error_response = self.client.get(callback_response.url)

        self.assertRedirects(
            error_response, reverse("login"), fetch_redirect_response=False
        )

        login_response = self.client.get(error_response.url)
        doc = PyQuery(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, str(GENERIC_DIGID_ERROR_MSG))

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_redirect_after_login_with_registration(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        """
        Full authentication flow with redirect after successful login and registration
        """
        OIDCClientFactory(
            with_digid=True,
            oidc_provider__oidc_op_authorization_endpoint="http://idp.local/auth",
        )
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "bsn": "123456782",
        }

        redirect_url = reverse("profile:detail")

        callback_response = perform_oidc_login(
            self.app, "digid", redirect_url=redirect_url
        )

        user = self.regular_users.get()

        self.assertEqual(user.pk, int(self.app.session.get("_auth_user_id")))
        self.assertEqual(user.bsn, "123456782")

        self.assertRedirects(
            callback_response, reverse("profile:detail"), fetch_redirect_response=False
        )

        response = self.app.get(callback_response.url)

        self.assertRedirects(
            response,
            furl(reverse("profile:registration_necessary"))
            .set({"next": reverse("profile:detail")})
            .url,
            fetch_redirect_response=False,
        )

        necessary_fields_response = self.app.get(response.url)
        form = necessary_fields_response.forms["necessary-form"]

        form["first_name"] = "a"
        form["last_name"] = "a"
        form["email"] = "foo@bar.org"

        necessary_fields_response = form.submit()

        self.assertRedirects(
            necessary_fields_response,
            reverse("profile:detail"),
            fetch_redirect_response=False,
        )

        profile_response = self.app.get(necessary_fields_response.url)

        self.assertEqual(profile_response.status_code, 200)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_redirect_after_login_no_registration(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        """
        Full authentication flow with redirect after successful login
        """
        OIDCClientFactory(
            with_digid=True,
            oidc_provider__oidc_op_authorization_endpoint="http://idp.local/auth",
        )
        # Create a user that already has a proper email adress, to avoid necessary field
        # registration
        DigidUserFactory.create(bsn="123456782", email="foo@bar.com")

        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "bsn": "123456782",
        }

        redirect_url = reverse("profile:detail")

        callback_response = perform_oidc_login(
            self.app, "digid", redirect_url=redirect_url
        )

        user = self.regular_users.get()

        self.assertEqual(user.pk, int(self.app.session.get("_auth_user_id")))
        self.assertEqual(user.bsn, "123456782")

        self.assertRedirects(
            callback_response, reverse("profile:detail"), fetch_redirect_response=False
        )

        profile_response = self.app.get(callback_response.url)

        self.assertEqual(profile_response.status_code, 200)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class eHerkenningOIDCFlowTests(OIDCMixin, WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProfileApphook)
        # create_homepage() creates a CMS infrastructure user (cms-test@example.com)
        # for versioning. Track its PK so tests can exclude it from user assertions.
        cls._infra_user_pks = set(User.objects.values_list("pk", flat=True))

    @property
    def regular_users(self):
        """Users created by tests, excluding CMS infrastructure users."""
        return User.objects.exclude(pk__in=self._infra_user_pks)

    @skip(
        "[#2662] This guarded a ValueError that the old mozilla-django-oidc-db "
        "raised for an empty claim path. The OIDCClient architecture stores claim "
        "paths in the options JSON and no longer raises here, so the "
        "misconfiguration guard needs rethinking before this can be ported."
    )
    def test_missing_claims_in_configuration_raises_exception(self):
        pass

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_missing_claim_in_token_redirects_to_error_page(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_retrieve_rsin_with_kvk,
        mock_kvk,
        mock_get_basisprofiel,
    ):
        OIDCClientFactory(with_eherkenning=True, legal_subject_claim=["sub"])
        mock_get_userinfo.return_value = {
            "email": "existing_user@example.com",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("eherkenning_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("oidc-error"), fetch_redirect_response=False
        )
        self.assertEqual(self.regular_users.count(), 0)

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_existing_kvk_creates_no_new_user(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_retrieve_rsin_with_kvk,
        mock_kvk,
        mock_get_basisprofiel,
    ):
        OIDCClientFactory(
            with_eherkenning=True,
            legal_subject_claim=["sub"],
            branch_number_claim=["branch"],
        )
        mock_kvk.return_value = [
            {"vestigingsnummer": "1234"},
        ]
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }

        mock_retrieve_rsin_with_kvk.return_value = "123456789"
        # set up a user with a colliding email address
        # sub is the oidc_id field in our db
        mock_get_userinfo.return_value = {
            "email": "existing_user@example.com",
            "sub": "12345678",
        }
        user = eHerkenningUserFactory.create(
            first_name="John",
            last_name="Doe",
            kvk="12345678",
            rsin="123456789",
            email="user-12345678@localhost",
            is_prepopulated=True,
        )
        self.assertEqual(user.oidc_id, "")
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
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
        self.assertEqual(self.regular_users.count(), 1)

        db_user = self.regular_users.get()

        # User data was prepopulated, so this should not be called
        mock_retrieve_rsin_with_kvk.assert_not_called()
        self.assertEqual(db_user.id, user.id)
        self.assertEqual(db_user.kvk, "12345678")
        self.assertEqual(db_user.login_type, LoginTypeChoices.eherkenning)
        self.assertEqual(db_user.first_name, "John")
        self.assertEqual(db_user.last_name, "Doe")

        self.assertEqual(callback_response.wsgi_request.user, db_user)
        self.assertFalse(
            EHerkenningSessionContext(
                callback_response.wsgi_request
            ).is_branch_restricted()
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_new_user_is_created_when_new_kvk(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_retrieve_rsin_with_kvk,
        mock_get_basisprofiel,
    ):
        OIDCClientFactory(with_eherkenning=True, legal_subject_claim=["sub"])
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }
        mock_retrieve_rsin_with_kvk.return_value = "123456789"
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {"sub": "00000000"}
        eHerkenningUserFactory.create(
            kvk="12345678", rsin="123456789", email="existing_user@example.com"
        )
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
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

        mock_retrieve_rsin_with_kvk.assert_called_with(kvk="00000000")
        salt = "generate_email_from_bsn"
        hashed_bsn = md5(
            (salt + "00000000").encode(), usedforsecurity=False
        ).hexdigest()
        self.assertEqual(new_user.email, f"{hashed_bsn}@localhost")
        self.assertEqual(new_user.rsin, "123456789")
        self.assertEqual(new_user.login_type, LoginTypeChoices.eherkenning)

        self.assertEqual(callback_response.wsgi_request.user, new_user)
        self.assertFalse(
            EHerkenningSessionContext(
                callback_response.wsgi_request
            ).is_branch_restricted()
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_new_user_is_created_when_existing_kvk_without_vestiging(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_retrieve_rsin_with_kvk,
        mock_get_basisprofiel,
    ):
        OIDCClientFactory(
            with_eherkenning=True,
            legal_subject_claim=["sub"],
            branch_number_claim=["urn:etoegang:1.9:ServiceRestriction:Vestigingsnr"],
        )
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }
        mock_retrieve_rsin_with_kvk.return_value = "123456789"
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {
            "sub": "12345678",
            "urn:etoegang:1.9:ServiceRestriction:Vestigingsnr": "849586958473",
        }
        existing_user = eHerkenningUserFactory.create(
            kvk="12345678", rsin="123456789", email="existing_user@example.com"
        )
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
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
        new_user = User.objects.get(kvk="12345678", vestiging="849586958473")

        mock_retrieve_rsin_with_kvk.assert_called_with(kvk="12345678")
        salt = "generate_email_from_bsn"
        hashed_bsn = md5(
            (salt + "12345678" + "849586958473").encode(), usedforsecurity=False
        ).hexdigest()
        self.assertEqual(new_user.email, f"{hashed_bsn}@localhost")
        self.assertEqual(new_user.rsin, "123456789")
        self.assertEqual(new_user.vestiging, "849586958473")
        self.assertEqual(new_user.login_type, LoginTypeChoices.eherkenning)

        self.assertEqual(existing_user.kvk, new_user.kvk)
        self.assertEqual(existing_user.vestiging, "")

        self.assertEqual(set(self.regular_users), {existing_user, new_user})

        self.assertEqual(callback_response.wsgi_request.user, new_user)
        self.assertTrue(
            EHerkenningSessionContext(
                callback_response.wsgi_request
            ).is_branch_restricted()
        )

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch("open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_existing_user_is_returned_for_already_existing_kvk_and_vestiging(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_retrieve_rsin_with_kvk,
        mock_get_basisprofiel,
    ):
        OIDCClientFactory(
            with_eherkenning=True,
            legal_subject_claim=["sub"],
            branch_number_claim=["urn:etoegang:1.9:ServiceRestriction:Vestigingsnr"],
        )
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }
        mock_retrieve_rsin_with_kvk.return_value = "123456789"
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {
            "sub": "12345678",
            "urn:etoegang:1.9:ServiceRestriction:Vestigingsnr": "849586958473",
        }
        existing_user = eHerkenningUserFactory.create(
            kvk="12345678",
            rsin="123456789",
            email="existing_user@example.com",
            vestiging="849586958473",
        )
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
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
        db_user = self.regular_users.get()

        mock_retrieve_rsin_with_kvk.assert_not_called()
        self.assertEqual(db_user.pk, existing_user.pk)
        self.assertEqual(db_user.kvk, existing_user.kvk)
        self.assertEqual(db_user.rsin, existing_user.rsin)

        self.assertEqual(callback_response.wsgi_request.user, db_user)
        self.assertTrue(
            EHerkenningSessionContext(
                callback_response.wsgi_request
            ).is_branch_restricted()
        )

    def test_logout(self):
        OIDCClientFactory(
            with_eherkenning=True,
            legal_subject_claim=["kvk"],
            oidc_provider__oidc_op_logout_endpoint="http://localhost:8080/logout",
        )
        # set up a user with a non existing email address
        user = eHerkenningUserFactory.create(
            kvk="12345678", email="existing_user@example.com"
        )
        self.client.force_login(user)
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
        session["oidc_id_token"] = "foo"
        session.save()
        logout_url = reverse("eherkenning_oidc:logout")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the logout flow
        logout_response = self.client.get(logout_url)

        self.assertRedirects(
            logout_response,
            "http://localhost:8080/logout"
            + "?"
            + urlencode(
                dict(
                    id_token_hint="foo",
                    post_logout_redirect_uri=f"http://testserver{settings.LOGOUT_REDIRECT_URL}",
                )
            ),
            fetch_redirect_response=False,
        )

        self.assertNotIn("oidc_states", self.client.session)
        self.assertNotIn("oidc_id_token", self.client.session)
        self.assertFalse(logout_response.wsgi_request.user.is_authenticated)

    def test_logout_without_sso_logout_configured(self):
        OIDCClientFactory(
            with_eherkenning=True,
            legal_subject_claim=["kvk"],
            oidc_provider__oidc_op_logout_endpoint="",
        )
        # set up a user with a non existing email address
        user = eHerkenningUserFactory.create(
            kvk="12345678", email="existing_user@example.com"
        )
        self.client.force_login(user)
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
        session["oidc_id_token"] = "foo"
        session.save()
        logout_url = reverse("eherkenning_oidc:logout")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the logout flow
        logout_response = self.client.get(logout_url)

        self.assertRedirects(
            logout_response,
            settings.LOGOUT_REDIRECT_URL,
            fetch_redirect_response=False,
        )

        self.assertNotIn("oidc_states", self.client.session)
        self.assertNotIn("oidc_id_token", self.client.session)
        self.assertFalse(logout_response.wsgi_request.user.is_authenticated)

    @modify_settings(
        MIDDLEWARE={
            "remove": [
                "open_inwoner.accounts.middleware.NecessaryFieldsMiddleware",
                "open_inwoner.kvk.middleware.KvKLoginMiddleware",
            ]
        }
    )
    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch(
        "open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk",
        return_value="123456789",
        autospec=True,
    )
    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches", autospec=True)
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token",
        autospec=True,
    )
    def test_error_first_cleared_after_succesful_login(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_kvk,
        mock_retrieve_rsin_with_kvk,
        mock_get_basisprofiel,
    ):
        OIDCClientFactory(with_eherkenning=True, legal_subject_claim=["kvk"])
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }
        mock_kvk.return_value = [{"vestigingsnummber": "1234"}]
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }

        session = self.client.session
        session["oidc-error"] = "some error"
        session.save()
        error_url = reverse("admin-oidc-error")

        with self.subTest("with error"):
            response = self.client.get(error_url)

            self.assertEqual(response.status_code, 200)

        with self.subTest("after succesful login"):
            session["oidc_states"] = {
                "mock": {
                    "nonce": "nonce",
                    "config_identifier": OIDC_EH_IDENTIFIER,
                }
            }
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

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_login_error_message_mapped_in_config(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_eherkenning=True, legal_subject_claim=["kvk"])
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("eherkenning_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url,
            {
                "error": "access_denied",
                "error_description": "The user cancelled",
                "state": "mock",
            },
        )

        self.assertRedirects(
            callback_response, reverse("oidc-error"), fetch_redirect_response=False
        )

        error_response = self.client.get(callback_response.url)

        self.assertRedirects(
            error_response, reverse("login"), fetch_redirect_response=False
        )

        login_response = self.client.get(error_response.url)
        doc = PyQuery(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, "U heeft het inloggen met eHerkenning geannuleerd.")

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_login_error_message_not_mapped_in_config(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        OIDCClientFactory(with_eherkenning=True, legal_subject_claim=["kvk"])
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("eherkenning_oidc:callback")

        # enter the login flow with an unmapped error code
        callback_response = self.client.get(
            callback_url,
            {
                "error": "server_error",
                "error_description": "",
                "state": "mock",
            },
        )

        self.assertRedirects(
            callback_response, reverse("oidc-error"), fetch_redirect_response=False
        )

        error_response = self.client.get(callback_response.url)

        self.assertRedirects(
            error_response, reverse("login"), fetch_redirect_response=False
        )

        login_response = self.client.get(error_response.url)
        doc = PyQuery(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, str(GENERIC_EHERKENNING_ERROR_MSG))

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_login_validation_error(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_get_basisprofiel,
    ):
        OIDCClientFactory(with_eherkenning=True, legal_subject_claim=["kvk"])
        mock_verify_token.side_effect = ValidationError("Something went wrong")
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("eherkenning_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response, reverse("oidc-error"), fetch_redirect_response=False
        )

        error_response = self.client.get(callback_response.url)

        self.assertRedirects(
            error_response, reverse("login"), fetch_redirect_response=False
        )

        login_response = self.client.get(error_response.url)
        doc = PyQuery(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, str(GENERIC_EHERKENNING_ERROR_MSG))

    @patch(
        "open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk", autospec=True
    )
    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token",
        autospec=True,
    )
    def test_login_as_eenmanszaak_blocked(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_get_basisprofiel,
        mock_retrieve_rsin_with_kvk,
    ):
        """
        Eenmanszaken do not have an RSIN, which means that if we have a feature flag
        to fetch resources using RSIN (from Open Zaak or Open Klant) enabled, we cannot
        let eenmanszaken log in using eHerkenning
        """
        OIDCClientFactory(with_eherkenning=True, legal_subject_claim=["sub"])
        mock_retrieve_rsin_with_kvk.return_value = ""
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Eenmanszaak"}}
        }
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {"sub": "00000000"}
        eHerkenningUserFactory.create(kvk="12345678", email="existing_user@example.com")
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EH_IDENTIFIER,
            }
        }
        session.save()
        callback_url = reverse("eherkenning_oidc:callback")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the login flow
        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        # User is logged out and redirected to login view
        self.assertNotIn("_auth_user_id", self.app.session)
        self.assertRedirects(
            callback_response, reverse("login"), fetch_redirect_response=False
        )

        response = self.client.get(callback_response.url)

        self.assertContains(response, _("Use DigiD to log in as a sole proprietor."))

    @skip("Slated for deprecation")
    @patch(
        "open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk",
        return_value="123456789",
        autospec=True,
    )
    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch(
        "open_inwoner.kvk.client.KvKClient.get_all_company_branches",
        autospec=True,
    )
    @patch(
        "open_inwoner.utils.context_processors.SiteConfiguration",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token",
        autospec=True,
    )
    def test_redirect_after_login_with_registration_and_branch_selection(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_siteconfig,
        mock_kvk,
        mock_get_basisprofiel,
        mock_retrieve_rsin_with_kvk,
    ):
        """
        Full authentication flow with redirect after successful login
        """
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }
        mock_siteconfig.return_value = SiteConfiguration(id=1, eherkenning_enabled=True)
        mock_kvk.return_value = [
            {"kvkNummer": "12345678"},
            {"kvkNummer": "12345678", "vestigingsnummer": "1234"},
        ]
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }

        self.assertEqual(User.objects.count(), 0)

        redirect_url = reverse("profile:detail")

        callback_response = perform_oidc_login(
            self.app, "eherkenning", redirect_url=redirect_url
        )

        user = User.objects.get()

        self.assertEqual(user.pk, int(self.app.session.get("_auth_user_id")))
        self.assertEqual(user.kvk, "12345678")

        self.assertRedirects(
            callback_response, reverse("profile:detail"), fetch_redirect_response=False
        )

        response = self.app.get(callback_response.url)

        self.assertRedirects(
            response,
            furl(reverse("kvk:branches")).set({"next": reverse("profile:detail")}).url,
            fetch_redirect_response=False,
        )

        branches_response = self.app.get(response.url)
        form = branches_response.forms["eherkenning-branch-form"]
        form["branch_number"] = "1234"
        branches_response = form.submit()

        self.assertRedirects(
            branches_response,
            furl(reverse("profile:detail"))
            .set({"next": reverse("profile:detail")})
            .url,
            fetch_redirect_response=False,
        )

        necessary_fields_response = self.app.get(branches_response.url).follow()

        form = necessary_fields_response.forms["necessary-form"]

        form["email"] = "foo@bar.org"

        necessary_fields_response = form.submit()

        self.assertRedirects(
            necessary_fields_response,
            reverse("profile:detail"),
            fetch_redirect_response=False,
        )

        profile_response = self.app.get(necessary_fields_response.url)

        self.assertEqual(profile_response.status_code, 200)

    @skip("Slated for deprecation")
    @patch(
        "open_inwoner.accounts.signals.KvKClient.retrieve_rsin_with_kvk",
        autospec=True,
    )
    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch(
        "open_inwoner.kvk.client.KvKClient.get_all_company_branches",
        autospec=True,
    )
    @patch(
        "open_inwoner.utils.context_processors.SiteConfiguration",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token",
        autospec=True,
    )
    @patch(
        "mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token",
        autospec=True,
    )
    def test_redirect_after_login_no_registration_with_branch_selection(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_siteconfig,
        mock_kvk,
        mock_get_basisprofiel,
        mock_retrieve_rsin_with_kvk,
    ):
        """
        Full authentication flow with redirect after successful login
        """
        user = eHerkenningUserFactory.create(kvk="12345678", rsin="123456789")
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }
        mock_siteconfig.return_value = SiteConfiguration(id=1, eherkenning_enabled=True)
        mock_kvk.return_value = [
            {"kvkNummer": "12345678"},
            {"kvkNummer": "12345678", "vestigingsnummer": "1234"},
        ]
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }

        self.assertEqual(User.objects.count(), 1)

        redirect_url = reverse("profile:detail")

        callback_response = perform_oidc_login(
            self.app, "eherkenning", redirect_url=redirect_url
        )

        user = User.objects.get()

        self.assertEqual(user.pk, int(self.app.session.get("_auth_user_id")))
        self.assertEqual(user.kvk, "12345678")

        self.assertRedirects(
            callback_response, reverse("profile:detail"), fetch_redirect_response=False
        )

        response = self.app.get(callback_response.url)

        self.assertRedirects(
            response,
            furl(reverse("kvk:branches")).set({"next": reverse("profile:detail")}).url,
            fetch_redirect_response=False,
        )

        branches_response = self.app.get(response.url)
        form = branches_response.forms["eherkenning-branch-form"]
        form["branch_number"] = "1234"
        branches_response = form.submit()

        self.assertRedirects(
            branches_response,
            furl(reverse("profile:detail"))
            .set({"next": reverse("profile:detail")})
            .url,
            fetch_redirect_response=False,
        )

        profile_response = self.app.get(branches_response.url)

        self.assertEqual(profile_response.status_code, 200)

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch("open_inwoner.utils.context_processors.SiteConfiguration")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_redirect_after_login_no_registration_and_no_branch_selection(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_siteconfig,
        mock_kvk,
        mock_get_basisprofiel,
    ):
        """
        Full authentication flow with redirect after successful login
        """
        OIDCClientFactory(
            with_eherkenning=True,
            legal_subject_claim=["kvk"],
            oidc_provider__oidc_op_authorization_endpoint="http://idp.local/auth",
        )
        user = eHerkenningUserFactory.create(kvk="12345678", rsin="123456789")
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }
        mock_siteconfig.return_value = SiteConfiguration(id=1, eherkenning_enabled=True)
        mock_kvk.return_value = [
            {"kvkNummer": "12345678"},
        ]
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }

        self.assertEqual(self.regular_users.count(), 1)

        redirect_url = reverse("profile:detail")

        callback_response = perform_oidc_login(
            self.app, "eherkenning", redirect_url=redirect_url
        )

        user = self.regular_users.get()

        self.assertEqual(user.pk, int(self.app.session.get("_auth_user_id")))
        self.assertEqual(user.kvk, "12345678")

        self.assertRedirects(
            callback_response, reverse("profile:detail"), fetch_redirect_response=False
        )

        response = self.app.get(callback_response.url)

        # User is redirect to branch selection, but immediately redirected because there
        # is only one branch
        self.assertRedirects(
            response,
            furl(reverse("kvk:branches")).set({"next": reverse("profile:detail")}).url,
            fetch_redirect_response=False,
        )

        profile_response = self.app.get(response.url)

        self.assertRedirects(
            profile_response,
            furl(reverse("profile:detail"))
            .set({"next": reverse("profile:detail")})
            .url,
            fetch_redirect_response=False,
        )

        profile_response = self.app.get(profile_response.url)

        self.assertEqual(profile_response.status_code, 200)

    @patch("open_inwoner.accounts.signals.KvKClient.get_basisprofiel", autospec=True)
    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch("open_inwoner.utils.context_processors.SiteConfiguration")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_redirect_after_login_branch_already_selected(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_siteconfig,
        mock_kvk,
        mock_get_basisprofiel,
    ):
        """
        KVK branch selection should be skipped
        """
        OIDCClientFactory(
            with_eherkenning=True,
            legal_subject_claim=["kvk"],
            oidc_provider__oidc_op_authorization_endpoint="http://idp.local/auth",
        )
        user = eHerkenningVestigingUserFactory.create(
            kvk="12345678", rsin="123456789", vestiging="123456789000"
        )
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
            "urn:etoegang:1.9:ServiceRestriction:Vestigingsnr": "123456789000",
        }
        mock_siteconfig.return_value = SiteConfiguration(id=1, eherkenning_enabled=True)
        mock_kvk.return_value = [
            {"kvkNummer": "12345678"},
            {"kvkNummer": "87654321"},
        ]
        mock_get_basisprofiel.return_value = {
            "_embedded": {"eigenaar": {"rechtsvorm": "Stichting"}}
        }

        self.assertEqual(self.regular_users.count(), 1)

        redirect_url = reverse("profile:detail")

        callback_response = perform_oidc_login(
            self.app, "eherkenning", redirect_url=redirect_url
        )

        user = self.regular_users.get()

        self.assertEqual(user.pk, int(self.app.session.get("_auth_user_id")))
        self.assertEqual(user.kvk, "12345678")
        self.assertEqual(user.vestiging, "123456789000")

        self.assertRedirects(
            callback_response, reverse("profile:detail"), fetch_redirect_response=False
        )

        response = self.app.get(callback_response.url)
        self.assertEqual(response.status_code, 200)


class EIDASOIDCFlowTests(OIDCMixin, WebTest):
    """
    Test the full OIDC authentication flow for eIDAS users.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProfileApphook)
        cls._infra_user_pks = set(User.objects.values_list("pk", flat=True))

    @property
    def regular_users(self):
        return User.objects.exclude(pk__in=self._infra_user_pks)

    def setUp(self):
        super().setUp()
        # Create and configure the eIDAS OIDC client. Claim paths match the claim
        # keys used by this class's userinfo payloads.
        self.oidc_client = OIDCClientFactory(
            with_eidas=True,
            options={
                "identity_settings": {
                    "legal_subject_pseudo_identifier_claim_path": ["sub"],
                    "legal_subject_bsn_identifier_claim_path": ["bsn"],
                    "legal_subject_first_name_claim_path": ["given_name"],
                    "legal_subject_family_name_claim_path": ["family_name"],
                    "company_name_claim_path": ["company_name"],
                    "legal_entity_identifier_claim_path": ["legal_entity_id"],
                }
            },
        )

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_new_eidas_person_with_bsn_is_created(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "sub": "eidas-pseudo-123",
            "bsn": "123456789",
            "given_name": "Jane",
            "family_name": "Doe",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No users should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response,
            reverse("pages-root"),
            fetch_redirect_response=False,
            msg_prefix="User should be redirected to homepage after successful authentication",
        )

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="Exactly one user should be created after authentication",
        )

        new_user = self.regular_users.get()

        self.assertEqual(
            new_user.eidas_pseudo_id,
            "eidas-pseudo-123",
            msg="User's eIDAS pseudo ID must match the value from the configured pseudo_identifier_claim",
        )
        self.assertEqual(
            new_user.bsn,
            "123456789",
            msg="User's BSN must match the value from the configured natural_person_bsn_identifier_claim",
        )
        self.assertEqual(
            new_user.first_name,
            "Jane",
            msg="User's first name must match the value from the configured natural_person_first_name_claim",
        )
        self.assertEqual(
            new_user.last_name,
            "Doe",
            msg="User's last name must match the value from the configured natural_person_family_name_claim",
        )
        self.assertEqual(
            new_user.login_type,
            LoginTypeChoices.eidas_person_bsn,
            msg="User with BSN claim must have login_type set to eidas_person_bsn",
        )
        self.assertTrue(
            new_user.email.endswith("@localhost"),
            msg="User email must be generated with @localhost domain when not provided in claims",
        )

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_existing_eidas_user_logs_in_without_creating_new_user(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        existing_user = UserFactory.create(
            eidas_pseudo_id="eidas-pseudo-456",
            login_type=LoginTypeChoices.eidas_person_pseudo_id,
            first_name="John",
            last_name="Smith",
        )

        mock_get_userinfo.return_value = {
            "sub": "eidas-pseudo-456",
            "given_name": "John",
            "family_name": "Smith",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="Exactly one user should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response,
            reverse("pages-root"),
            fetch_redirect_response=False,
            msg_prefix="Existing user should be redirected to homepage after successful authentication",
        )

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="No new user should be created when existing user with matching pseudo_id logs in",
        )

        user = self.regular_users.get()

        self.assertEqual(
            user.id,
            existing_user.id,
            msg="The authenticated user must be the same as the existing user",
        )
        self.assertEqual(
            user.eidas_pseudo_id,
            "eidas-pseudo-456",
            msg="User's eIDAS pseudo ID must remain unchanged",
        )

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_new_eidas_company_user_is_created(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "sub": "eidas-company-789",
            "company_name": "Acme Corporation",
            "legal_entity_id": "NL123456789B01",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No users should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response,
            reverse("pages-root"),
            fetch_redirect_response=False,
            msg_prefix="Company user should be redirected to homepage after successful authentication",
        )

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="Exactly one user should be created after authentication",
        )

        new_user = self.regular_users.get()

        self.assertEqual(
            new_user.eidas_pseudo_id,
            "eidas-company-789",
            msg="User's eIDAS pseudo ID must match the value from the configured pseudo_identifier_claim",
        )
        self.assertEqual(
            new_user.company_name,
            "Acme Corporation",
            msg="User's company name must match the value from the configured company_name_claim",
        )
        self.assertEqual(
            new_user.eidas_company_id,
            "NL123456789B01",
            msg="User's company ID must match the value from the configured legal_entity_identifier_claim",
        )
        self.assertEqual(
            new_user.login_type,
            LoginTypeChoices.eidas_company,
            msg="User with company claims must have login_type set to eidas_company",
        )
        self.assertEqual(
            new_user.first_name,
            "",
            msg="Company user should not have first_name set",
        )
        self.assertEqual(
            new_user.last_name,
            "",
            msg="Company user should not have last_name set",
        )
        self.assertEqual(
            new_user.bsn,
            "",
            msg="Company user should not have BSN set",
        )

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_new_eidas_person_without_bsn_is_created(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "sub": "eidas-pseudo-no-bsn",
            "given_name": "Maria",
            "family_name": "Garcia",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No users should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response,
            reverse("pages-root"),
            fetch_redirect_response=False,
            msg_prefix="User should be redirected to homepage after successful authentication",
        )

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="Exactly one user should be created after authentication",
        )

        new_user = self.regular_users.get()

        self.assertEqual(
            new_user.eidas_pseudo_id,
            "eidas-pseudo-no-bsn",
            msg="User's eIDAS pseudo ID must match the value from the configured pseudo_identifier_claim",
        )
        self.assertEqual(
            new_user.first_name,
            "Maria",
            msg="User's first name must match the value from the configured natural_person_first_name_claim",
        )
        self.assertEqual(
            new_user.last_name,
            "Garcia",
            msg="User's last name must match the value from the configured natural_person_family_name_claim",
        )
        self.assertEqual(
            new_user.login_type,
            LoginTypeChoices.eidas_person_pseudo_id,
            msg="User without BSN claim must have login_type set to eidas_person_pseudo_id",
        )
        self.assertEqual(
            new_user.bsn,
            "",
            msg="User without BSN claim should have empty BSN field",
        )
        self.assertEqual(
            new_user.company_name,
            "",
            msg="Person user should not have company_name set",
        )
        self.assertEqual(
            new_user.eidas_company_id,
            "",
            msg="Person user should not have eidas_company_id set",
        )

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_authentication_fails_when_pseudo_id_missing(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "given_name": "John",
            "family_name": "Doe",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No users should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response,
            reverse("oidc-error"),
            fetch_redirect_response=False,
            msg_prefix="User should be redirected to error page when authentication fails",
        )

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No user should be created when pseudo_id claim is missing",
        )

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_existing_user_information_is_updated(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        existing_user = UserFactory.create(
            eidas_pseudo_id="eidas-pseudo-update",
            login_type=LoginTypeChoices.eidas_person_pseudo_id,
            first_name="OldFirstName",
            last_name="OldLastName",
        )

        mock_get_userinfo.return_value = {
            "sub": "eidas-pseudo-update",
            "bsn": "392228634",
            "given_name": "NewFirstName",
            "family_name": "NewLastName",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="Exactly one user should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response,
            reverse("pages-root"),
            fetch_redirect_response=False,
            msg_prefix="User should be redirected to homepage after successful authentication",
        )

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="No new user should be created when existing user logs in",
        )

        user = self.regular_users.get()

        self.assertEqual(
            user.id,
            existing_user.id,
            msg="The authenticated user must be the same as the existing user",
        )
        self.assertEqual(
            user.first_name,
            "NewFirstName",
            msg="User's first name should be updated to match new claims",
        )
        self.assertEqual(
            user.last_name,
            "NewLastName",
            msg="User's last name should be updated to match new claims",
        )
        self.assertEqual(
            user.bsn,
            "392228634",
            msg="User's BSN should be updated when provided in new claims",
        )
        self.assertEqual(
            user.login_type,
            LoginTypeChoices.eidas_person_bsn,
            msg="Login type should be updated to eidas_person_bsn when BSN is added",
        )

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_company_claims_take_priority_over_person_claims(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "sub": "eidas-pseudo-mixed",
            "company_name": "Priority Company",
            "legal_entity_id": "NL999999999B01",
            "bsn": "123456789",
            "given_name": "John",
            "family_name": "Doe",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No users should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response,
            reverse("pages-root"),
            fetch_redirect_response=False,
            msg_prefix="User should be redirected to homepage after successful authentication",
        )

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="Exactly one user should be created after authentication",
        )

        new_user = self.regular_users.get()

        self.assertEqual(
            new_user.login_type,
            LoginTypeChoices.eidas_company,
            msg="When both company and person claims present, login_type must be eidas_company",
        )
        self.assertEqual(
            new_user.company_name,
            "Priority Company",
            msg="Company name should be set from company claims",
        )
        self.assertEqual(
            new_user.eidas_company_id,
            "NL999999999B01",
            msg="Company ID should be set from company claims",
        )
        self.assertEqual(
            new_user.first_name,
            "",
            msg="Person first_name should not be set when company claims take priority",
        )
        self.assertEqual(
            new_user.last_name,
            "",
            msg="Person last_name should not be set when company claims take priority",
        )
        self.assertEqual(
            new_user.bsn,
            "",
            msg="Person BSN should not be set when company claims take priority",
        )

    def test_user_cancellation_shows_appropriate_error_message(self):
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No users should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url,
            {
                "error": "access_denied",
                "error_description": "The user cancelled",
                "state": "mock",
            },
        )

        self.assertRedirects(
            callback_response,
            reverse("oidc-error"),
            fetch_redirect_response=False,
            msg_prefix="User should be redirected to error page when authentication is cancelled",
        )

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No user should be created when user cancels authentication",
        )

        error_response = self.client.get(callback_response.url)

        self.assertRedirects(
            error_response,
            reverse("login"),
            fetch_redirect_response=False,
            msg_prefix="Error page should redirect to login page",
        )

        login_response = self.client.get(error_response.url)
        content = login_response.content.decode()

        self.assertIn(
            "U heeft het inloggen met eIDAS geannuleerd",
            content,
            msg="Cancellation error message should be displayed to user",
        )

    def test_logout_with_sso_logout_configured(self):
        provider = self.oidc_client.oidc_provider
        provider.oidc_op_logout_endpoint = "http://localhost:8080/eidas-logout"
        provider.save()

        user = UserFactory.create(
            eidas_pseudo_id="eidas-logout-test",
            login_type=LoginTypeChoices.eidas_person_pseudo_id,
        )
        self.client.force_login(user)
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session["oidc_id_token"] = "test-id-token"
        session.save()

        logout_url = reverse("eidas_oidc:logout")

        logout_response = self.client.get(logout_url)

        self.assertRedirects(
            logout_response,
            "http://localhost:8080/eidas-logout"
            + "?"
            + urlencode(
                dict(
                    id_token_hint="test-id-token",
                    post_logout_redirect_uri=f"http://testserver{settings.LOGOUT_REDIRECT_URL}",
                )
            ),
            fetch_redirect_response=False,
            msg_prefix="Should redirect to OIDC provider logout endpoint with id_token_hint",
        )

        self.assertNotIn(
            "oidc_states",
            self.client.session,
            msg="OIDC states should be cleared from session after logout",
        )
        self.assertNotIn(
            "oidc_id_token",
            self.client.session,
            msg="OIDC ID token should be cleared from session after logout",
        )
        self.assertFalse(
            logout_response.wsgi_request.user.is_authenticated,
            msg="User should not be authenticated after logout",
        )

    def test_logout_without_sso_logout_configured(self):
        provider = self.oidc_client.oidc_provider
        provider.oidc_op_logout_endpoint = ""
        provider.save()

        user = UserFactory.create(
            eidas_pseudo_id="eidas-logout-no-sso",
            login_type=LoginTypeChoices.eidas_person_pseudo_id,
        )
        self.client.force_login(user)
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session["oidc_id_token"] = "test-id-token"
        session.save()

        logout_url = reverse("eidas_oidc:logout")

        logout_response = self.client.get(logout_url)

        self.assertRedirects(
            logout_response,
            settings.LOGOUT_REDIRECT_URL,
            fetch_redirect_response=False,
            msg_prefix="Should redirect to local logout URL when SSO logout not configured",
        )

        self.assertNotIn(
            "oidc_states",
            self.client.session,
            msg="OIDC states should be cleared from session after logout",
        )
        self.assertNotIn(
            "oidc_id_token",
            self.client.session,
            msg="OIDC ID token should be cleared from session after logout",
        )
        self.assertFalse(
            logout_response.wsgi_request.user.is_authenticated,
            msg="User should not be authenticated after logout",
        )

    def test_generic_authentication_error_shows_generic_message(self):
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No users should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url,
            {
                "error": "server_error",
                "error_description": "",
                "state": "mock",
            },
        )

        self.assertRedirects(
            callback_response,
            reverse("oidc-error"),
            fetch_redirect_response=False,
            msg_prefix="User should be redirected to error page when generic error occurs",
        )

        self.assertEqual(
            self.regular_users.count(),
            0,
            msg="No user should be created when authentication error occurs",
        )

        error_response = self.client.get(callback_response.url)

        self.assertRedirects(
            error_response,
            reverse("login"),
            fetch_redirect_response=False,
            msg_prefix="Error page should redirect to login page",
        )

        login_response = self.client.get(error_response.url)
        content = login_response.content.decode()

        self.assertIn(
            "Inloggen bij deze organisatie is niet gelukt",
            content,
            msg="Generic eIDAS error message should be displayed for unmapped errors",
        )

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    def test_duplicate_pseudo_id_prevents_user_creation(
        self,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        existing_user = UserFactory.create(
            eidas_pseudo_id="duplicate-pseudo-id",
            login_type=LoginTypeChoices.eidas_person_pseudo_id,
            first_name="Existing",
            last_name="User",
        )

        mock_get_userinfo.return_value = {
            "sub": "duplicate-pseudo-id",
            "given_name": "New",
            "family_name": "User",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_identifier": OIDC_EIDAS_IDENTIFIER,
            }
        }
        session.save()

        callback_url = reverse("eidas_oidc:callback")

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="Exactly one user should exist before authentication",
        )

        callback_response = self.client.get(
            callback_url, {"code": "mock", "state": "mock"}
        )

        self.assertRedirects(
            callback_response,
            reverse("pages-root"),
            fetch_redirect_response=False,
            msg_prefix="Existing user should be logged in when pseudo_id matches",
        )

        self.assertEqual(
            self.regular_users.count(),
            1,
            msg="No new user should be created when pseudo_id already exists",
        )

        user = self.regular_users.get()

        self.assertEqual(
            user.id,
            existing_user.id,
            msg="The authenticated user must be the existing user with matching pseudo_id",
        )
        self.assertEqual(
            user.eidas_pseudo_id,
            "duplicate-pseudo-id",
            msg="User's eIDAS pseudo_id must remain unchanged",
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class GenericOIDCLogoutViewTests(WebTest):
    """Tests for the generic OIDC logout view (for staff/admin users)."""

    def test_generic_oidc_logout_accepts_post_request_for_oidc_users(self):
        """
        Test that the generic OIDC logout view accepts POST requests for users
        with login_type=oidc.
        """
        user = UserFactory.create(login_type=LoginTypeChoices.oidc)
        self.client.force_login(user)

        logout_url = reverse("oidc_logout")

        # Verify user is logged in
        self.assertTrue(self.client.session.get("_auth_user_id"))

        # Perform logout via POST request
        response = self.client.post(logout_url)

        # Should redirect to logout redirect URL
        self.assertRedirects(
            response,
            settings.LOGOUT_REDIRECT_URL,
            fetch_redirect_response=False,
        )

        # User should be logged out
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_generic_oidc_logout_redirects_non_oidc_users_to_correct_endpoint(self):
        """
        Test that users with non-OIDC login types who manually navigate to
        /oidc/logout/ are redirected to their proper logout endpoint which
        handles SSO logout.
        """
        # Map login types to appropriate factory and any required fields
        login_type_configs = {
            LoginTypeChoices.default: {
                "factory": UserFactory,
                "kwargs": {},
            },
            LoginTypeChoices.digid: {
                "factory": DigidUserFactory,
                "kwargs": {},
            },
            LoginTypeChoices.eherkenning: {
                "factory": eHerkenningUserFactory,
                "kwargs": {},
            },
            LoginTypeChoices.eidas_person_bsn: {
                "factory": UserFactory,
                "kwargs": {
                    "login_type": LoginTypeChoices.eidas_person_bsn,
                    "bsn": "123456782",
                    "eidas_pseudo_id": "eidas-bsn-pseudo-123",
                },
            },
            LoginTypeChoices.eidas_person_pseudo_id: {
                "factory": UserFactory,
                "kwargs": {
                    "login_type": LoginTypeChoices.eidas_person_pseudo_id,
                    "eidas_pseudo_id": "eidas-person-pseudo-456",
                },
            },
            LoginTypeChoices.eidas_company: {
                "factory": UserFactory,
                "kwargs": {
                    "login_type": LoginTypeChoices.eidas_company,
                    "kvk": "12345678",
                    "eidas_pseudo_id": "eidas-bsn-pseudo-789",
                },
            },
        }

        for login_type, config in login_type_configs.items():
            with self.subTest(login_type=login_type):
                factory = config["factory"]
                kwargs = config["kwargs"]
                user = factory.create(**kwargs)

                self.client.force_login(user)

                # User with non-OIDC login_type tries to use generic OIDC logout
                response = self.client.post(reverse("oidc_logout"))

                # Should redirect to the correct logout URL for their login type
                expected_logout_url = user.get_logout_url()
                self.assertRedirects(
                    response, expected_logout_url, fetch_redirect_response=False
                )

                # User should still be logged in (redirect happened before logout)
                self.assertTrue(self.client.session.get("_auth_user_id"))

                # Clean up for next iteration
                self.client.logout()
