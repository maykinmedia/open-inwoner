from django.core.exceptions import ValidationError
from django.test import TestCase

from open_inwoner.haalcentraal.models import HaalCentraalConfig
from open_inwoner.haalcentraal.validators import (
    STANDARD_HTTP_HEADERS,
    validate_no_standard_http_headers,
)


class TestHeadersValidatorWiring(TestCase):
    def test_validator_is_registered_on_headers_field(self):
        field = HaalCentraalConfig._meta.get_field("headers")
        self.assertIn(validate_no_standard_http_headers, field.validators)


class TestHeadersValidatorShape(TestCase):
    def test_non_list_rejected(self):
        config = HaalCentraalConfig.get_solo()
        config.headers = {"content-type": "application/json"}
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_item_missing_key_field_rejected(self):
        config = HaalCentraalConfig.get_solo()
        config.headers = [{"value": "application/json"}]
        with self.assertRaises(ValidationError):
            config.full_clean()


class TestHeadersValidator(TestCase):
    def test_standard_http_header_rejected(self):
        config = HaalCentraalConfig.get_solo()
        config.headers = [{"key": "content-type", "value": "application/json"}]
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_standard_http_headers_case_insensitive(self):
        config = HaalCentraalConfig.get_solo()
        config.headers = [{"key": "Authorization", "value": "Bearer token"}]
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_all_standard_headers_rejected(self):
        config = HaalCentraalConfig.get_solo()
        for header in STANDARD_HTTP_HEADERS:
            config.headers = [{"key": header, "value": "test"}]
            with self.assertRaises(ValidationError, msg=f"{header} should be rejected"):
                config.full_clean()

    def test_custom_header_accepted(self):
        from open_inwoner.haalcentraal.validators import (
            validate_no_standard_http_headers,
        )

        # Should not raise
        validate_no_standard_http_headers(
            [{"key": "x-origin-oin", "value": "00000001234567890000"}]
        )
