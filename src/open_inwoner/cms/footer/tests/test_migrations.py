import importlib
import json
import unittest.mock as mock

from django.db import connection
from django.test import SimpleTestCase, tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations

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


def _text_with_link(text, href):
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "marks": [{"type": "link", "attrs": {"href": href}}],
                    }
                ],
            }
        ],
    }


@tag("migrations")
class SanitizeProsemirrorLinkHrefsMigrationTest(TestSuccessfulMigrations):
    """
    Test migration 0007: strip unsafe hrefs from stored prosemirror link marks
    on CMSFlatPageModel.content.
    """

    migrate_from = "0006_alter_cmsflatpagemodel_content"
    migrate_to = "0007_sanitize_prosemirror_link_hrefs"
    app = "footer"

    def setUpBeforeMigration(self, apps):
        Placeholder = apps.get_model("cms", "Placeholder")
        placeholder = Placeholder.objects.create(slot="content")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin
                    (placeholder_id, language, plugin_type, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (placeholder.id, "nl", "CMSFlatPagePlugin", 0),
            )
            self.plugin_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO footer_cmsflatpagemodel (cmsplugin_ptr_id, title, content) "
                "VALUES (%s, %s, %s::jsonb)",
                (
                    self.plugin_id,
                    "",
                    json.dumps(_text_with_link("click", "javascript:alert(1)")),
                ),
            )

    def test_unsafe_href_stripped_from_content(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT content::text FROM footer_cmsflatpagemodel "
                "WHERE cmsplugin_ptr_id = %s",
                (self.plugin_id,),
            )
            doc = json.loads(cursor.fetchone()[0])
        text_node = doc["content"][0]["content"][0]
        self.assertEqual(text_node["marks"], [])
        self.assertEqual(text_node["text"], "click")
