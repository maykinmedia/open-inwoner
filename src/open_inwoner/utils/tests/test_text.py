from django.test import TestCase
from django.utils.safestring import mark_safe

from open_inwoner.utils.text import html_tag_wrap_format, middle_truncate


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
