from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.mixins import OpenIDConnectConfig

from .choices import OpenIDDisplayChoices


def validate_oidc_config(value):
    """Prevent display of OIDC login to regular users if `make_users_staff` is true"""

    open_id_config = OpenIDConnectConfig.get_solo()

    if open_id_config.make_users_staff and value == OpenIDDisplayChoices.regular:
        raise ValidationError(
            _(
                "You cannot select this option if 'Make users staff' is selected "
                "in the OpenID Connect configuration."
            )
        )
