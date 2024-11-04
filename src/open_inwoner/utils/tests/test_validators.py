from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext as _

from ..validators import (
    DutchPhoneNumberValidator,
    format_phone_number,
    validate_array_contents_non_empty,
    validate_phone_number,
    validate_postal_code,
)


class ValidatorsTestCase(TestCase):
    """
    Validates the functions defined in ``utils.validators`` module.
    """

    def test_validate_postal_code(self):
        """
        Test all valid postal code and also test invalid values
        """
        invalid_postal_codes = [
            "0000AA",
            "0999AA",
            "1000  AA",
            "1000 AAA",
            "1000AAA",
            "0000aa",
            "0999aa",
            "1000  aa",
            "1000 aaa",
            "1000aaa",
            "1111,aa",
            "1111,a",
            '1111"a',
            '1111"aa',
        ]
        for invalid_postal_code in invalid_postal_codes:
            self.assertRaisesMessage(
                ValidationError,
                "Ongeldige postcode",
                validate_postal_code,
                invalid_postal_code,
            )

        self.assertIsNone(validate_postal_code("1015CJ"))
        self.assertIsNone(validate_postal_code("1015 CJ"))
        self.assertIsNone(validate_postal_code("1015cj"))
        self.assertIsNone(validate_postal_code("1015 cj"))
        self.assertIsNone(validate_postal_code("1015Cj"))
        self.assertIsNone(validate_postal_code("1015 Cj"))
        self.assertIsNone(validate_postal_code("1015cJ"))
        self.assertIsNone(validate_postal_code("1015 cJ"))

    def test_validate_phone_number(self):
        invalid_phone_numbers = [
            "0695azerty",
            "azerty0545",
            "@4566544++8",
            "onetwothreefour",
        ]
        for invalid_phone_number in invalid_phone_numbers:
            self.assertRaisesMessage(
                ValidationError,
                "Het opgegeven mobiele telefoonnummer is ongeldig.",
                validate_phone_number,
                invalid_phone_number,
            )

        self.assertEqual(validate_phone_number(" 0695959595"), " 0695959595")
        self.assertEqual(validate_phone_number("+33695959595"), "+33695959595")
        self.assertEqual(validate_phone_number("00695959595"), "00695959595")
        self.assertEqual(validate_phone_number("00-69-59-59-59-5"), "00-69-59-59-59-5")
        self.assertEqual(validate_phone_number("00 69 59 59 59 5"), "00 69 59 59 59 5")

    def test_format_phone_number(self):
        samples = [
            "0031123456789",
            "+31123456789",
            "0123456789",
            "012-3456789",
            "012 345 67 89",
            "+31 12 345 67 89",
        ]
        expected_result = "+31123456789"

        for num in samples:
            self.assertEqual(format_phone_number(num), expected_result)

        # testing some non dutch numbers
        self.assertEqual(format_phone_number("+32 12 345 67 89"), "+32123456789")
        self.assertEqual(format_phone_number("0032 12 345 67 89"), "+32123456789")

    def test_dutch_phonenumber_validator(self):
        valid_samples = [
            "0612345678",
            "+31612345678",
            "0201234567",
            "+31201234567",
        ]
        invalid_samples = [
            "1123456789",
            "+31123456789",
            "0123456789",
            "0695azerty",
            "azerty0545",
            "@4566544++8",
            "onetwothreefour",
        ]
        invalid_samples_2 = [
            "012-3456789",
            "012 345 67 89",
            "+31 12 345 67 89",
        ]

        for valid_num in valid_samples:
            self.assertIsNone(DutchPhoneNumberValidator()(valid_num))

        for invalid_num in invalid_samples:
            self.assertRaisesMessage(
                ValidationError,
                _(
                    "Not a valid dutch phone number. An example of a valid dutch phone number is 0612345678"
                ),
                DutchPhoneNumberValidator(),
                invalid_num,
            )

        for invalid_num in invalid_samples_2:
            self.assertRaisesMessage(
                ValidationError,
                _("The phone number cannot contain spaces or dashes"),
                DutchPhoneNumberValidator(),
                invalid_num,
            )

    def test_validate_array_contents_ok(self):
        for val in [["test"], ["t", "e", "s", "t"], []]:
            with self.subTest(val=val):
                validate_array_contents_non_empty(val)

    def test_validate_array_contents_error(self):
        for val in [["test", ""], ["test", "  "]]:
            with self.subTest(val=val):
                with self.assertRaises(ValidationError):
                    validate_array_contents_non_empty(val)
