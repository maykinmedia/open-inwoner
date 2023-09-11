from django.test import TestCase

from open_inwoner.openzaak.models import StatusTranslation
from open_inwoner.openzaak.tests.factories import StatusTranslationFactory


class StatusTranslationModelTest(TestCase):
    def test_lookup(self):
        StatusTranslationFactory(status="foo", translation="FOO")
        StatusTranslationFactory(status="bar", translation="BAR")

        lookup = StatusTranslation.objects.get_lookup()

        tests = [
            # input, expected
            ("foo", "FOO"),
            ("bar", "BAR"),
            ("bazz", "bazz"),
            ("", ""),
        ]
        for value, expected in tests:
            with self.subTest(value=value, expected=expected):
                actual = lookup(value)
                self.assertEqual(expected, actual)

        # NOTE the TranslationLookup helper is further tested in its own file
