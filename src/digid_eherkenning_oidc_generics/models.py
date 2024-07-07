from django.db import models
from django.utils.translation import gettext_lazy as _

from django_jsonform.models.fields import ArrayField
from mozilla_django_oidc_db.models import OpenIDConnectConfigBase


def get_default_scopes_bsn():
    """
    Returns the default scopes to request for OpenID Connect logins
    """
    return ["openid", "bsn"]


def get_default_scopes_kvk():
    """
    Returns the default scopes to request for OpenID Connect logins
    """
    return ["openid", "kvk"]


class OpenIDConnectDigiDConfig(OpenIDConnectConfigBase):
    """
    Configuration for DigiD authentication via OpenID connect
    """

    oidc_rp_client_id = models.CharField(
        help_text="OpenID Connect client ID provided by the OIDC Provider",
        max_length=1000,
        verbose_name="OpenID Connect client ID",
    )
    oidc_rp_client_secret = models.CharField(
        help_text="OpenID Connect secret provided by the OIDC Provider",
        max_length=1000,
        verbose_name="OpenID Connect secret",
    )
    oidc_rp_sign_algo = models.CharField(
        default="HS256",
        help_text="Algorithm the Identity Provider uses to sign ID tokens",
        max_length=50,
        verbose_name="OpenID sign algorithm",
    )
    oidc_op_discovery_endpoint = models.URLField(
        blank=True,
        help_text="URL of your OpenID Connect provider discovery endpoint ending with a slash (`.well-known/...` will be added automatically). If this is provided, the remaining endpoints can be omitted, as they will be derived from this endpoint.",
        max_length=1000,
        verbose_name="Discovery endpoint",
    )
    oidc_op_jwks_endpoint = models.URLField(
        blank=True,
        help_text="URL of your OpenID Connect provider JSON Web Key Set endpoint. Required if `RS256` is used as signing algorithm.",
        max_length=1000,
        verbose_name="JSON Web Key Set endpoint",
    )
    oidc_op_authorization_endpoint = models.URLField(
        help_text="URL of your OpenID Connect provider authorization endpoint",
        max_length=1000,
        verbose_name="Authorization endpoint",
    )
    oidc_op_token_endpoint = models.URLField(
        help_text="URL of your OpenID Connect provider token endpoint",
        max_length=1000,
        verbose_name="Token endpoint",
    )
    oidc_op_user_endpoint = models.URLField(
        help_text="URL of your OpenID Connect provider userinfo endpoint",
        max_length=1000,
        verbose_name="User endpoint",
    )
    oidc_rp_idp_sign_key = models.CharField(
        blank=True,
        help_text="Key the Identity Provider uses to sign ID tokens in the case of an RSA sign algorithm. Should be the signing key in PEM or DER format.",
        max_length=1000,
        verbose_name="Sign key",
    )
    oidc_use_nonce = models.BooleanField(
        default=True,
        help_text="Controls whether the OpenID Connect client uses nonce verification",
        verbose_name="Use nonce",
    )
    oidc_nonce_size = models.PositiveIntegerField(
        default=32,
        help_text="Sets the length of the random string used for OpenID Connect nonce verification",
        verbose_name="Nonce size",
    )
    oidc_state_size = models.PositiveIntegerField(
        default=32,
        help_text="Sets the length of the random string used for OpenID Connect state verification",
        verbose_name="State size",
    )
    oidc_exempt_urls = ArrayField(
        base_field=models.CharField(max_length=1000, verbose_name="Exempt URL"),
        blank=True,
        default=list,
        help_text="This is a list of absolute url paths, regular expressions for url paths, or Django view names. This plus the mozilla-django-oidc urls are exempted from the session renewal by the SessionRefresh middleware.",
        size=None,
        verbose_name="URLs exempt from session renewal",
    )
    userinfo_claims_source = models.CharField(
        choices=[
            ("userinfo_endpoint", "Userinfo endpoint"),
            ("id_token", "ID token"),
        ],
        default="userinfo_endpoint",
        help_text="Indicates the source from which the user information claims should be extracted.",
        max_length=100,
        verbose_name="user information claims extracted from",
    )
    oidc_op_logout_endpoint = models.URLField(
        blank=True,
        help_text="URL of your OpenID Connect provider logout endpoint",
        max_length=1000,
        verbose_name="Logout endpoint",
    )
    oidc_keycloak_idp_hint = models.CharField(
        blank=True,
        help_text="Specific for Keycloak: parameter that indicates which identity provider should be used (therefore skipping the Keycloak login screen).",
        max_length=1000,
        verbose_name="Keycloak Identity Provider hint",
    )
    enabled = models.BooleanField(
        default=False,
        help_text="Indicates whether OpenID Connect for authentication/authorization is enabled. This overrides overrides the usage of SAML for DigiD authentication.",
        verbose_name="enable",
    )
    identifier_claim_name = models.CharField(
        default="bsn",
        help_text="The name of the claim in which the BSN of the user is stored",
        max_length=100,
        verbose_name="BSN claim name",
    )
    oidc_rp_scopes_list = ArrayField(
        base_field=models.CharField(max_length=50, verbose_name="OpenID Connect scope"),
        blank=True,
        default=get_default_scopes_bsn,
        help_text="OpenID Connect scopes that are requested during login. These scopes are hardcoded and must be supported by the identity provider",
        size=None,
        verbose_name="OpenID Connect scopes",
    )

    # TODO: this is not in django-digid-eherkenning
    error_message_mapping = models.JSONField(
        blank=True,
        default=dict,
        help_text="Mapping that maps error messages returned by the identity provider to human readable error messages that are shown to the user",
        max_length=1000,
        verbose_name="Error message mapping",
    )

    # XXX: no longer necessary to be a separate URL, kept for backwards compatibility
    # since OIDC providers need to update the allowed Redirect URIs
    oidc_authentication_callback_url = "digid_oidc:callback"

    @property
    def oidcdb_username_claim(self):
        return [self.identifier_claim_name]

    def get_callback_view(self):
        from .views import DigiDOIDCAuthenticationCallbackView

        return DigiDOIDCAuthenticationCallbackView.as_view()

    class Meta:
        verbose_name = _("OpenID Connect configuration for DigiD")
        db_table = "digid_eherkenning_oidc_generics_openidconnectdigidconfig"


class OpenIDConnectEHerkenningConfig(OpenIDConnectConfigBase):
    """
    Configuration for eHerkenning authentication via OpenID connect
    """

    oidc_rp_client_id = models.CharField(
        help_text="OpenID Connect client ID provided by the OIDC Provider",
        max_length=1000,
        verbose_name="OpenID Connect client ID",
    )
    oidc_rp_client_secret = models.CharField(
        help_text="OpenID Connect secret provided by the OIDC Provider",
        max_length=1000,
        verbose_name="OpenID Connect secret",
    )
    oidc_rp_sign_algo = models.CharField(
        default="HS256",
        help_text="Algorithm the Identity Provider uses to sign ID tokens",
        max_length=50,
        verbose_name="OpenID sign algorithm",
    )
    oidc_op_discovery_endpoint = models.URLField(
        blank=True,
        help_text="URL of your OpenID Connect provider discovery endpoint ending with a slash (`.well-known/...` will be added automatically). If this is provided, the remaining endpoints can be omitted, as they will be derived from this endpoint.",
        max_length=1000,
        verbose_name="Discovery endpoint",
    )
    oidc_op_jwks_endpoint = models.URLField(
        blank=True,
        help_text="URL of your OpenID Connect provider JSON Web Key Set endpoint. Required if `RS256` is used as signing algorithm.",
        max_length=1000,
        verbose_name="JSON Web Key Set endpoint",
    )
    oidc_op_authorization_endpoint = models.URLField(
        help_text="URL of your OpenID Connect provider authorization endpoint",
        max_length=1000,
        verbose_name="Authorization endpoint",
    )
    oidc_op_token_endpoint = models.URLField(
        help_text="URL of your OpenID Connect provider token endpoint",
        max_length=1000,
        verbose_name="Token endpoint",
    )
    oidc_op_user_endpoint = models.URLField(
        help_text="URL of your OpenID Connect provider userinfo endpoint",
        max_length=1000,
        verbose_name="User endpoint",
    )
    oidc_rp_idp_sign_key = models.CharField(
        blank=True,
        help_text="Key the Identity Provider uses to sign ID tokens in the case of an RSA sign algorithm. Should be the signing key in PEM or DER format.",
        max_length=1000,
        verbose_name="Sign key",
    )
    oidc_use_nonce = models.BooleanField(
        default=True,
        help_text="Controls whether the OpenID Connect client uses nonce verification",
        verbose_name="Use nonce",
    )
    oidc_nonce_size = models.PositiveIntegerField(
        default=32,
        help_text="Sets the length of the random string used for OpenID Connect nonce verification",
        verbose_name="Nonce size",
    )
    oidc_state_size = models.PositiveIntegerField(
        default=32,
        help_text="Sets the length of the random string used for OpenID Connect state verification",
        verbose_name="State size",
    )
    oidc_exempt_urls = ArrayField(
        base_field=models.CharField(max_length=1000, verbose_name="Exempt URL"),
        blank=True,
        default=list,
        help_text="This is a list of absolute url paths, regular expressions for url paths, or Django view names. This plus the mozilla-django-oidc urls are exempted from the session renewal by the SessionRefresh middleware.",
        size=None,
        verbose_name="URLs exempt from session renewal",
    )
    userinfo_claims_source = models.CharField(
        choices=[
            ("userinfo_endpoint", "Userinfo endpoint"),
            ("id_token", "ID token"),
        ],
        default="userinfo_endpoint",
        help_text="Indicates the source from which the user information claims should be extracted.",
        max_length=100,
        verbose_name="user information claims extracted from",
    )
    oidc_op_logout_endpoint = models.URLField(
        blank=True,
        help_text="URL of your OpenID Connect provider logout endpoint",
        max_length=1000,
        verbose_name="Logout endpoint",
    )
    oidc_keycloak_idp_hint = models.CharField(
        blank=True,
        help_text="Specific for Keycloak: parameter that indicates which identity provider should be used (therefore skipping the Keycloak login screen).",
        max_length=1000,
        verbose_name="Keycloak Identity Provider hint",
    )
    enabled = models.BooleanField(
        default=False,
        help_text="Indicates whether OpenID Connect for authentication/authorization is enabled. This overrides overrides the usage of SAML for eHerkenning authentication.",
        verbose_name="enable",
    )
    identifier_claim_name = models.CharField(
        default="kvk",
        help_text="The name of the claim in which the KVK of the user is stored",
        max_length=100,
        verbose_name="KVK claim name",
    )
    oidc_rp_scopes_list = ArrayField(
        base_field=models.CharField(max_length=50, verbose_name="OpenID Connect scope"),
        blank=True,
        default=get_default_scopes_kvk,
        help_text="OpenID Connect scopes that are requested during login. These scopes are hardcoded and must be supported by the identity provider",
        size=None,
        verbose_name="OpenID Connect scopes",
    )

    # TODO: this is not in django-digid-eherkenning
    error_message_mapping = models.JSONField(
        blank=True,
        default=dict,
        help_text="Mapping that maps error messages returned by the identity provider to human readable error messages that are shown to the user",
        max_length=1000,
        verbose_name="Error message mapping",
    )

    # XXX: no longer necessary to be a separate URL, kept for backwards compatibility
    # since OIDC providers need to update the allowed Redirect URIs
    oidc_authentication_callback_url = "eherkenning_oidc:callback"

    @property
    def oidcdb_username_claim(self):
        return [self.identifier_claim_name]

    def get_callback_view(self):
        from open_inwoner.accounts.views import (
            CustomEHerkenningOIDCAuthenticationCallbackView as CallbackView,
        )

        return CallbackView.as_view()

    class Meta:
        verbose_name = _("OpenID Connect configuration for eHerkenning")
        db_table = "digid_eherkenning_oidc_generics_openidconnecteherkenningconfig"
