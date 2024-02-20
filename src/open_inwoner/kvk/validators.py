import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

regexp = re.compile("/api/[0-9a-z]")


def validate_api_root(value):
    if regexp.search(value, re.IGNORECASE):
        raise ValidationError(
            _(
                "The API root is incorrect. Please double-check that "
                "you didn't include the version number or endpoint."
            )
        )
