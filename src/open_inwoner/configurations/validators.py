from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.models import OIDCClient

from .choices import OpenIDDisplayChoices


def validate_oidc_config(value):
    """Prevent display of OIDC login to regular users if `make_users_staff` is true"""

    admin_oidc_client = OIDCClient.objects.filter(
        identifier=OIDC_ADMIN_CONFIG_IDENTIFIER
    ).first()
    make_users_staff = bool(
        admin_oidc_client
        and admin_oidc_client.options.get("groups_settings", {}).get("make_users_staff")
    )

    if make_users_staff and value == OpenIDDisplayChoices.regular:
        raise ValidationError(
            _(
                "You cannot select this option if 'Make users staff' is selected "
                "in the OpenID Connect configuration."
            )
        )


def validate_javascript_file(file):
    """Validate JavaScript file for size only"""
    max_size = 1024 * 512  # 0.5MB
    if file.size > max_size:
        raise ValidationError(
            _("File is too large. Maximum size is %(max_size)s MB")
            % {"max_size": max_size / (1024 * 1024)}
        )

    # Basic file validation
    file.seek(0)
    try:
        content = file.read().decode("utf-8")
    except UnicodeDecodeError:
        raise ValidationError(
            _("File is not a valid JavaScript file (invalid encoding)")
        ) from None

    # Reset file pointer
    file.seek(0)
    return file
