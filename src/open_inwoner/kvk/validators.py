import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# There are only 4 possibilities, let's enumerate them
regexes = (
    re.compile(r"^https://api.kvk.nl/api$"),
    re.compile(r"^https://api.kvk.nl/api/$"),
    re.compile(r"^https://api.kvk.nl/test/api$"),
    re.compile(r"^https://api.kvk.nl/test/api/$"),
)


def validate_api_root(value):
    if not any(regex.match(value) for regex in regexes):
        raise ValidationError(
            _(
                "The API root is incorrect. Please double-check that the host is "
                "correct and you didn't include the version number or endpoint."
            )
        )
