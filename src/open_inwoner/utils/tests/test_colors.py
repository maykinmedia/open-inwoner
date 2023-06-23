from django.test import TestCase

from open_inwoner.utils.colors import get_contrast_ratio, hex_to_hsl, hex_to_luminance


class ColorUtilsTestCase(TestCase):
    def test_hex_to_hsl(self):
        tests = [
            ("#000000", (0, 0, 0)),
            ("#ffffff", (0, 0, 100)),
            ("#ff0000", (0, 100, 50)),
            ("#00ff00", (120, 100, 50)),
            ("#0000ff", (240, 100, 50)),
            ("#CCCCFF", (240, 100, 90)),
        ]

        for i, (hex, expected) in enumerate(tests):
            with self.subTest(i=i, hex=hex, expected=expected):
                actual = hex_to_hsl(hex)
                self.assertEqual(actual, expected)

    def test_hex_to_luminance(self):
        tests = [
            ("#000000", 0),
            ("#ffffff", 1),
            ("#ff0000", 0.2126),
            ("#00ff00", 0.7152),
            ("#0000ff", 0.0722),
            ("#CCCCFF", 0.6324),
        ]

        for i, (hex, expected) in enumerate(tests):
            with self.subTest(i=i, hex=hex, expected=expected):
                actual = hex_to_luminance(hex)
                self.assertAlmostEqual(actual, expected, places=3)

    def test_get_contrast_ratio(self):
        tests = [
            ("#000000", "#ffffff", 21.0),
            ("#ffffff", "#000000", 21.0),
            ("#ffffff", "#ffffff", 1.0),
            ("#ffffff", "#ffff00", 1.074),
            ("#ffffff", "#0000ff", 8.592),
        ]

        for i, (fore_hex, back_hex, expected) in enumerate(tests):
            with self.subTest(i=i, hex=hex, expected=expected):
                actual = get_contrast_ratio(fore_hex, back_hex)
                self.assertAlmostEqual(actual, expected, places=3)
