from django.test import TestCase

from open_inwoner.utils.css import clean_stylesheet


class CSSUtilsTestCase(TestCase):
    def test_clean_stylesheet_multi(self):
        tests = [
            (
                "* {color: #fff;}",
                "* {color: #fff;}",
            ),
            (
                "p { color: #fff; }",
                "p {color: #fff; }",
            ),
            (
                "p {color: #fff; \n cursor: hand; \n font-size: 10px;}",
                "p {color: #fff; \n cursor: hand; \n font-size: 10px;}",
            ),
            # props not allowed
            ("p { unknown-prop: 0%;}", ""),
            (
                "p {color: #fff; \n unknown-prop: 0%; \n font-size: 10px;}",
                "p {color: #fff; \n font-size: 10px;}",
            ),
            # ignore space and comments
            ("", ""),
            (" \n ", ""),
            ("/* foo */\n \n", ""),
            ("/* foo */\n \n", ""),
        ]
        for i, (css, expected) in enumerate(tests):
            with self.subTest(i=i):
                self.assertEqual(expected, clean_stylesheet(css))

    def test_clean_stylesheet_arguments(self):
        allowed_props = ["width"]
        css = "body { width:10px; color: #fff;}"
        expected = "body {width:10px; }"

        self.assertEqual(
            expected, clean_stylesheet(css, allowed_properties=allowed_props)
        )

    def test_clean_stylesheet_allows_any_string(self):
        """
        proves we need to escape this if we print in html
        """
        css = 'body {color: "/style><script>evil();</script><style ";}'
        expected = css

        self.assertEqual(expected, clean_stylesheet(css))
