from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext as _

from ..validators import validate_api_root


class KvKAPIRootValidationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.error_msg = _(
            "The API root is incorrect. Please double-check that the host is correct "
            "and you didn't include the version number or endpoint."
        )

    def test_invalid_because_version_number_or_endpoint_included(self):
        test_cases = (
            "https://api.kvk.nl/api/v1",
            "https://api.kvk.nl/api/v1/test",
            "https://api.kvk.nl/api/123",
        )
        for i, test_string in enumerate(test_cases):
            with self.subTest(i=i):
                with self.assertRaisesMessage(ValidationError, self.error_msg):
                    validate_api_root(test_string)

    def test_invalid_kvk_host(self):
        test_cases = (
            "https://kvk.api.nl/api",
            "https://apii.kvk.nl/test/api",
            "http://api.kvk.nl/",
        )
        for i, test_string in enumerate(test_cases):
            with self.subTest(i=i):
                with self.assertRaisesMessage(ValidationError, self.error_msg):
                    validate_api_root(test_string)

    def test_valid_kvk_api_root(self):
        test_cases = (
            "https://api.kvk.nl/api",
            "https://api.kvk.nl/api/",
            "https://api.kvk.nl/test/api",
            "https://api.kvk.nl/test/api/",
        )
        for i, test_string in enumerate(test_cases):
            with self.subTest(i=i):
                validate_api_root(test_string)
