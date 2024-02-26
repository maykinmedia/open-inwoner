from copy import deepcopy

from mozilla_django_oidc_db.constants import OIDC_MAPPING as _OIDC_MAPPING
from mozilla_django_oidc_db.forms import OpenIDConnectConfigForm

from .models import OpenIDConnectDigiDConfig, OpenIDConnectEHerkenningConfig

OIDC_MAPPING = deepcopy(_OIDC_MAPPING)

OIDC_MAPPING["oidc_op_logout_endpoint"] = "end_session_endpoint"


class OpenIDConnectBaseConfigForm(OpenIDConnectConfigForm):
    required_endpoints = [
        "oidc_op_authorization_endpoint",
        "oidc_op_token_endpoint",
        "oidc_op_user_endpoint",
        "oidc_op_logout_endpoint",
    ]
    oidc_mapping = OIDC_MAPPING


class OpenIDConnectDigiDConfigForm(OpenIDConnectBaseConfigForm):
    class Meta:
        model = OpenIDConnectDigiDConfig
        fields = "__all__"


class OpenIDConnectEHerkenningConfigForm(OpenIDConnectBaseConfigForm):
    class Meta:
        model = OpenIDConnectEHerkenningConfig
        fields = "__all__"
