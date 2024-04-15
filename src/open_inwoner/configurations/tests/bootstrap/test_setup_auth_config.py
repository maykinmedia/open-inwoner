from unittest import skip

from django.test import TestCase, override_settings

import requests
import requests_mock
from django_setup_configuration.exceptions import ConfigurationRunFailed
from mozilla_django_oidc_db.models import UserInformationClaimsSources

from digid_eherkenning_oidc_generics.models import (
    OpenIDConnectDigiDConfig,
    OpenIDConnectEHerkenningConfig,
)
from open_inwoner.utils.test import ClearCachesMixin

from ...bootstrap.auth import (
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
