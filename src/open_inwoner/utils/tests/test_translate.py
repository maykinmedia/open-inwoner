from django.test import TestCase

from open_inwoner.utils.translate import TranslationLookup


class TranslationLookupTest(TestCase):
    def test_lookup(self):
        values_list = [
            ("foo", "FOO"),
            ("bar", "BAR"),
        ]
        lookup = TranslationLookup(values_list)

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

        # extra
        with self.subTest("normal key with default returns key"):
            actual = lookup("bazz", default="buzz")
            self.assertEqual("bazz", actual)

        with self.subTest("empty key with default return default"):
            actual = lookup("", default="buzz")
            self.assertEqual("buzz", actual)

    def test_lookup_from_glom(self):
        values_list = [
            ("foo", "FOO"),
            ("bar", "BAR"),
        ]
        lookup = TranslationLookup(values_list)

        data = {
            "aaa": {
                "fff": "foo",
                "bbb": "bar",
                "zzz": "bazz",
            },
        }

        tests = [
            # input, expected
            ("aaa.fff", "FOO"),
            ("aaa.bbb", "BAR"),
            ("aaa.zzz", "bazz"),
            ("aaa.xxx", ""),
            ("", ""),
        ]
        for value, expected in tests:
            with self.subTest(value=value, expected=expected):
                actual = lookup.from_glom(data, value)
                self.assertEqual(expected, actual)

        with self.subTest("with default"):
            actual = lookup.from_glom(data, "aaa.xxx", default="buzz")
            self.assertEqual("buzz", actual)

        with self.subTest("with empty default"):
            actual = lookup.from_glom(data, "aaa.xxx", default="")
            self.assertEqual("", actual)
