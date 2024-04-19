from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from solo.admin import SingletonModelAdmin

from .forms import OpenIDConnectDigiDConfigForm, OpenIDConnectEHerkenningConfigForm
from .models import OpenIDConnectDigiDConfig, OpenIDConnectEHerkenningConfig


class OpenIDConnectConfigBaseAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            _("Activation"),
            {"fields": ("enabled",)},
        ),
        (
            _("Common settings"),
            {
                "fields": (
                    "identifier_claim_name",
                    "oidc_rp_client_id",
                    "oidc_rp_client_secret",
                    "oidc_rp_scopes_list",
                    "oidc_rp_sign_algo",
                    "oidc_rp_idp_sign_key",
                    "userinfo_claims_source",
                    "error_message_mapping",
                )
            },
        ),
        (
            _("Endpoints"),
            {
                "fields": (
                    "oidc_op_discovery_endpoint",
                    "oidc_op_jwks_endpoint",
                    "oidc_op_authorization_endpoint",
                    "oidc_op_token_endpoint",
                    "oidc_op_user_endpoint",
                    "oidc_op_logout_endpoint",
                )
            },
        ),
        (_("Keycloak specific settings"), {"fields": ("oidc_keycloak_idp_hint",)}),
        (
            _("Advanced settings"),
            {
                "fields": (
                    "oidc_use_nonce",
                    "oidc_nonce_size",
                    "oidc_state_size",
                    "oidc_exempt_urls",
                ),
                "classes": [
                    "collapse in",
                ],
            },
        ),
    )


@admin.register(OpenIDConnectDigiDConfig)
class OpenIDConnectConfigDigiDAdmin(OpenIDConnectConfigBaseAdmin):
    form = OpenIDConnectDigiDConfigForm


@admin.register(OpenIDConnectEHerkenningConfig)
class OpenIDConnectConfigEHerkenningAdmin(OpenIDConnectConfigBaseAdmin):
    form = OpenIDConnectEHerkenningConfigForm
