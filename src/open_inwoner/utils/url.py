import re
import uuid

from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme

from furl.furl import furl


def build_absolute_url(path: str) -> str:
    domain = Site.objects.get_current().domain
    protocol = "https" if settings.IS_HTTPS else "http"
    return f"{protocol}://{domain}{path}"


def get_next_url_from(request, *, default: str = "") -> str:
    # possibly add parameter to prioritize get/post, override parameter name
    next_url = request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts=[
            request.get_host(),
        ],
        require_https=settings.IS_HTTPS,
    ):
        return iri_to_uri(next_url)
    return default


def get_next_url_param(url: str) -> str:
    return furl(url).args.get("next", "")


def set_next_url_param(url: str, next_url: str) -> str:
    if not next_url:
        return url
    f = furl(url)
    f.args["next"] = next_url
    return str(f)


def prepend_next_url_param(url: str, next_url: str) -> str:
    """
    set next parameter on url,
        if parameter already exists prepend it to the new next_url (recursively in case it already exists)

    prepend_next_url_param('/foo', '/bar')
    (url encoded) '/foo?next=/bar'

    prepend_next_url_param('/foo?next=/bar', '/bazz')
    (url encoded) '/foo?next=/bazz?next=/bar'
    """
    if not next_url:
        return url

    u = furl(url)
    current_next = u.args.get("next", "")
    if current_next:
        next_url = prepend_next_url_param(next_url, current_next)
    u.args.set("next", next_url)
    return u.url


_UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)


def uuid_from_url(
    url: str, allow_multiple: bool = False
) -> uuid.UUID | list[uuid.UUID] | None:
    """Extract UUID(s) from a given URL"""

    matches = re.findall(_UUID_PATTERN, url)

    if not matches:
        return None
    if len(matches) > 1:
        if allow_multiple:
            return [uuid.UUID(match) for match in matches]
        raise ValueError(
            "url contains more than 1 UUID (use allow_multiple=True if you expect multiple results)"
        )

    return uuid.UUID(matches[0])
