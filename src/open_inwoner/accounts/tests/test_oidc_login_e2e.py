"""
End-to-end (Playwright) tests for the OIDC login flows against a *live* Keycloak.

Unlike the request-based OIDC tests (``test_oidc_views.py``, which mock the
provider's HTTP responses), these drive a real browser through the full
authorization-code flow, so they require a running Keycloak with the ``test``
realm imported. The suite is tagged ``keycloak`` and skips itself when Keycloak
is not reachable.

See the "OIDC login end-to-end tests" section in ``docs/testing.rst`` for how to
run these locally and how they run in CI.
"""

import os
from importlib import import_module
from unittest import SkipTest

from django.conf import settings
from django.test import override_settings, tag

import requests
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.models import OIDCClient, OIDCProvider

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.accounts.oidc_plugins.constants import (
    OIDC_DIGID_IDENTIFIER,
    OIDC_EH_IDENTIFIER,
    OIDC_EIDAS_IDENTIFIER,
)
from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    UserFactory,
    eHerkenningVestigingUserFactory,
)
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.choices import OpenIDDisplayChoices
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.tests.playwright import PlaywrightSyncLiveServerTestCase

# Keycloak realm base URL, reachable by both the browser and the backend. Defaults
# to the docker dev-stack alias; override in CI where Keycloak is published.
KEYCLOAK_REALM_URL = os.environ.get(
    "E2E_KEYCLOAK_REALM_URL",
    "http://keycloak.open-inwoner.local:8080/realms/test",
)
# The `testid` client + secret from docker/keycloak/fixtures/realm.json.
KEYCLOAK_CLIENT_ID = "testid"
KEYCLOAK_CLIENT_SECRET = "7DB3KUAAizYCcmZufpHRVOcD0TOkNO3I"
# Fixed `id` of the realm's `admin` user, which becomes its `sub` claim (stored as
# `oidc_id` on the created Django user).
KEYCLOAK_ADMIN_SUB = "6db2db87-de31-4e30-9f25-cefe5da8b154"


def _endpoint(path: str) -> str:
    return f"{KEYCLOAK_REALM_URL}/protocol/openid-connect/{path}"


@tag("e2e", "keycloak")
@override_settings(DIGID_ENABLED=True)
class OIDCLoginFlowsE2ETest(PlaywrightSyncLiveServerTestCase):
    # Must be a host:port present in the realm's `testid` redirectUris, otherwise
    # Keycloak rejects the callback with "Invalid parameter: redirect_uri".
    host = "localhost"
    port = 8000

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Skip the whole suite if Keycloak / the realm is not reachable, so this
        # doesn't hard-fail environments without a live Keycloak.
        try:
            resp = requests.get(
                f"{KEYCLOAK_REALM_URL}/.well-known/openid-configuration", timeout=5
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise SkipTest(
                f"Keycloak realm not reachable at {KEYCLOAK_REALM_URL}: {exc}"
            ) from exc

    def setUp(self):
        super().setUp()
        # LiveServerTestCase is a TransactionTestCase (tables are flushed between
        # tests), so provision everything per test. Clear the rows the post-migrate
        # signal may have created.
        #
        # The flush also repopulates django_content_type with fresh pks each test,
        # which desyncs djangocms-versioning's process-level content-type cache;
        # without this reset the CMS toolbar 500s when the admin (superuser) flow
        # renders a versioned page. See the helper's docstring.
        cms_tools.reset_versionables_content_type_cache()
        OIDCClient.objects.all().delete()
        OIDCProvider.objects.all().delete()
        self._setup_oidc_config()

        # The login page renders each flow's button only when its config is
        # enabled; a homepage is needed for master.html to render.
        cms_tools.create_homepage()
        # The post-login redirect for users missing required fields targets
        # `profile:registration_necessary`; register the profile apphook so that
        # namespace resolves (otherwise the redirect raises NoReverseMatch -> 500).
        cms_tools.create_apphook_page(ProfileApphook)
        config = SiteConfiguration.get_solo()
        config.cookie_info_text = ""  # disable the cookie banner (it intercepts clicks)
        config.eherkenning_enabled = True  # reveals the Zakelijk tab + button
        config.openid_display = OpenIDDisplayChoices.regular  # org-account button
        config.save()

    @staticmethod
    def _setup_oidc_config() -> None:
        """Mirror docker/setup_configuration/data.yaml, pointed at the test realm."""
        provider = OIDCProvider.objects.create(
            identifier="keycloak-provider",
            oidc_op_authorization_endpoint=_endpoint("auth"),
            oidc_op_token_endpoint=_endpoint("token"),
            oidc_op_user_endpoint=_endpoint("userinfo"),
            oidc_op_jwks_endpoint=_endpoint("certs"),
            oidc_op_logout_endpoint=_endpoint("logout"),
        )
        common = {
            "oidc_provider": provider,
            "enabled": True,
            "oidc_rp_client_id": KEYCLOAK_CLIENT_ID,
            "oidc_rp_client_secret": KEYCLOAK_CLIENT_SECRET,
            "oidc_rp_sign_algo": "RS256",
        }

        OIDCClient.objects.create(
            identifier=OIDC_DIGID_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "bsn"],
            options={"identity_settings": {"bsn_claim_path": ["bsn"]}},
            **common,
        )
        OIDCClient.objects.create(
            identifier=OIDC_EH_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "bsn"],
            options={
                "identity_settings": {
                    "identifier_type_claim_path": ["name_qualifier"],
                    "legal_subject_claim_path": ["legalSubjectID"],
                    "acting_subject_claim_path": ["actingSubjectID"],
                    "branch_number_claim_path": ["vestiging"],
                }
            },
            **common,
        )
        OIDCClient.objects.create(
            identifier=OIDC_EIDAS_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "eidas", "profile"],
            options={
                "identity_settings": {
                    "legal_subject_pseudo_identifier_claim_path": [
                        "person_pseudo_identifier"
                    ],
                    "legal_subject_bsn_identifier_claim_path": [
                        "person_bsn_identifier"
                    ],
                    "legal_subject_first_name_claim_path": ["first_name"],
                    "legal_subject_family_name_claim_path": ["family_name"],
                    "legal_subject_date_of_birth_claim_path": ["birthdate"],
                    "legal_entity_identifier_claim_path": ["company_identifier"],
                    "company_name_claim_path": ["company_name"],
                }
            },
            **common,
        )
        OIDCClient.objects.create(
            identifier=OIDC_ADMIN_CONFIG_IDENTIFIER,
            oidc_rp_scopes_list=["openid", "email", "profile"],
            options={
                "user_settings": {
                    "claim_mappings": {
                        "username": ["sub"],
                        "first_name": ["given_name"],
                    },
                    "username_case_sensitive": False,
                },
                "groups_settings": {
                    "make_users_staff": True,
                    "claim_mapping": ["groups"],
                    "sync": True,
                    "sync_pattern": "*",
                    "superuser_group_names": ["Registreerders", "/Registreerders"],
                    "default_groups": [],
                },
            },
            **common,
        )

    # -- helpers ---------------------------------------------------------------

    def _login(
        self,
        *,
        link_selector: str,
        username: str,
        password: str,
        callback_path: str,
        activate_zakelijk: bool = False,
    ):
        """Log in by visiting the login page and clicking the flow's link.

        This exercises the login-page rendering + link wiring, not just the init
        view. A fresh browser context per call keeps Keycloak's SSO session from
        carrying over between flows.

        ``callback_path`` is the URL path Keycloak must redirect the browser back
        to. For the citizen flows this is the legacy per-provider callback URL:
        that is the redirect_uri customers have whitelisted in their IdP
        configuration, and it must not silently change (see
        LegacyCallbackURLMixin in oidc_plugins.plugins).
        """
        context = self.get_context()
        page = context.new_page()

        # Record the browser's requests so we can assert which callback URL the
        # IdP redirected to.
        request_urls: list[str] = []
        page.on("request", lambda request: request_urls.append(request.url))

        page.goto(self.live_reverse("login"))
        if activate_zakelijk:
            # eHerkenning lives under the (initially hidden) "Zakelijk" tab.
            page.click("#zakelijk_tab")
        page.click(link_selector)

        # Keycloak login form (standard themed ids).
        page.wait_for_selector("#username")
        page.fill("#username", username)
        page.fill("#password", password)
        page.click("#kc-login")

        # Back on our live server (callback + post-login redirect).
        page.wait_for_url(lambda url: url.startswith(self.live_server_url))

        callback_prefix = f"{self.live_server_url}{callback_path}"
        self.assertTrue(
            any(url.startswith(callback_prefix) for url in request_urls),
            f"expected Keycloak to redirect the browser to {callback_prefix}, "
            f"but no request hit it",
        )
        return page

    def _assert_active_session(self, context, user: User) -> None:
        """The browser has an authenticated session for ``user``.

        Sessions are cache-backed, so decode the browser's session cookie through
        the configured session store rather than querying the Session table.
        """
        cookie = next(
            (c for c in context.cookies() if c["name"] == settings.SESSION_COOKIE_NAME),
            None,
        )
        self.assertIsNotNone(cookie, "expected a session cookie after login")

        session_store = import_module(settings.SESSION_ENGINE).SessionStore
        session = session_store(session_key=cookie["value"])
        self.assertEqual(session.get("_auth_user_id"), str(user.pk))

    # -- login creates a user + establishes a session --------------------------

    def test_digid_login(self):
        """DigiD (BSN) via `testuser` -> bsn 111222333, logged in."""
        page = self._login(
            link_selector=".link--digid",
            username="testuser",
            password="testuser",
            callback_path="/digid-oidc/callback/",
        )

        user = User.objects.get(login_type=LoginTypeChoices.digid)
        self.assertEqual(user.bsn, "111222333")
        self._assert_active_session(page.context, user)

    def test_eherkenning_vestiging_login(self):
        """eHerkenning branch login via `eherkenning-vestiging` -> kvk + vestiging."""
        page = self._login(
            link_selector=".link--eherkenning",
            username="eherkenning-vestiging",
            password="eherkenning-vestiging",
            callback_path="/eherkenning-oidc/callback/",
            activate_zakelijk=True,
        )

        user = User.objects.get(login_type=LoginTypeChoices.eherkenning)
        self.assertEqual(user.kvk, "12345678")
        self.assertEqual(user.vestiging, "123456789012")
        self._assert_active_session(page.context, user)

    def test_eherkenning_rechtspersoon_login(self):
        """eHerkenning legal-entity login via `eherkenning-rechtspersoon`.

        This realm user carries kvk (legalSubjectID) but no `vestiging` claim, so
        the resulting user has a kvk and an empty vestiging (not branch-restricted).
        """
        page = self._login(
            link_selector=".link--eherkenning",
            username="eherkenning-rechtspersoon",
            password="eherkenning-rechtspersoon",
            callback_path="/eherkenning-oidc/callback/",
            activate_zakelijk=True,
        )

        user = User.objects.get(login_type=LoginTypeChoices.eherkenning)
        self.assertEqual(user.kvk, "12345678")
        self.assertEqual(user.vestiging, "")
        self._assert_active_session(page.context, user)

    def test_eidas_person_login(self):
        """eIDAS natural person via `eidas-person-pseudo` -> pseudo identifier.

        eIDAS requires the pseudo identifier claim (``verify_claims`` returns
        ``bool(pseudo_id)``). The realm's ``eidas-person`` user only carries a
        BSN (no pseudo), so the pseudo variant is the one that can complete
        authentication.
        """
        page = self._login(
            link_selector=".link--eidas",
            username="eidas-person-pseudo",
            password="eidas-person-pseudo",
            callback_path="/eidas-oidc/callback/",
        )

        user = User.objects.get(login_type=LoginTypeChoices.eidas_person_pseudo_id)
        self.assertEqual(user.eidas_pseudo_id, "4B75A0EA107B3D36")
        self._assert_active_session(page.context, user)

    def test_admin_oidc_login(self):
        """Admin SSO via `admin` -> staff + superuser (Registreerders), logged in."""
        page = self._login(
            link_selector=".link--oidc",
            username="admin",
            password="admin",
            # The admin flow always used the generic callback endpoint; only the
            # citizen flows have legacy per-provider callback URLs.
            callback_path="/oidc/callback/",
        )

        # Fetch by oidc_id (the sub): create_homepage() also makes a staff user,
        # so is_staff alone is ambiguous.
        user = User.objects.get(oidc_id=KEYCLOAK_ADMIN_SUB)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self._assert_active_session(page.context, user)

    # -- existing-user reuse ---------------------------------------------------
    #
    # A login for a user that already exists (matched on the per-flow identifier:
    # bsn / kvk / eidas_pseudo_id / oidc_id) must reuse that account, not create a
    # duplicate. Each test pre-creates the user, logs in, and asserts a single row
    # with the original pk.

    def _assert_reused(self, existing_pk: int, **lookup) -> None:
        self.assertEqual(User.objects.filter(**lookup).count(), 1)
        self.assertEqual(User.objects.get(**lookup).pk, existing_pk)

    def test_digid_login_reuses_existing_user(self):
        existing = DigidUserFactory(bsn="111222333")

        self._login(
            link_selector=".link--digid",
            username="testuser",
            password="testuser",
            callback_path="/digid-oidc/callback/",
        )

        self._assert_reused(existing.pk, bsn="111222333")

    def test_eherkenning_login_reuses_existing_user(self):
        existing = eHerkenningVestigingUserFactory(
            kvk="12345678", vestiging="123456789012"
        )

        self._login(
            link_selector=".link--eherkenning",
            username="eherkenning-vestiging",
            password="eherkenning-vestiging",
            callback_path="/eherkenning-oidc/callback/",
            activate_zakelijk=True,
        )

        self._assert_reused(existing.pk, kvk="12345678")

    def test_eidas_login_reuses_existing_user(self):
        existing = UserFactory(
            login_type=LoginTypeChoices.eidas_person_pseudo_id,
            eidas_pseudo_id="4B75A0EA107B3D36",
        )

        self._login(
            link_selector=".link--eidas",
            username="eidas-person-pseudo",
            password="eidas-person-pseudo",
            callback_path="/eidas-oidc/callback/",
        )

        self._assert_reused(existing.pk, eidas_pseudo_id="4B75A0EA107B3D36")

    def test_admin_login_reuses_existing_user(self):
        existing = UserFactory(
            oidc_id=KEYCLOAK_ADMIN_SUB, login_type=LoginTypeChoices.oidc
        )

        self._login(
            link_selector=".link--oidc",
            username="admin",
            password="admin",
            callback_path="/oidc/callback/",
        )

        self._assert_reused(existing.pk, oidc_id=KEYCLOAK_ADMIN_SUB)
        self.assertTrue(User.objects.get(pk=existing.pk).is_superuser)
