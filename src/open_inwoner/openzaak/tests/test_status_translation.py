from django.test import TestCase

from open_inwoner.openzaak.models import StatusTranslation
from open_inwoner.openzaak.tests.factories import StatusTranslationFactory
from open_inwoner.openzaak.utils import translate_single_status


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
        #    src/open_inwoner/utils/tests/test_translate.py

    def test_helper(self):
        StatusTranslationFactory(status="foo", translation="FOO")
        self.assertEqual("FOO", translate_single_status("foo"))
        self.assertEqual("not_translated", translate_single_status("not_translated"))
