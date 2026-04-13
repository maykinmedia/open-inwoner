from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils.translation import gettext as _

import clamd

from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.validators import (
    DutchPhoneNumberValidator,
    NoVirusValidator,
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


@patch("open_inwoner.utils.validators.clamd.ClamdNetworkSocket")
class NoVirusValidatorTests(TestCase):
    def setUp(self):
        self.config = SiteConfiguration.get_solo()
        self.config.enable_virus_scan = True
        self.config.clamav_host = "clamav"
        self.config.clamav_port = 3310
        self.config.clamav_timeout = 30.0
        self.config.save()

    def _uploaded_file(self, content=b"data"):
        return SimpleUploadedFile(
            "test.bin", content, content_type="application/octet-stream"
        )

    def test_scan_disabled_skips_clamd(self, mock_clamd_cls):
        self.config.enable_virus_scan = False
        self.config.save()
        NoVirusValidator()(self._uploaded_file())
        mock_clamd_cls.assert_not_called()

    def test_clean_file_passes(self, mock_clamd_cls):
        mock_clamd_cls.return_value.instream.return_value = {"stream": ("OK", "")}
        NoVirusValidator()(self._uploaded_file())

    def test_clean_file_seeks_to_zero_before_scan(self, mock_clamd_cls):
        def _drain_and_return_ok(f):
            f.read()
            return {"stream": ("OK", "")}

        mock_clamd_cls.return_value.instream.side_effect = _drain_and_return_ok
        uploaded = self._uploaded_file()
        uploaded.read()

        NoVirusValidator()(uploaded)

        mock_clamd_cls.return_value.instream.assert_called_once_with(uploaded)
        self.assertEqual(uploaded.tell(), 0)

    def test_virus_found_raises_validation_error_with_threat_name(self, mock_clamd_cls):
        mock_clamd_cls.return_value.instream.return_value = {
            "stream": ("FOUND", "Eicar-Test-Signature")
        }
        with self.assertRaises(ValidationError) as ctx:
            NoVirusValidator()(self._uploaded_file())
        self.assertIn("Eicar-Test-Signature", str(ctx.exception))

    def test_virus_found_with_eicar_bytes(self, mock_clamd_cls):
        mock_clamd_cls.return_value.instream.return_value = {
            "stream": ("FOUND", "Eicar-Test-Signature")
        }
        eicar_file = SimpleUploadedFile(
            "eicar.bin", clamd.EICAR, content_type="application/octet-stream"
        )
        with self.assertRaises(ValidationError):
            NoVirusValidator()(eicar_file)

    def test_scan_error_response_raises_validation_error(self, mock_clamd_cls):
        mock_clamd_cls.return_value.instream.return_value = {
            "stream": ("ERROR", "Permission denied")
        }
        with self.assertRaises(ValidationError) as ctx:
            NoVirusValidator()(self._uploaded_file())
        self.assertIn("error", str(ctx.exception).lower())

    def test_clamd_connection_error_raises_retry_message(self, mock_clamd_cls):
        mock_clamd_cls.return_value.instream.side_effect = clamd.ConnectionError(
            "refused"
        )
        with self.assertRaises(ValidationError) as ctx:
            NoVirusValidator()(self._uploaded_file())
        self.assertIn("retry", str(ctx.exception).lower())

    def test_unexpected_exception_raises_validation_error(self, mock_clamd_cls):
        mock_clamd_cls.return_value.instream.side_effect = OSError("broken pipe")
        with self.assertRaises(ValidationError):
            NoVirusValidator()(self._uploaded_file())

    def test_unexpected_status_raises_validation_error(self, mock_clamd_cls):
        mock_clamd_cls.return_value.instream.return_value = {
            "stream": ("UNKNOWN", "???")
        }
        with self.assertRaises(ValidationError) as ctx:
            NoVirusValidator()(self._uploaded_file())
        self.assertIn("unexpected", str(ctx.exception).lower())

    def test_scanner_constructed_with_config_values(self, mock_clamd_cls):
        self.config.clamav_host = "av.internal"
        self.config.clamav_port = 4000
        self.config.clamav_timeout = 10.0
        self.config.save()
        mock_clamd_cls.return_value.instream.return_value = {"stream": ("OK", "")}
        NoVirusValidator()(self._uploaded_file())
        mock_clamd_cls.assert_called_once_with(
            host="av.internal", port=4000, timeout=10.0
        )
