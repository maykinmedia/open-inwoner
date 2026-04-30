import importlib
import unittest.mock as mock

from django.test import SimpleTestCase

_migration = importlib.import_module(
    "open_inwoner.cms.footer.migrations.0002_migrate_flatpages_content_to_cms"
)
_html_to_pm_doc = _migration._html_to_pm_doc


class HtmlToPmDocTest(SimpleTestCase):
    def test_none_returns_none(self):
        self.assertIsNone(_html_to_pm_doc(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(_html_to_pm_doc(""))

    def test_whitespace_only_returns_none(self):
        self.assertIsNone(_html_to_pm_doc("   "))

    def test_valid_html_returns_prosemirror_doc(self):
        result = _html_to_pm_doc("<p>Hello <strong>world</strong></p>")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "doc")

    def test_heading_is_preserved(self):
        result = _html_to_pm_doc("<h2>Title</h2><p>Body</p>")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "doc")

    def test_unparseable_html_returns_none(self):
        with mock.patch.object(
            _migration, "html_to_doc", side_effect=Exception("parse error")
        ):
            result = _html_to_pm_doc("<p>content</p>")
        self.assertIsNone(result)
