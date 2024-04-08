from unittest import skip

from django.test import TestCase, override_settings

import requests
import requests_mock
from django_setup_configuration.exceptions import ConfigurationRunFailed
from mozilla_django_oidc_db.models import (
    OpenIDConnectConfig,
    UserInformationClaimsSources,
)

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.utils.test import ClearCachesMixin

from ...bootstrap.auth import (
    AdminOIDCConfigurationStep,
    DigiDOIDCConfigurationStep,
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

    @override_settings(
        DIGID_OIDC_IDENTIFIER_CLAIM_NAME=None,
        DIGID_OIDC_OIDC_RP_SCOPES_LIST=None,
        DIGID_OIDC_OIDC_RP_SIGN_ALGO=None,
        DIGID_OIDC_OIDC_RP_IDP_SIGN_KEY=None,
        DIGID_OIDC_USERINFO_CLAIMS_SOURCE=None,
        DIGID_OIDC_ERROR_MESSAGE_MAPPING=None,
        DIGID_OIDC_OIDC_KEYCLOAK_IDP_HINT=None,
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

    @override_settings(
        EHERKENNING_OIDC_IDENTIFIER_CLAIM_NAME=None,
        EHERKENNING_OIDC_OIDC_RP_SCOPES_LIST=None,
        EHERKENNING_OIDC_OIDC_RP_SIGN_ALGO=None,
        EHERKENNING_OIDC_OIDC_RP_IDP_SIGN_KEY=None,
        EHERKENNING_OIDC_USERINFO_CLAIMS_SOURCE=None,
        EHERKENNING_OIDC_ERROR_MESSAGE_MAPPING=None,
        EHERKENNING_OIDC_OIDC_KEYCLOAK_IDP_HINT=None,
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
    ADMIN_OIDC_USERNAME_CLAIM="claim_name",
    ADMIN_OIDC_GROUPS_CLAIM="groups_claim_name",
    ADMIN_OIDC_CLAIM_MAPPING={"first_name": "given_name"},
    ADMIN_OIDC_SYNC_GROUPS=False,
    ADMIN_OIDC_SYNC_GROUPS_GLOB_PATTERN="local.groups.*",
    ADMIN_OIDC_DEFAULT_GROUPS=["Admins", "Read-only"],
    ADMIN_OIDC_MAKE_USERS_STAFF=True,
    ADMIN_OIDC_SUPERUSER_GROUP_NAMES=["superuser"],
    ADMIN_OIDC_OIDC_USE_NONCE=False,
    ADMIN_OIDC_OIDC_NONCE_SIZE=48,
    ADMIN_OIDC_OIDC_STATE_SIZE=48,
    ADMIN_OIDC_OIDC_EXEMPT_URLS=["http://testserver/some-endpoint"],
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
        self.assertEqual(config.username_claim, "claim_name")
        self.assertEqual(config.groups_claim, "groups_claim_name")
        self.assertEqual(config.claim_mapping, {"first_name": "given_name"})
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
        self.assertEqual(config.oidc_exempt_urls, ["http://testserver/some-endpoint"])
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
        ADMIN_OIDC_OIDC_EXEMPT_URLS=None,
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
        self.assertEqual(config.username_claim, "sub")
        self.assertEqual(config.groups_claim, "groups_claim_name")
        self.assertEqual(
            config.claim_mapping,
            {"last_name": "family_name", "first_name": "given_name"},
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
        self.assertEqual(config.oidc_exempt_urls, [])
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
