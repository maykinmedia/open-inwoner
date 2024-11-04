from typing import TYPE_CHECKING, Protocol

from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

import phonenumbers
from filer.models import Image

if TYPE_CHECKING:
    from phonenumbers.phonenumber import PhoneNumber


class ParsePhoneNumber(Protocol):
    def __call__(self, value: str) -> "PhoneNumber":
        ...  # pragma: nocover


@deconstructible
class DutchPhoneNumberValidator:
    language = "NL"
    country_name = _("Netherlands")
    error_message = _(
        "Not a valid dutch phone number. An example of a valid dutch phone number is 0612345678"
    )
    _parse_phonenumber: ParsePhoneNumber

    def __call__(self, value):
        self._check_for_invalid_chars(value)

        parsed_value = self._parse_phonenumber(value)

        if not phonenumbers.is_possible_number(
            parsed_value
        ) or not phonenumbers.is_valid_number(parsed_value):
            raise ValidationError(
                self.error_message,
                params={"country": self.country_name},
                code="invalid",
            )

        # this additional check is needed because while .parse() does some checks on country
        #   is_possible_number() and is_valid_number() do not
        #   eg: country=NL would accept "+442083661177"
        if not phonenumbers.is_valid_number_for_region(parsed_value, self.language):
            raise ValidationError(
                self.error_message,
                params={"country": self.country_name},
                code="invalid",
            )

    def _parse_phonenumber(self, value: str) -> "PhoneNumber":
        try:
            return phonenumbers.parse(value, self.language)
        except phonenumbers.NumberParseException:
            raise ValidationError(
                self.error_message,
                code="invalid",
            )

    def _check_for_invalid_chars(self, value: str) -> None:
        if " " in value or "-" in value:
            raise ValidationError(
                _("The phone number cannot contain spaces or dashes"),
                code="invalid",
            )


validate_digits = RegexValidator(
    regex="^[0-9]+$", message=_("Expected a numerical value.")
)


@deconstructible
class CharFieldValidator(RegexValidator):
    regex = r"^[\w'’\- ]+\Z"
    message = _(
        "Please make sure your input contains only valid characters "
        "(letters, numbers, apostrophe, dash, space)."
    )


# deprecated
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
        value = f"+{value[2:]}"
    elif value[0] == "0":
        value = f"+31{value[1:]}"
    return value.strip().replace("-", "").replace(" ", "")


class CustomRegexValidator(RegexValidator):
    """
    CustomRegexValidator because the validated value is append to the message.
    """

    def __call__(self, value):
        """
        Validates that the input matches the regular expression.
        """
        if not self.regex.search(force_str(value)):
            message = "{}: {}".format(self.message, force_str(value))
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


class DiversityValidator:
    def validate(self, password, user=None):
        if (
            password.isupper()
            or password.islower()
            or password.isalpha()
            or password.isdigit()
        ):
            raise ValidationError(
                _(
                    "Your password must contain at least 1 upper-case letter, "
                    "1 lower-case letter, 1 digit."
                )
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 upper-case letter, "
            "1 lower-case letter, 1 digit."
        )


def validate_kvk(value):
    if len(value) != 8:
        raise ValidationError(
            _("Het KVK nummer moet uit 8 cijfers bestaan."), code="invalid"
        )
    if not value.isdigit():
        raise ValidationError(_("Het KVK nummer moet numeriek zijn."), code="invalid")


def validate_array_contents_non_empty(list_: list) -> None:
    if any(item.isspace() or len(item) < 1 for item in list_):
        raise ValidationError(
            _("Valid strings must include at least one non-space character")
        )
