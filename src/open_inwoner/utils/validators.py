from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _

from filer.models import Image


def validate_charfield_entry(value, allow_apostrophe=False):
    """
    Validates a charfield entry according with requirements.

    :param value: The input value string to be validated.
    :param allow_apostrophe: Boolean to add the apostrophe character to the
    validation. Apostrophes are allowed in input with ``True`` value. Defaults
    to ``False``.
    :return: The input value if validation passed. Otherwise, raises a
    ``ValidationError`` exception.
    """
    invalid_chars = '/"\\,;' if allow_apostrophe else "/\"\\,.:;'"

    for char in invalid_chars:
        if char in value:
            raise ValidationError(_("Uw invoer bevat een ongeldig teken: %s") % char)
    return value


def validate_phone_number(value):
    try:
        int(value.strip().lstrip("0+").replace("-", "").replace(" ", ""))
    except (ValueError, TypeError):
        raise ValidationError(_("Het opgegeven mobiele telefoonnummer is ongeldig."))

    return value


def format_phone_number(value):
    if value[0:2] == "00":
        value = "+{val}".format(val=value[2:])
    elif value[0] == "0":
        value = "+31{val}".format(val=value[1:])
    return value.strip().replace("-", "").replace(" ", "")


class CustomRegexValidator(RegexValidator):
    """
    CustomRegexValidator because the validated value is append to the message.
    """

    def __call__(self, value):
        """
        Validates that the input matches the regular expression.
        """
        if not self.regex.search(force_text(value)):
            message = "{0}: {1}".format(self.message, force_text(value))
            raise ValidationError(message, code=self.code)


validate_postal_code = CustomRegexValidator(
    regex="^[1-9][0-9]{3} ?[a-zA-Z]{2}$", message=_("Ongeldige postcode")
)


@deconstructible
class FilerExactImageSizeValidator:
    def __init__(self, width, height):
        if not width or not height:
            raise ValueError("specify exact height and width")
        self.width = width
        self.height = height

    def __call__(self, image_id):
        image = Image.objects.get(pk=image_id)
        width, height = get_image_dimensions(image.file)

        if width != self.width or height != self.height:
            raise ValidationError(
                [
                    f"Image size should be exactly {self.width}x{self.height} pixels (not {width}x{height}."
                ]
            )

    def __eq__(self, other):
        return self.width == other.width and self.height == other.height
