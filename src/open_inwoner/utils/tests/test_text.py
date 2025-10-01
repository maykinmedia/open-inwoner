from decimal import Decimal
from unittest import TestCase

from django.utils.safestring import mark_safe

from open_inwoner.utils.text import (
    html_tag_wrap_format,
    mask_sensitive_data,
    middle_truncate,
)


class TextTestCase(TestCase):
    def test_middle_truncate(self):
        self.assertEqual(middle_truncate("abc", 5), "abc")
        self.assertEqual(
            middle_truncate("a_pretty_long_file_name.jpg", 23), "a_pretty...le_name.jpg"
        )

    def test_html_tag_wrap_format(self):
        format_str = "foo {value}"
        self.assertEqual(
            html_tag_wrap_format(format_str, "b", value="bar"), "foo <b>bar</b>"
        )
        with self.assertRaises(KeyError):
            html_tag_wrap_format(format_str, "b", bad_key="bar")

        # multiple
        format_str = "foo {one} {two}"
        self.assertEqual(
            html_tag_wrap_format(format_str, "b", one=1, two="2"),
            "foo <b>1</b> <b>2</b>",
        )
        # escape or use safe
        self.assertEqual(
            html_tag_wrap_format(format_str, "b", one="<one>", two=mark_safe("<two>")),
            "foo <b>&lt;one&gt;</b> <b><two></b>",
        )


class TestMaskSensitiveData(TestCase):
    """Test suite for mask_sensitive_data function."""

    def test_empty_input(self):
        """Test with empty string."""
        self.assertEqual(mask_sensitive_data(""), "")
        self.assertEqual(mask_sensitive_data(None), "")

    def test_short_values(self):
        """Test with values shorter than min_length."""
        self.assertEqual(mask_sensitive_data("12345"), "*****")
        self.assertEqual(mask_sensitive_data("abc"), "***")

    def test_default_masking(self):
        """Test with default parameters."""
        self.assertEqual(mask_sensitive_data("password123"), "pa*******23")
        self.assertEqual(mask_sensitive_data("1234567890"), "12******90")

    def test_credit_card_masking(self):
        """Test typical credit card masking."""
        self.assertEqual(
            mask_sensitive_data("4111222233334444", 4, 4), "4111********4444"
        )
        self.assertEqual(
            mask_sensitive_data("378282246310005", 2, 4), "37*********0005"
        )

    def test_email_masking(self):
        """Test email address masking."""
        self.assertEqual(
            mask_sensitive_data("user@example.com", 2, 11), "us***example.com"
        )
        self.assertEqual(
            mask_sensitive_data("john.doe@company.org", 5, 12), "john.***@company.org"
        )

    def test_phone_number_masking(self):
        """Test phone number masking."""
        self.assertEqual(mask_sensitive_data("1234567890", 3, 2), "123*****90")
        self.assertEqual(mask_sensitive_data("+15551234567", 3, 4), "+15*****4567")

    def test_zero_visible_chars(self):
        """Test with zero visible characters."""
        self.assertEqual(mask_sensitive_data("secretkey", 0, 0), "*********")
        self.assertEqual(mask_sensitive_data("password", 0, 0), "********")

    def test_boundary_conditions(self):
        """Test boundary conditions and edge cases."""
        # Visible chars more than string length
        self.assertEqual(mask_sensitive_data("123456", 10, 2), "1234*6")
        self.assertEqual(mask_sensitive_data("abcdef", 3, 10), "a*cdef")

        # Adjust min_length parameter
        self.assertEqual(mask_sensitive_data("123456", 2, 2, 10), "******")
        self.assertEqual(mask_sensitive_data("12345678", 2, 2, 5), "12****78")

    def test_non_string_input(self):
        """Test with non-string input that should be converted."""
        self.assertEqual(mask_sensitive_data(12345678), "12****78")
        self.assertEqual(mask_sensitive_data(None), "")
        self.assertEqual(mask_sensitive_data(Decimal("3.14158")), "3.***58")
