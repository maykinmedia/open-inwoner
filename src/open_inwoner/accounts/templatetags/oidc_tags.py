from django import template

from mozilla_django_oidc_db.models import OIDCClient

register = template.Library()


@register.simple_tag
def get_oidc_client(identifier: str) -> OIDCClient | None:
    """
    Return the OIDCClient for the given identifier, or None if it doesn't exist.

    Mirrors mozilla_django_oidc_db's own ``get_oidc_admin_client`` tag, but for
    an arbitrary identifier (e.g. our DigiD/eHerkenning/eIDAS clients).
    """
    return OIDCClient.objects.filter(identifier=identifier).first()
