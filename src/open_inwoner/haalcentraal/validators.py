from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# Standard HTTP headers that must not be overridden via config (RFC 7230 / common headers).
# Comparison is case-insensitive (HTTP headers are case-insensitive per RFC 7230).
STANDARD_HTTP_HEADERS = frozenset(
    {
        "accept",
        "accept-charset",
        "accept-encoding",
        "accept-language",
        "authorization",
        "cache-control",
        "connection",
        "content-encoding",
        "content-language",
        "content-length",
        "content-location",
        "content-md5",
        "content-range",
        "content-type",
        "cookie",
        "date",
        "expect",
        "expires",
        "from",
        "host",
        "if-match",
        "if-modified-since",
        "if-none-match",
        "if-range",
        "if-unmodified-since",
        "last-modified",
        "max-forwards",
        "pragma",
        "proxy-authorization",
        "range",
        "referer",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
        "user-agent",
        "via",
        "warning",
    }
)


def validate_no_standard_http_headers(headers: list) -> None:
    """
    Ensure none of the configured header keys shadow standard HTTP headers.
    Protects against accidentally overriding headers like Content-Type or Authorization.
    """
    if not isinstance(headers, list):
        raise ValidationError(
            _("Expected a list of header objects, got {type}.").format(
                type=type(headers).__name__
            )
        )

    malformed = [
        item for item in headers if not isinstance(item, dict) or "key" not in item
    ]
    if malformed:
        raise ValidationError(_("Each header must be an object with a 'key' field."))

    conflicts = [
        item["key"] for item in headers if item["key"].lower() in STANDARD_HTTP_HEADERS
    ]
    if conflicts:
        raise ValidationError(
            _(
                "The following header names conflict with standard HTTP headers "
                "and cannot be used: {headers}"
            ).format(headers=", ".join(conflicts))
        )


def validate_verwerking_header(value: str) -> None:
    """
    **Deprecated.** The `api_verwerking` field has been removed. This validator is
    retained because historical migrations reference it and cannot be removed.
    """
    if value.count("@") > 1:
        raise ValidationError(
            _("The x-verwerking header must contain at most one '@' character."),
            code="no_multiple_at_characters",
        )
