import tempfile
import urllib.error
from unittest import skip
from uuid import UUID

from django.conf import settings
from django.test import TestCase, override_settings

import requests
import requests_mock
from digid_eherkenning.choices import (
    AssuranceLevels,
    DigestAlgorithms,
    SignatureAlgorithms,
    XMLContentTypes,
)
from digid_eherkenning.models import DigidConfiguration, EherkenningConfiguration
from django_setup_configuration.exceptions import ConfigurationRunFailed
from mozilla_django_oidc_db.models import (
    OpenIDConnectConfig,
    UserInformationClaimsSources,
)
from privates.test import temp_private_root
from simple_certmanager.constants import CertificateTypes

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.utils.test import ClearCachesMixin

from ...bootstrap.auth import (
    AdminOIDCConfigurationStep,
    DigiDConfigurationStep,
    DigiDOIDCConfigurationStep,
    eHerkenningConfigurationStep,
    eHerkenningOIDCConfigurationStep,
)

IDENTITY_PROVIDER = "https://keycloak.local/realms/digid/"
CONTACTMOMENTEN_API_ROOT = "https://openklant.local/contactmomenten/api/v1/"

DISCOVERY_ENDPOINT_RESPONSE = {
    "issuer": IDENTITY_PROVIDER,
    "authorization_endpoint": f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
    "token_endpoint": f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
    "userinfo_endpoint": f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
    "end_session_endpoint": f"{IDENTITY_PROVIDER}protocol/openid-connect/logout",
    "jwks_uri": f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
}

DIGID_XML_METADATA_PATH = (
    "src/open_inwoner/configurations/tests/bootstrap/files/digid-metadata.xml"
)

PUBLIC_CERT_FILE = tempfile.NamedTemporaryFile()
PRIVATE_KEY_FILE = tempfile.NamedTemporaryFile()

with open(PUBLIC_CERT_FILE.name, "w") as f:
    f.write("cert")

with open(PRIVATE_KEY_FILE.name, "w") as f:
    f.write("key")


@override_settings(
    DIGID_OIDC_OIDC_RP_CLIENT_ID="client-id",
    DIGID_OIDC_OIDC_RP_CLIENT_SECRET="secret",
    DIGID_OIDC_IDENTIFIER_CLAIM_NAME="claim_name",
    DIGID_OIDC_OIDC_RP_SCOPES_LIST=["openid", "bsn", "extra_scope"],
    DIGID_OIDC_OIDC_RP_SIGN_ALGO="RS256",
    DIGID_OIDC_OIDC_RP_IDP_SIGN_KEY="key",
    DIGID_OIDC_OIDC_OP_DISCOVERY_ENDPOINT=None,
    DIGID_OIDC_OIDC_OP_JWKS_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
    DIGID_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
    DIGID_OIDC_OIDC_OP_TOKEN_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
    DIGID_OIDC_OIDC_OP_USER_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
    DIGID_OIDC_OIDC_OP_LOGOUT_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/logout",
    DIGID_OIDC_USERINFO_CLAIMS_SOURCE=UserInformationClaimsSources.id_token,
    DIGID_OIDC_ERROR_MESSAGE_MAPPING={"some_error": "Some readable error"},
    DIGID_OIDC_OIDC_KEYCLOAK_IDP_HINT="parameter",
    DIGID_OIDC_OIDC_USE_NONCE=False,
    DIGID_OIDC_OIDC_NONCE_SIZE=64,
    DIGID_OIDC_OIDC_STATE_SIZE=64,
)
class DigiDOIDCConfigurationTests(ClearCachesMixin, TestCase):
    def test_configure(self):
        DigiDOIDCConfigurationStep().configure()

        config = OpenIDConnectDigiDConfig.get_solo()

        self.assertTrue(config.enabled)
        self.assertEqual(config.oidc_rp_client_id, "client-id")
        self.assertEqual(config.oidc_rp_client_secret, "secret")
        self.assertEqual(config.identifier_claim_name, "claim_name")
        self.assertEqual(config.oidc_rp_scopes_list, ["openid", "bsn", "extra_scope"])
        self.assertEqual(config.oidc_rp_sign_algo, "RS256")
        self.assertEqual(config.oidc_rp_idp_sign_key, "key")
        self.assertEqual(config.oidc_op_discovery_endpoint, "")
        self.assertEqual(
            config.oidc_op_jwks_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.oidc_op_authorization_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
        )
        self.assertEqual(
            config.oidc_op_token_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
        )
        self.assertEqual(
            config.oidc_op_user_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
        )
        self.assertEqual(
            config.oidc_op_logout_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/logout",
        )
        self.assertEqual(
            config.userinfo_claims_source, UserInformationClaimsSources.id_token
        )
        self.assertEqual(
            config.error_message_mapping, {"some_error": "Some readable error"}
        )
        self.assertEqual(config.oidc_keycloak_idp_hint, "parameter")
        self.assertEqual(config.oidc_use_nonce, False)
        self.assertEqual(config.oidc_nonce_size, 64)
        self.assertEqual(config.oidc_state_size, 64)

    @override_settings(
        DIGID_OIDC_IDENTIFIER_CLAIM_NAME=None,
        DIGID_OIDC_OIDC_RP_SCOPES_LIST=None,
        DIGID_OIDC_OIDC_RP_SIGN_ALGO=None,
        DIGID_OIDC_OIDC_RP_IDP_SIGN_KEY=None,
        DIGID_OIDC_USERINFO_CLAIMS_SOURCE=None,
        DIGID_OIDC_ERROR_MESSAGE_MAPPING=None,
        DIGID_OIDC_OIDC_KEYCLOAK_IDP_HINT=None,
        DIGID_OIDC_OIDC_USE_NONCE=None,
        DIGID_OIDC_OIDC_NONCE_SIZE=None,
        DIGID_OIDC_OIDC_STATE_SIZE=None,
    )
    def test_configure_use_defaults(self):
        DigiDOIDCConfigurationStep().configure()

        config = OpenIDConnectDigiDConfig.get_solo()

        self.assertTrue(config.enabled)
        self.assertEqual(config.oidc_rp_client_id, "client-id")
        self.assertEqual(config.oidc_rp_client_secret, "secret")
        self.assertEqual(config.identifier_claim_name, "bsn")
        self.assertEqual(config.oidc_rp_scopes_list, ["openid", "bsn"])
        self.assertEqual(config.oidc_rp_sign_algo, "HS256")
        self.assertEqual(config.oidc_rp_idp_sign_key, "")
        self.assertEqual(config.oidc_op_discovery_endpoint, "")
        self.assertEqual(
            config.oidc_op_jwks_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.oidc_op_authorization_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
        )
        self.assertEqual(
            config.oidc_op_token_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
        )
        self.assertEqual(
            config.oidc_op_user_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
        )
        self.assertEqual(
            config.oidc_op_logout_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/logout",
        )
        self.assertEqual(
            config.userinfo_claims_source,
            UserInformationClaimsSources.userinfo_endpoint,
        )
        self.assertEqual(config.error_message_mapping, {})
        self.assertEqual(config.oidc_keycloak_idp_hint, "")
        self.assertEqual(config.oidc_use_nonce, True)
        self.assertEqual(config.oidc_nonce_size, 32)
        self.assertEqual(config.oidc_state_size, 32)

    @override_settings(
        DIGID_OIDC_OIDC_OP_DISCOVERY_ENDPOINT=IDENTITY_PROVIDER,
        DIGID_OIDC_OIDC_OP_JWKS_ENDPOINT=None,
        DIGID_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT=None,
        DIGID_OIDC_OIDC_OP_TOKEN_ENDPOINT=None,
        DIGID_OIDC_OIDC_OP_USER_ENDPOINT=None,
        DIGID_OIDC_OIDC_OP_LOGOUT_ENDPOINT=None,
    )
    @requests_mock.Mocker()
    def test_configure_use_discovery_endpoint(self, m):
        m.get(
            f"{IDENTITY_PROVIDER}.well-known/openid-configuration",
            json=DISCOVERY_ENDPOINT_RESPONSE,
        )

        DigiDOIDCConfigurationStep().configure()

        config = OpenIDConnectDigiDConfig.get_solo()

        self.assertTrue(config.enabled)
        self.assertEqual(config.oidc_op_discovery_endpoint, IDENTITY_PROVIDER)
        self.assertEqual(
            config.oidc_op_jwks_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.oidc_op_authorization_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
        )
        self.assertEqual(
            config.oidc_op_token_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
        )
        self.assertEqual(
            config.oidc_op_user_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
        )
        self.assertEqual(
            config.oidc_op_logout_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/logout",
        )

    @override_settings(
        DIGID_OIDC_OIDC_OP_DISCOVERY_ENDPOINT=IDENTITY_PROVIDER,
        DIGID_OIDC_OIDC_OP_JWKS_ENDPOINT=None,
        DIGID_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT=None,
        DIGID_OIDC_OIDC_OP_TOKEN_ENDPOINT=None,
        DIGID_OIDC_OIDC_OP_USER_ENDPOINT=None,
        DIGID_OIDC_OIDC_OP_LOGOUT_ENDPOINT=None,
    )
    @requests_mock.Mocker()
    def test_configure_failure(self, m):
        mock_kwargs = (
            {"exc": requests.ConnectTimeout},
            {"exc": requests.ConnectionError},
            {"status_code": 404},
            {"status_code": 403},
            {"status_code": 500},
        )
        for mock_config in mock_kwargs:
            with self.subTest(mock=mock_config):
                m.get(
                    f"{IDENTITY_PROVIDER}.well-known/openid-configuration",
                    **mock_config,
                )

                with self.assertRaises(ConfigurationRunFailed):
                    DigiDOIDCConfigurationStep().configure()

                self.assertFalse(OpenIDConnectDigiDConfig.get_solo().enabled)

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_ok(self, m):
        raise NotImplementedError

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_failures(self, m):
        raise NotImplementedError

    def test_is_configured(self):
        config = DigiDOIDCConfigurationStep()

        self.assertFalse(config.is_configured())

        config.configure()

        self.assertTrue(config.is_configured())


@override_settings(
    EHERKENNING_OIDC_OIDC_RP_CLIENT_ID="client-id",
    EHERKENNING_OIDC_OIDC_RP_CLIENT_SECRET="secret",
    EHERKENNING_OIDC_IDENTIFIER_CLAIM_NAME="claim_name",
    EHERKENNING_OIDC_OIDC_RP_SCOPES_LIST=["openid", "kvk", "extra_scope"],
    EHERKENNING_OIDC_OIDC_RP_SIGN_ALGO="RS256",
    EHERKENNING_OIDC_OIDC_RP_IDP_SIGN_KEY="key",
    EHERKENNING_OIDC_OIDC_OP_DISCOVERY_ENDPOINT=None,
    EHERKENNING_OIDC_OIDC_OP_JWKS_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
    EHERKENNING_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
    EHERKENNING_OIDC_OIDC_OP_TOKEN_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
    EHERKENNING_OIDC_OIDC_OP_USER_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
    EHERKENNING_OIDC_OIDC_OP_LOGOUT_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/logout",
    EHERKENNING_OIDC_USERINFO_CLAIMS_SOURCE=UserInformationClaimsSources.id_token,
    EHERKENNING_OIDC_ERROR_MESSAGE_MAPPING={"some_error": "Some readable error"},
    EHERKENNING_OIDC_OIDC_KEYCLOAK_IDP_HINT="parameter",
    EHERKENNING_OIDC_OIDC_USE_NONCE=False,
    EHERKENNING_OIDC_OIDC_NONCE_SIZE=64,
    EHERKENNING_OIDC_OIDC_STATE_SIZE=64,
)
class eHerkenningOIDCConfigurationTests(ClearCachesMixin, TestCase):
    def test_configure(self):
        eHerkenningOIDCConfigurationStep().configure()

        config = OpenIDConnectEHerkenningConfig.get_solo()

        self.assertTrue(config.enabled)
        self.assertEqual(config.oidc_rp_client_id, "client-id")
        self.assertEqual(config.oidc_rp_client_secret, "secret")
        self.assertEqual(config.identifier_claim_name, "claim_name")
        self.assertEqual(config.oidc_rp_scopes_list, ["openid", "kvk", "extra_scope"])
        self.assertEqual(config.oidc_rp_sign_algo, "RS256")
        self.assertEqual(config.oidc_rp_idp_sign_key, "key")
        self.assertEqual(config.oidc_op_discovery_endpoint, "")
        self.assertEqual(
            config.oidc_op_jwks_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.oidc_op_authorization_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
        )
        self.assertEqual(
            config.oidc_op_token_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
        )
        self.assertEqual(
            config.oidc_op_user_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
        )
        self.assertEqual(
            config.oidc_op_logout_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/logout",
        )
        self.assertEqual(
            config.userinfo_claims_source, UserInformationClaimsSources.id_token
        )
        self.assertEqual(
            config.error_message_mapping, {"some_error": "Some readable error"}
        )
        self.assertEqual(config.oidc_keycloak_idp_hint, "parameter")
        self.assertEqual(config.oidc_use_nonce, False)
        self.assertEqual(config.oidc_nonce_size, 64)
        self.assertEqual(config.oidc_state_size, 64)

    @override_settings(
        EHERKENNING_OIDC_IDENTIFIER_CLAIM_NAME=None,
        EHERKENNING_OIDC_OIDC_RP_SCOPES_LIST=None,
        EHERKENNING_OIDC_OIDC_RP_SIGN_ALGO=None,
        EHERKENNING_OIDC_OIDC_RP_IDP_SIGN_KEY=None,
        EHERKENNING_OIDC_USERINFO_CLAIMS_SOURCE=None,
        EHERKENNING_OIDC_ERROR_MESSAGE_MAPPING=None,
        EHERKENNING_OIDC_OIDC_KEYCLOAK_IDP_HINT=None,
        EHERKENNING_OIDC_OIDC_USE_NONCE=None,
        EHERKENNING_OIDC_OIDC_NONCE_SIZE=None,
        EHERKENNING_OIDC_OIDC_STATE_SIZE=None,
    )
    def test_configure_use_defaults(self):
        eHerkenningOIDCConfigurationStep().configure()

        config = OpenIDConnectEHerkenningConfig.get_solo()

        self.assertTrue(config.enabled)
        self.assertEqual(config.oidc_rp_client_id, "client-id")
        self.assertEqual(config.oidc_rp_client_secret, "secret")
        self.assertEqual(config.identifier_claim_name, "kvk")
        self.assertEqual(config.oidc_rp_scopes_list, ["openid", "kvk"])
        self.assertEqual(config.oidc_rp_sign_algo, "HS256")
        self.assertEqual(config.oidc_rp_idp_sign_key, "")
        self.assertEqual(config.oidc_op_discovery_endpoint, "")
        self.assertEqual(
            config.oidc_op_jwks_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.oidc_op_authorization_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
        )
        self.assertEqual(
            config.oidc_op_token_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
        )
        self.assertEqual(
            config.oidc_op_user_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
        )
        self.assertEqual(
            config.oidc_op_logout_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/logout",
        )
        self.assertEqual(
            config.userinfo_claims_source,
            UserInformationClaimsSources.userinfo_endpoint,
        )
        self.assertEqual(config.error_message_mapping, {})
        self.assertEqual(config.oidc_keycloak_idp_hint, "")
        self.assertEqual(config.oidc_use_nonce, True)
        self.assertEqual(config.oidc_nonce_size, 32)
        self.assertEqual(config.oidc_state_size, 32)

    @override_settings(
        EHERKENNING_OIDC_OIDC_OP_DISCOVERY_ENDPOINT=IDENTITY_PROVIDER,
        EHERKENNING_OIDC_OIDC_OP_JWKS_ENDPOINT=None,
        EHERKENNING_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT=None,
        EHERKENNING_OIDC_OIDC_OP_TOKEN_ENDPOINT=None,
        EHERKENNING_OIDC_OIDC_OP_USER_ENDPOINT=None,
        EHERKENNING_OIDC_OIDC_OP_LOGOUT_ENDPOINT=None,
    )
    @requests_mock.Mocker()
    def test_configure_use_discovery_endpoint(self, m):
        m.get(
            f"{IDENTITY_PROVIDER}.well-known/openid-configuration",
            json=DISCOVERY_ENDPOINT_RESPONSE,
        )

        eHerkenningOIDCConfigurationStep().configure()

        config = OpenIDConnectEHerkenningConfig.get_solo()

        self.assertTrue(config.enabled)
        self.assertEqual(config.oidc_op_discovery_endpoint, IDENTITY_PROVIDER)
        self.assertEqual(
            config.oidc_op_jwks_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.oidc_op_authorization_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
        )
        self.assertEqual(
            config.oidc_op_token_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
        )
        self.assertEqual(
            config.oidc_op_user_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
        )
        self.assertEqual(
            config.oidc_op_logout_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/logout",
        )

    @override_settings(
        EHERKENNING_OIDC_OIDC_OP_DISCOVERY_ENDPOINT=IDENTITY_PROVIDER,
        EHERKENNING_OIDC_OIDC_OP_JWKS_ENDPOINT=None,
        EHERKENNING_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT=None,
        EHERKENNING_OIDC_OIDC_OP_TOKEN_ENDPOINT=None,
        EHERKENNING_OIDC_OIDC_OP_USER_ENDPOINT=None,
        EHERKENNING_OIDC_OIDC_OP_LOGOUT_ENDPOINT=None,
    )
    @requests_mock.Mocker()
    def test_configure_failure(self, m):
        mock_kwargs = (
            {"exc": requests.ConnectTimeout},
            {"exc": requests.ConnectionError},
            {"status_code": 404},
            {"status_code": 403},
            {"status_code": 500},
        )
        for mock_config in mock_kwargs:
            with self.subTest(mock=mock_config):
                m.get(
                    f"{IDENTITY_PROVIDER}.well-known/openid-configuration",
                    **mock_config,
                )

                with self.assertRaises(ConfigurationRunFailed):
                    eHerkenningOIDCConfigurationStep().configure()

                self.assertFalse(OpenIDConnectEHerkenningConfig.get_solo().enabled)

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_ok(self, m):
        raise NotImplementedError

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_failures(self, m):
        raise NotImplementedError

    def test_is_configured(self):
        config = eHerkenningOIDCConfigurationStep()

        self.assertFalse(config.is_configured())

        config.configure()

        self.assertTrue(config.is_configured())


@override_settings(
    ADMIN_OIDC_OIDC_RP_CLIENT_ID="client-id",
    ADMIN_OIDC_OIDC_RP_CLIENT_SECRET="secret",
    ADMIN_OIDC_OIDC_RP_SCOPES_LIST=["open_id", "email", "profile", "extra_scope"],
    ADMIN_OIDC_OIDC_RP_SIGN_ALGO="RS256",
    ADMIN_OIDC_OIDC_RP_IDP_SIGN_KEY="key",
    ADMIN_OIDC_OIDC_OP_DISCOVERY_ENDPOINT=None,
    ADMIN_OIDC_OIDC_OP_JWKS_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
    ADMIN_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
    ADMIN_OIDC_OIDC_OP_TOKEN_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
    ADMIN_OIDC_OIDC_OP_USER_ENDPOINT=f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
    ADMIN_OIDC_USERNAME_CLAIM=["claim_name"],
    ADMIN_OIDC_GROUPS_CLAIM=["groups_claim_name"],
    ADMIN_OIDC_CLAIM_MAPPING={"first_name": ["given_name"]},
    ADMIN_OIDC_SYNC_GROUPS=False,
    ADMIN_OIDC_SYNC_GROUPS_GLOB_PATTERN="local.groups.*",
    ADMIN_OIDC_DEFAULT_GROUPS=["Admins", "Read-only"],
    ADMIN_OIDC_MAKE_USERS_STAFF=True,
    ADMIN_OIDC_SUPERUSER_GROUP_NAMES=["superuser"],
    ADMIN_OIDC_OIDC_USE_NONCE=False,
    ADMIN_OIDC_OIDC_NONCE_SIZE=48,
    ADMIN_OIDC_OIDC_STATE_SIZE=48,
    ADMIN_OIDC_USERINFO_CLAIMS_SOURCE=UserInformationClaimsSources.id_token,
)
class AdminOIDCConfigurationTests(ClearCachesMixin, TestCase):
    def test_configure(self):
        AdminOIDCConfigurationStep().configure()

        config = OpenIDConnectConfig.get_solo()

        self.assertTrue(config.enabled)
        self.assertEqual(config.oidc_rp_client_id, "client-id")
        self.assertEqual(config.oidc_rp_client_secret, "secret")
        self.assertEqual(
            config.oidc_rp_scopes_list, ["open_id", "email", "profile", "extra_scope"]
        )
        self.assertEqual(config.oidc_rp_sign_algo, "RS256")
        self.assertEqual(config.oidc_rp_idp_sign_key, "key")
        self.assertEqual(config.oidc_op_discovery_endpoint, "")
        self.assertEqual(
            config.oidc_op_jwks_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.oidc_op_authorization_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
        )
        self.assertEqual(
            config.oidc_op_token_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
        )
        self.assertEqual(
            config.oidc_op_user_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
        )
        self.assertEqual(config.username_claim, ["claim_name"])
        self.assertEqual(config.groups_claim, ["groups_claim_name"])
        self.assertEqual(config.claim_mapping, {"first_name": ["given_name"]})
        self.assertEqual(config.sync_groups, False)
        self.assertEqual(config.sync_groups_glob_pattern, "local.groups.*")
        self.assertEqual(
            list(group.name for group in config.default_groups.all()),
            ["Admins", "Read-only"],
        )
        self.assertEqual(config.make_users_staff, True)
        self.assertEqual(config.superuser_group_names, ["superuser"])
        self.assertEqual(config.oidc_use_nonce, False)
        self.assertEqual(config.oidc_nonce_size, 48)
        self.assertEqual(config.oidc_state_size, 48)
        self.assertEqual(
            config.userinfo_claims_source, UserInformationClaimsSources.id_token
        )

    @override_settings(
        ADMIN_OIDC_OIDC_RP_SCOPES_LIST=None,
        ADMIN_OIDC_OIDC_RP_SIGN_ALGO=None,
        ADMIN_OIDC_OIDC_RP_IDP_SIGN_KEY=None,
        ADMIN_OIDC_USERNAME_CLAIM=None,
        ADMIN_OIDC_CLAIM_MAPPING=None,
        ADMIN_OIDC_SYNC_GROUPS=None,
        ADMIN_OIDC_SYNC_GROUPS_GLOB_PATTERN=None,
        ADMIN_OIDC_MAKE_USERS_STAFF=None,
        ADMIN_OIDC_OIDC_USE_NONCE=None,
        ADMIN_OIDC_OIDC_NONCE_SIZE=None,
        ADMIN_OIDC_OIDC_STATE_SIZE=None,
        ADMIN_OIDC_USERINFO_CLAIMS_SOURCE=None,
    )
    def test_configure_use_defaults(self):
        AdminOIDCConfigurationStep().configure()

        config = OpenIDConnectConfig.get_solo()

        self.assertTrue(config.enabled)
        self.assertEqual(config.oidc_rp_client_id, "client-id")
        self.assertEqual(config.oidc_rp_client_secret, "secret")
        self.assertEqual(config.oidc_rp_scopes_list, ["openid", "email", "profile"])
        self.assertEqual(config.oidc_rp_sign_algo, "HS256")
        self.assertEqual(config.oidc_rp_idp_sign_key, "")
        self.assertEqual(config.oidc_op_discovery_endpoint, "")
        self.assertEqual(
            config.oidc_op_jwks_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.oidc_op_authorization_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
        )
        self.assertEqual(
            config.oidc_op_token_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
        )
        self.assertEqual(
            config.oidc_op_user_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
        )
        self.assertEqual(config.username_claim, ["sub"])
        self.assertEqual(config.groups_claim, ["groups_claim_name"])
        self.assertEqual(
            config.claim_mapping,
            {"last_name": ["family_name"], "first_name": ["given_name"]},
        )
        self.assertEqual(config.sync_groups, True)
        self.assertEqual(config.sync_groups_glob_pattern, "*")
        self.assertEqual(
            list(group.name for group in config.default_groups.all()),
            ["Admins", "Read-only"],
        )
        self.assertEqual(config.make_users_staff, False)
        self.assertEqual(config.superuser_group_names, ["superuser"])
        self.assertEqual(config.oidc_use_nonce, True)
        self.assertEqual(config.oidc_nonce_size, 32)
        self.assertEqual(config.oidc_state_size, 32)
        self.assertEqual(
            config.userinfo_claims_source,
            UserInformationClaimsSources.userinfo_endpoint,
        )

    @override_settings(
        ADMIN_OIDC_OIDC_OP_DISCOVERY_ENDPOINT=IDENTITY_PROVIDER,
        ADMIN_OIDC_OIDC_OP_JWKS_ENDPOINT=None,
        ADMIN_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT=None,
        ADMIN_OIDC_OIDC_OP_TOKEN_ENDPOINT=None,
        ADMIN_OIDC_OIDC_OP_USER_ENDPOINT=None,
    )
    @requests_mock.Mocker()
    def test_configure_use_discovery_endpoint(self, m):
        m.get(
            f"{IDENTITY_PROVIDER}.well-known/openid-configuration",
            json=DISCOVERY_ENDPOINT_RESPONSE,
        )

        AdminOIDCConfigurationStep().configure()

        config = OpenIDConnectConfig.get_solo()

        self.assertTrue(config.enabled)
        self.assertEqual(config.oidc_op_discovery_endpoint, IDENTITY_PROVIDER)
        self.assertEqual(
            config.oidc_op_jwks_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/certs",
        )
        self.assertEqual(
            config.oidc_op_authorization_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/auth",
        )
        self.assertEqual(
            config.oidc_op_token_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/token",
        )
        self.assertEqual(
            config.oidc_op_user_endpoint,
            f"{IDENTITY_PROVIDER}protocol/openid-connect/userinfo",
        )

    @override_settings(
        ADMIN_OIDC_OIDC_OP_DISCOVERY_ENDPOINT=IDENTITY_PROVIDER,
        ADMIN_OIDC_OIDC_OP_JWKS_ENDPOINT=None,
        ADMIN_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT=None,
        ADMIN_OIDC_OIDC_OP_TOKEN_ENDPOINT=None,
        ADMIN_OIDC_OIDC_OP_USER_ENDPOINT=None,
    )
    @requests_mock.Mocker()
    def test_configure_failure(self, m):
        mock_kwargs = (
            {"exc": requests.ConnectTimeout},
            {"exc": requests.ConnectionError},
            {"status_code": 404},
            {"status_code": 403},
            {"status_code": 500},
        )
        for mock_config in mock_kwargs:
            with self.subTest(mock=mock_config):
                m.get(
                    f"{IDENTITY_PROVIDER}.well-known/openid-configuration",
                    **mock_config,
                )

                with self.assertRaises(ConfigurationRunFailed):
                    AdminOIDCConfigurationStep().configure()

                self.assertFalse(OpenIDConnectConfig.get_solo().enabled)

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_ok(self, m):
        raise NotImplementedError

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_failures(self, m):
        raise NotImplementedError

    def test_is_configured(self):
        config = AdminOIDCConfigurationStep()

        self.assertFalse(config.is_configured())

        config.configure()

        self.assertTrue(config.is_configured())


@temp_private_root()
@override_settings(
    DIGID_CERTIFICATE_LABEL="DigiD certificate",
    DIGID_CERTIFICATE_TYPE=CertificateTypes.key_pair,
    DIGID_CERTIFICATE_PUBLIC_CERTIFICATE=PUBLIC_CERT_FILE.name,
    DIGID_CERTIFICATE_PRIVATE_KEY=PRIVATE_KEY_FILE.name,
    DIGID_METADATA_FILE_SOURCE="http://metadata.local/file.xml",
    DIGID_ENTITY_ID="1234",
    DIGID_BASE_URL="http://digid.local",
    DIGID_SERVICE_NAME="OIP",
    DIGID_SERVICE_DESCRIPTION="Open Inwoner",
    DIGID_WANT_ASSERTIONS_SIGNED=False,
    DIGID_WANT_ASSERTIONS_ENCRYPTED=True,
    DIGID_ARTIFACT_RESOLVE_CONTENT_TYPE=XMLContentTypes.text_xml,
    DIGID_KEY_PASSPHRASE="foo",
    DIGID_SIGNATURE_ALGORITHM=SignatureAlgorithms.dsa_sha1,
    DIGID_DIGEST_ALGORITHM=DigestAlgorithms.sha512,
    DIGID_TECHNICAL_CONTACT_PERSON_TELEPHONE="0612345678",
    DIGID_TECHNICAL_CONTACT_PERSON_EMAIL="foo@bar.org",
    DIGID_ORGANIZATION_URL="http://open-inwoner.local",
    DIGID_ORGANIZATION_NAME="Open Inwoner",
    DIGID_ATTRIBUTE_CONSUMING_SERVICE_INDEX="2",
    DIGID_REQUESTED_ATTRIBUTES=[
        {"name": "bsn", "required": True},
        {"name": "email", "required": False},
    ],
    DIGID_SLO=False,
)
class DigiDConfigurationTests(ClearCachesMixin, TestCase):
    @requests_mock.Mocker()
    def test_configure(self, m):
        with open(DIGID_XML_METADATA_PATH, "rb") as f:
            m.get("http://metadata.local/file.xml", content=f.read())

            DigiDConfigurationStep().configure()

        config = DigidConfiguration.get_solo()

        self.assertEqual(config.certificate.label, "DigiD certificate")
        self.assertEqual(config.certificate.type, CertificateTypes.key_pair)

        public_cert = config.certificate.public_certificate
        private_key = config.certificate.private_key

        self.assertTrue(public_cert.path.startswith(settings.PRIVATE_MEDIA_ROOT))
        self.assertEqual(public_cert.file.read(), b"cert")
        self.assertTrue(private_key.path.startswith(settings.PRIVATE_MEDIA_ROOT))
        self.assertEqual(private_key.file.read(), b"key")

        self.assertEqual(config.key_passphrase, "foo")
        self.assertEqual(config.metadata_file_source, "http://metadata.local/file.xml")
        self.assertEqual(
            config.idp_service_entity_id,
            "https://was-preprod1.digid.nl/saml/idp/metadata",
        )
        self.assertTrue(config.idp_metadata_file.path.endswith(".xml"))
        self.assertEqual(config.entity_id, "1234")
        self.assertEqual(config.base_url, "http://digid.local")
        self.assertEqual(config.service_name, "OIP")
        self.assertEqual(config.service_description, "Open Inwoner")
        self.assertEqual(config.want_assertions_signed, False)
        self.assertEqual(config.want_assertions_encrypted, True)
        self.assertEqual(config.artifact_resolve_content_type, XMLContentTypes.text_xml)
        self.assertEqual(config.signature_algorithm, SignatureAlgorithms.dsa_sha1)
        self.assertEqual(config.digest_algorithm, DigestAlgorithms.sha512)
        self.assertEqual(config.technical_contact_person_telephone, "0612345678")
        self.assertEqual(config.technical_contact_person_email, "foo@bar.org")
        self.assertEqual(config.organization_url, "http://open-inwoner.local")
        self.assertEqual(config.organization_name, "Open Inwoner")
        self.assertEqual(config.attribute_consuming_service_index, "2")
        self.assertEqual(
            config.requested_attributes,
            [{"name": "bsn", "required": True}, {"name": "email", "required": False}],
        )
        self.assertEqual(config.slo, False)

    @requests_mock.Mocker()
    @override_settings(
        DIGID_WANT_ASSERTIONS_SIGNED=None,
        DIGID_WANT_ASSERTIONS_ENCRYPTED=None,
        DIGID_ARTIFACT_RESOLVE_CONTENT_TYPE=None,
        DIGID_KEY_PASSPHRASE=None,
        DIGID_SIGNATURE_ALGORITHM=None,
        DIGID_DIGEST_ALGORITHM=None,
        DIGID_ATTRIBUTE_CONSUMING_SERVICE_INDEX=None,
        DIGID_REQUESTED_ATTRIBUTES=None,
        DIGID_SLO=None,
    )
    def test_configure_use_defaults(self, m):
        with open(DIGID_XML_METADATA_PATH, "rb") as f:
            m.get("http://metadata.local/file.xml", content=f.read())

            DigiDConfigurationStep().configure()

        config = DigidConfiguration.get_solo()

        self.assertEqual(config.key_passphrase, "")
        self.assertEqual(config.want_assertions_signed, True)
        self.assertEqual(config.want_assertions_encrypted, False)
        self.assertEqual(config.artifact_resolve_content_type, XMLContentTypes.soap_xml)
        self.assertEqual(config.signature_algorithm, SignatureAlgorithms.rsa_sha1)
        self.assertEqual(config.digest_algorithm, DigestAlgorithms.sha1)
        self.assertEqual(config.attribute_consuming_service_index, "1")
        self.assertEqual(
            config.requested_attributes,
            [{"name": "bsn", "required": True}],
        )
        self.assertEqual(config.slo, True)

    @requests_mock.Mocker()
    def test_configure_failure(self, m):
        exceptions = (urllib.error.HTTPError, urllib.error.URLError)
        for exception in exceptions:
            with self.subTest(exception=exception):
                m.get("http://metadata.local/file.xml", exc=exception)
                with self.assertRaises(ConfigurationRunFailed):
                    DigiDConfigurationStep().configure()

                config = DigidConfiguration.get_solo()

                self.assertFalse(config.certificate, None)

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_ok(self, m):
        raise NotImplementedError

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_failures(self, m):
        raise NotImplementedError

    @requests_mock.Mocker()
    def test_is_configured(self, m):
        config = DigiDConfigurationStep()

        self.assertFalse(config.is_configured())

        with open(DIGID_XML_METADATA_PATH, "rb") as f:
            m.get("http://metadata.local/file.xml", content=f.read())
            config.configure()

        self.assertTrue(config.is_configured())


@temp_private_root()
@override_settings(
    EHERKENNING_CERTIFICATE_LABEL="eHerkenning certificate",
    EHERKENNING_CERTIFICATE_TYPE=CertificateTypes.key_pair,
    EHERKENNING_CERTIFICATE_PUBLIC_CERTIFICATE=PUBLIC_CERT_FILE.name,
    EHERKENNING_CERTIFICATE_PRIVATE_KEY=PRIVATE_KEY_FILE.name,
    EHERKENNING_METADATA_FILE_SOURCE="http://metadata.local/file.xml",
    EHERKENNING_ENTITY_ID="1234",
    EHERKENNING_BASE_URL="http://eherkenning.local",
    EHERKENNING_SERVICE_NAME="OIP",
    EHERKENNING_SERVICE_DESCRIPTION="Open Inwoner",
    EHERKENNING_WANT_ASSERTIONS_SIGNED=False,
    EHERKENNING_WANT_ASSERTIONS_ENCRYPTED=True,
    EHERKENNING_ARTIFACT_RESOLVE_CONTENT_TYPE=XMLContentTypes.text_xml,
    EHERKENNING_KEY_PASSPHRASE="foo",
    EHERKENNING_SIGNATURE_ALGORITHM=SignatureAlgorithms.dsa_sha1,
    EHERKENNING_DIGEST_ALGORITHM=DigestAlgorithms.sha512,
    EHERKENNING_TECHNICAL_CONTACT_PERSON_TELEPHONE="0612345678",
    EHERKENNING_TECHNICAL_CONTACT_PERSON_EMAIL="foo@bar.org",
    EHERKENNING_ORGANIZATION_URL="http://open-inwoner.local",
    EHERKENNING_ORGANIZATION_NAME="Open Inwoner",
    EHERKENNING_EH_LOA=AssuranceLevels.high,
    EHERKENNING_EH_ATTRIBUTE_CONSUMING_SERVICE_INDEX="9053",
    EHERKENNING_EH_REQUESTED_ATTRIBUTES=[{"name": "kvk", "required": True}],
    EHERKENNING_EH_SERVICE_UUID="a89ca0cc-e0db-417a-993e-1a54300a3537",
    EHERKENNING_EH_SERVICE_INSTANCE_UUID="feed1712-4d97-4aaf-92e1-607ebd65263d",
    EHERKENNING_EIDAS_LOA=AssuranceLevels.high,
    EHERKENNING_EIDAS_ATTRIBUTE_CONSUMING_SERVICE_INDEX="9054",
    EHERKENNING_EIDAS_REQUESTED_ATTRIBUTES=[{"name": "kvk", "required": True}],
    EHERKENNING_EIDAS_SERVICE_UUID="59d0bfe8-10e6-4830-bc2b-c7d895a16f31",
    EHERKENNING_EIDAS_SERVICE_INSTANCE_UUID="c1cd3bfa-cd5e-4f68-8991-7a87c137f8f0",
    EHERKENNING_OIN="11111222223333344444",
    EHERKENNING_NO_EIDAS=True,
    EHERKENNING_PRIVACY_POLICY="http://privacy-policy.local/",
    EHERKENNING_MAKELAAR_ID="44444333332222211111",
    EHERKENNING_SERVICE_LANGUAGE="en",
)
class eHerkenningConfigurationTests(ClearCachesMixin, TestCase):
    @requests_mock.Mocker()
    def test_configure(self, m):
        with open(DIGID_XML_METADATA_PATH, "rb") as f:
            m.get("http://metadata.local/file.xml", content=f.read())

            eHerkenningConfigurationStep().configure()

        config = EherkenningConfiguration.get_solo()

        self.assertEqual(config.certificate.label, "eHerkenning certificate")
        self.assertEqual(config.certificate.type, CertificateTypes.key_pair)

        public_cert = config.certificate.public_certificate
        private_key = config.certificate.private_key

        self.assertTrue(public_cert.path.startswith(settings.PRIVATE_MEDIA_ROOT))
        self.assertEqual(public_cert.file.read(), b"cert")
        self.assertTrue(private_key.path.startswith(settings.PRIVATE_MEDIA_ROOT))
        self.assertEqual(private_key.file.read(), b"key")

        self.assertEqual(config.key_passphrase, "foo")
        self.assertEqual(config.metadata_file_source, "http://metadata.local/file.xml")
        self.assertEqual(
            config.idp_service_entity_id,
            "https://was-preprod1.digid.nl/saml/idp/metadata",
        )
        self.assertTrue(config.idp_metadata_file.path.endswith(".xml"))
        self.assertEqual(config.entity_id, "1234")
        self.assertEqual(config.base_url, "http://eherkenning.local")
        self.assertEqual(config.service_name, "OIP")
        self.assertEqual(config.service_description, "Open Inwoner")
        self.assertEqual(config.want_assertions_signed, False)
        self.assertEqual(config.want_assertions_encrypted, True)
        self.assertEqual(config.artifact_resolve_content_type, XMLContentTypes.text_xml)
        self.assertEqual(config.signature_algorithm, SignatureAlgorithms.dsa_sha1)
        self.assertEqual(config.digest_algorithm, DigestAlgorithms.sha512)
        self.assertEqual(config.technical_contact_person_telephone, "0612345678")
        self.assertEqual(config.technical_contact_person_email, "foo@bar.org")
        self.assertEqual(config.organization_url, "http://open-inwoner.local")
        self.assertEqual(config.organization_name, "Open Inwoner")
        self.assertEqual(config.eh_loa, AssuranceLevels.high)
        self.assertEqual(config.eh_attribute_consuming_service_index, "9053")
        self.assertEqual(
            config.eh_requested_attributes, [{"name": "kvk", "required": True}]
        )
        self.assertEqual(
            config.eh_service_uuid, UUID("a89ca0cc-e0db-417a-993e-1a54300a3537")
        )
        self.assertEqual(
            config.eh_service_instance_uuid,
            UUID("feed1712-4d97-4aaf-92e1-607ebd65263d"),
        )
        self.assertEqual(config.eidas_loa, AssuranceLevels.high)
        self.assertEqual(config.eidas_attribute_consuming_service_index, "9054")
        self.assertEqual(
            config.eidas_requested_attributes, [{"name": "kvk", "required": True}]
        )
        self.assertEqual(
            config.eidas_service_uuid, UUID("59d0bfe8-10e6-4830-bc2b-c7d895a16f31")
        )
        self.assertEqual(
            config.eidas_service_instance_uuid,
            UUID("c1cd3bfa-cd5e-4f68-8991-7a87c137f8f0"),
        )
        self.assertEqual(config.oin, "11111222223333344444")
        self.assertEqual(config.no_eidas, True)
        self.assertEqual(config.privacy_policy, "http://privacy-policy.local/")
        self.assertEqual(config.makelaar_id, "44444333332222211111")
        self.assertEqual(config.service_language, "en")

    @requests_mock.Mocker()
    @override_settings(
        EHERKENNING_WANT_ASSERTIONS_SIGNED=None,
        EHERKENNING_WANT_ASSERTIONS_ENCRYPTED=None,
        EHERKENNING_ARTIFACT_RESOLVE_CONTENT_TYPE=None,
        EHERKENNING_KEY_PASSPHRASE=None,
        EHERKENNING_SIGNATURE_ALGORITHM=None,
        EHERKENNING_DIGEST_ALGORITHM=None,
        EHERKENNING_EH_LOA=None,
        EHERKENNING_EH_ATTRIBUTE_CONSUMING_SERVICE_INDEX=None,
        EHERKENNING_EH_SERVICE_UUID=None,
        EHERKENNING_EH_SERVICE_INSTANCE_UUID=None,
        EHERKENNING_EIDAS_LOA=None,
        EHERKENNING_EIDAS_ATTRIBUTE_CONSUMING_SERVICE_INDEX=None,
        EHERKENNING_EIDAS_SERVICE_UUID=None,
        EHERKENNING_EIDAS_SERVICE_INSTANCE_UUID=None,
        EHERKENNING_NO_EIDAS=None,
        EHERKENNING_SERVICE_LANGUAGE=None,
    )
    def test_configure_use_defaults(self, m):
        with open(DIGID_XML_METADATA_PATH, "rb") as f:
            m.get("http://metadata.local/file.xml", content=f.read())

            eHerkenningConfigurationStep().configure()

        config = EherkenningConfiguration.get_solo()

        self.assertEqual(config.want_assertions_signed, True)
        self.assertEqual(config.want_assertions_encrypted, False)
        self.assertEqual(config.artifact_resolve_content_type, XMLContentTypes.soap_xml)
        self.assertEqual(config.key_passphrase, "")
        self.assertEqual(config.signature_algorithm, SignatureAlgorithms.rsa_sha1)
        self.assertEqual(config.digest_algorithm, DigestAlgorithms.sha1)
        self.assertEqual(config.eh_loa, AssuranceLevels.substantial)
        self.assertEqual(config.eh_attribute_consuming_service_index, "9052")
        self.assertIsInstance(config.eh_service_uuid, UUID)
        self.assertIsInstance(config.eh_service_instance_uuid, UUID)
        self.assertEqual(config.eidas_loa, AssuranceLevels.substantial)
        self.assertEqual(config.eidas_attribute_consuming_service_index, "9053")
        self.assertIsInstance(config.eidas_service_uuid, UUID)
        self.assertIsInstance(config.eidas_service_instance_uuid, UUID)
        self.assertEqual(config.no_eidas, False)
        self.assertEqual(config.service_language, "nl")

    @requests_mock.Mocker()
    def test_configure_failure(self, m):
        exceptions = (urllib.error.HTTPError, urllib.error.URLError)
        for exception in exceptions:
            with self.subTest(exception=exception):
                m.get("http://metadata.local/file.xml", exc=exception)
                with self.assertRaises(ConfigurationRunFailed):
                    eHerkenningConfigurationStep().configure()

                config = EherkenningConfiguration.get_solo()

                self.assertFalse(config.certificate, None)

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_ok(self, m):
        raise NotImplementedError

    @skip("Testing config for DigiD OIDC is not implemented yet")
    @requests_mock.Mocker()
    def test_configuration_check_failures(self, m):
        raise NotImplementedError

    @requests_mock.Mocker()
    def test_is_configured(self, m):
        config = eHerkenningConfigurationStep()

        self.assertFalse(config.is_configured())

        with open(DIGID_XML_METADATA_PATH, "rb") as f:
            m.get("http://metadata.local/file.xml", content=f.read())

            config.configure()

        self.assertTrue(config.is_configured())
