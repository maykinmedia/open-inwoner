from hashlib import md5
from typing import Literal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, modify_settings, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import requests
import requests_mock
from django_webtest import DjangoTestApp, DjangoWebtestResponse, WebTest
from furl import furl
from mozilla_django_oidc_db.models import OpenIDConnectConfig
from pyquery import PyQuery as PQ

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from digid_eherkenning_oidc_generics.views import (
    GENERIC_DIGID_ERROR_MSG,
    GENERIC_EHERKENNING_ERROR_MSG,
)
from open_inwoner.configurations.choices import OpenIDDisplayChoices
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.kvk.branches import KVK_BRANCH_SESSION_VARIABLE
from open_inwoner.openzaak.models import OpenZaakConfig

from ...cms.profile.cms_apps import ProfileApphook
from ...cms.tests import cms_tools
from ..choices import LoginTypeChoices
from .factories import DigidUserFactory, UserFactory, eHerkenningUserFactory

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

    doc = PQ(login_response.content)
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


class OIDCFlowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProfileApphook)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True, make_users_staff=True),
    )
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.admin),
    )
    def test_existing_email_updates_admin_user(
        self,
        mock_config_get_solo,
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "mozilla_django_oidc_db.OpenIDConnectConfig",
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

        self.assertEqual(User.objects.count(), 1)

        user.refresh_from_db()

        self.assertEqual(user.oidc_id, "some_username")
        self.assertEqual(user.login_type, LoginTypeChoices.oidc)
        self.assertEqual(user.is_staff, True)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True, make_users_staff=False),
    )
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_existing_email_updates_regular_user(
        self,
        mock_config_get_solo,
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "mozilla_django_oidc_db.OpenIDConnectConfig",
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

        self.assertEqual(User.objects.count(), 1)

        user.refresh_from_db()

        self.assertEqual(user.oidc_id, "some_username")
        self.assertEqual(user.login_type, LoginTypeChoices.oidc)
        self.assertEqual(user.is_staff, False)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(
            id=1,
            enabled=True,
            make_users_staff=False,
            claim_mapping={"first_name": ["first_name"]},
        ),
    )
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_existing_oidc_id_updates_regular_user(
        self,
        mock_config_get_solo,
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
            "first_name": "bar",
        }
        user = UserFactory.create(
            oidc_id="some_username", first_name="Foo", login_type=LoginTypeChoices.oidc
        )
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "mozilla_django_oidc_db.OpenIDConnectConfig",
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

        self.assertEqual(User.objects.count(), 1)

        user.refresh_from_db()

        self.assertEqual(user.oidc_id, "some_username")
        self.assertEqual(user.first_name, "bar")
        self.assertEqual(user.is_staff, False)

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True),
    )
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_existing_case_sensitive_email_updates_user(
        self,
        mock_config_get_solo,
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "mozilla_django_oidc_db.OpenIDConnectConfig",
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
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True, make_users_staff=True),
    )
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.admin),
    )
    def test_new_admin_user_is_created_when_new_email(
        self,
        mock_config_get_solo,
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "mozilla_django_oidc_db.OpenIDConnectConfig",
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
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True, make_users_staff=False),
    )
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_new_regular_user_is_created_when_new_email(
        self,
        mock_config_get_solo,
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "mozilla_django_oidc_db.OpenIDConnectConfig",
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
        "mozilla_django_oidc_db.models.OpenIDConnectConfig.get_solo",
        return_value=OpenIDConnectConfig(id=1, enabled=True),
    )
    @patch(
        "open_inwoner.configurations.models.SiteConfiguration.get_solo",
        return_value=SiteConfiguration(openid_display=OpenIDDisplayChoices.regular),
    )
    def test_error_first_cleared_after_succesful_login(
        self,
        mock_config_get_solo,
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
            session["oidc_states"] = {
                "mock": {
                    "nonce": "nonce",
                    "config_class": "mozilla_django_oidc_db.OpenIDConnectConfig",
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
class DigiDOIDCFlowTests(WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProfileApphook)

    @patch("open_inwoner.haalcentraal.signals.update_brp_data_in_db")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(
            id=1, enabled=True, identifier_claim_name="sub"
        ),
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
                "config_class": "digid_eherkenning_oidc_generics_legacy.OpenIDConnectDigiDConfig",
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
        return_value=OpenIDConnectDigiDConfig(
            id=1, enabled=True, identifier_claim_name="sub"
        ),
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
        mock_get_userinfo.return_value = {"sub": "000000000"}
        DigidUserFactory.create(bsn="123456782", email="existing_user@example.com")
        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "digid_eherkenning_oidc_generics_legacy.OpenIDConnectDigiDConfig",
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "digid_eherkenning_oidc_generics_legacy.OpenIDConnectDigiDConfig",
            }
        }
        session["oidc_id_token"] = "foo"
        session.save()
        logout_url = reverse("digid_oidc:logout")

        self.assertFalse(User.objects.filter(email="new_user@example.com").exists())

        # enter the logout flow
        with requests_mock.Mocker() as m:
            m.post("http://localhost:8080/logout")
            logout_response = self.client.get(logout_url)

            self.assertEqual(len(m.request_history), 1)
            self.assertEqual(m.request_history[0].url, "http://localhost:8080/logout")
            self.assertEqual(m.request_history[0].body, "id_token_hint=foo")

        self.assertRedirects(
            logout_response, reverse("login"), fetch_redirect_response=False
        )

        self.assertNotIn("oidc_states", self.client.session)
        self.assertNotIn("oidc_id_token", self.client.session)

    def test_error_page_direct_access(self):
        error_url = reverse("oidc-error")

        response = self.client.get(error_url)

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

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
                    "config_class": "digid_eherkenning_oidc_generics_legacy.OpenIDConnectDigiDConfig",
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
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(
            id=1,
            enabled=True,
            error_message_mapping={"some mapped message": "Some Error"},
        ),
    )
    def test_login_error_message_mapped_in_config(
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "digid_eherkenning_oidc_generics_legacy.OpenIDConnectDigiDConfig",
            }
        }
        session.save()
        callback_url = reverse("digid_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url,
            {
                "error": "access_denied",
                "error_description": "some mapped message",
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
        doc = PQ(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, "Some Error")

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(id=1, enabled=True),
    )
    def test_login_error_message_not_mapped_in_config(
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
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "digid_eherkenning_oidc_generics_legacy.OpenIDConnectDigiDConfig",
            }
        }
        session.save()
        callback_url = reverse("digid_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url,
            {
                "error": "access_denied",
                "error_description": "some unmapped message",
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
        doc = PQ(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, str(GENERIC_DIGID_ERROR_MSG))

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(id=1, enabled=True),
    )
    def test_login_validation_error(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_verify_token.side_effect = ValidationError("Something went wrong")
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "bsn": "123456782",
        }

        session = self.client.session
        session["oidc_states"] = {
            "mock": {
                "nonce": "nonce",
                "config_class": "digid_eherkenning_oidc_generics_legacy.OpenIDConnectDigiDConfig",
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
        doc = PQ(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, str(GENERIC_DIGID_ERROR_MSG))

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(
            id=1, enabled=True, oidc_op_authorization_endpoint="http://idp.local/auth"
        ),
    )
    def test_redirect_after_login_with_registration(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        """
        Full authentication flow with redirect after successful login and registration
        """
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "bsn": "123456782",
        }

        redirect_url = reverse("profile:detail")

        callback_response = perform_oidc_login(
            self.app, "digid", redirect_url=redirect_url
        )

        user = User.objects.get()

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
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo",
        return_value=OpenIDConnectDigiDConfig(
            id=1, enabled=True, oidc_op_authorization_endpoint="http://idp.local/auth"
        ),
    )
    def test_redirect_after_login_no_registration(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        """
        Full authentication flow with redirect after successful login
        """
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

        user = User.objects.get()

        self.assertEqual(user.pk, int(self.app.session.get("_auth_user_id")))
        self.assertEqual(user.bsn, "123456782")

        self.assertRedirects(
            callback_response, reverse("profile:detail"), fetch_redirect_response=False
        )

        profile_response = self.app.get(callback_response.url)

        self.assertEqual(profile_response.status_code, 200)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class eHerkenningOIDCFlowTests(WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProfileApphook)

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch("open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(
            id=1, enabled=True, identifier_claim_name="sub"
        ),
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
        return_value=OpenIDConnectEHerkenningConfig(
            id=1, enabled=True, identifier_claim_name="sub"
        ),
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
        mock_get_userinfo.return_value = {"sub": "00000000"}
        eHerkenningUserFactory.create(
            kvk="12345678", rsin="123456789", email="existing_user@example.com"
        )
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
        session[KVK_BRANCH_SESSION_VARIABLE] = None
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
            m.post(logout_endpoint_url)
            logout_response = self.client.get(logout_url, follow=False)

            self.assertEqual(len(m.request_history), 1)
            self.assertEqual(m.request_history[0].url, logout_endpoint_url)

        self.assertRedirects(
            logout_response, reverse("login"), fetch_redirect_response=False
        )

        self.assertNotIn("oidc_states", self.client.session)
        self.assertNotIn("oidc_id_token", self.client.session)

    @modify_settings(
        MIDDLEWARE={
            "remove": [
                "open_inwoner.accounts.middleware.NecessaryFieldsMiddleware",
                "open_inwoner.kvk.middleware.KvKLoginMiddleware",
            ]
        }
    )
    @patch(
        "open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk",
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
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(id=1, enabled=True),
        autospec=True,
    )
    def test_error_first_cleared_after_succesful_login(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_kvk,
        mock_retrieve_rsin_with_kvk,
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

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(
            id=1,
            enabled=True,
            error_message_mapping={"some mapped message": "Some Error"},
        ),
    )
    def test_login_error_message_mapped_in_config(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }

        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("eherkenning_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url,
            {
                "error": "access_denied",
                "error_description": "some mapped message",
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
        doc = PQ(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, "Some Error")

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(id=1, enabled=True),
    )
    def test_login_error_message_not_mapped_in_config(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }

        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
        session.save()
        callback_url = reverse("eherkenning_oidc:callback")

        # enter the login flow
        callback_response = self.client.get(
            callback_url,
            {
                "error": "access_denied",
                "error_description": "some unmapped message",
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
        doc = PQ(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, str(GENERIC_EHERKENNING_ERROR_MSG))

    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(id=1, enabled=True),
    )
    def test_login_validation_error(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
    ):
        mock_verify_token.side_effect = ValidationError("Something went wrong")
        mock_get_userinfo.return_value = {
            "sub": "some_username",
            "kvk": "12345678",
        }

        session = self.client.session
        session["oidc_states"] = {"mock": {"nonce": "nonce"}}
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
        doc = PQ(login_response.content)
        error_msg = doc.find(".notification__content").text()

        self.assertEqual(error_msg, str(GENERIC_EHERKENNING_ERROR_MSG))

    @patch(
        "open_inwoner.accounts.views.auth.OpenZaakConfig.get_solo",
        return_value=OpenZaakConfig(fetch_eherkenning_zaken_with_rsin=True),
        autospec=True,
    )
    @patch("open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk", autospec=True)
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
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(
            id=1, enabled=True, identifier_claim_name="sub"
        ),
        autospec=True,
    )
    def test_login_as_eenmanszaak_blocked(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_retrieve_rsin_with_kvk,
        mock_oz_config,
    ):
        """
        Eenmanszaken do not have an RSIN, which means that if we have a feature flag
        to fetch resources using RSIN (from Open Zaak or Open Klant) enabled, we cannot
        let eenmanszaken log in using eHerkenning
        """
        mock_retrieve_rsin_with_kvk.return_value = ""
        # set up a user with a non existing email address
        mock_get_userinfo.return_value = {"sub": "00000000"}
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

        # User is logged out and redirected to login view
        self.assertNotIn("_auth_user_id", self.app.session)
        self.assertRedirects(
            callback_response, reverse("login"), fetch_redirect_response=False
        )

        response = self.client.get(callback_response.url)

        self.assertContains(response, _("Use DigiD to log in as a sole proprietor."))

    @patch(
        "open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk",
        return_value="123456789",
        autospec=True,
    )
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
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(
            id=1, enabled=True, oidc_op_authorization_endpoint="http://idp.local/auth"
        ),
        autospec=True,
    )
    def test_redirect_after_login_with_registration_and_branch_selection(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_siteconfig,
        mock_kvk,
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

    @patch(
        "open_inwoner.kvk.signals.KvKClient.retrieve_rsin_with_kvk",
        autospec=True,
    )
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
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(
            id=1, enabled=True, oidc_op_authorization_endpoint="http://idp.local/auth"
        ),
        autospec=True,
    )
    def test_redirect_after_login_no_registration_with_branch_selection(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_siteconfig,
        mock_kvk,
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

    @patch("open_inwoner.kvk.client.KvKClient.get_all_company_branches")
    @patch("open_inwoner.utils.context_processors.SiteConfiguration")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_userinfo")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.store_tokens")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.verify_token")
    @patch("mozilla_django_oidc_db.backends.OIDCAuthenticationBackend.get_token")
    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo",
        return_value=OpenIDConnectEHerkenningConfig(
            id=1, enabled=True, oidc_op_authorization_endpoint="http://idp.local/auth"
        ),
    )
    def test_redirect_after_login_no_registration_and_no_branch_selection(
        self,
        mock_get_solo,
        mock_get_token,
        mock_verify_token,
        mock_store_tokens,
        mock_get_userinfo,
        mock_siteconfig,
        mock_kvk,
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
        ]

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
