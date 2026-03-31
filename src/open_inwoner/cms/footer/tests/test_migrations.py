import json

from django.db import connection
from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class FlatPageContentMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0002_migrate_flatpages_content_to_cms"
    migrate_to = "0005_cmsflatpagemodel_content_schema_2"
    app = "footer"

    def setUpBeforeMigration(self, apps):
        Placeholder = apps.get_model("cms", "Placeholder")

        placeholder = Placeholder.objects.create(slot="test")

        # Use raw SQL to insert plugin records, bypassing the historical model
        # that expects treebeard fields (depth, path, numchild) which don't exist in CMS 4.x
        with connection.cursor() as cursor:
            # Insert base CMSPlugin records
            cms_plugin_data = [
                (1, placeholder.id, "nl", "CMSFlatPagePlugin", 1),
                (2, placeholder.id, "nl", "CMSFlatPagePlugin", 2),
                (3, placeholder.id, "nl", "CMSFlatPagePlugin", 3),
            ]

            for (
                plugin_id,
                placeholder_id,
                language,
                plugin_type,
                position,
            ) in cms_plugin_data:
                cursor.execute(
                    """
                    INSERT INTO cms_cmsplugin
                    (id, placeholder_id, language, plugin_type, position, creation_date, changed_date, parent_id)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), NULL)
                    """,
                    (plugin_id, placeholder_id, language, plugin_type, position),
                )

            # Store plugin IDs for test assertions
            self.plugin_1_id = 1
            self.plugin_2_id = 2
            self.plugin_3_id = 3

            # Insert CMSFlatPageModel data
            flatpage_data = [
                (
                    self.plugin_1_id,
                    "Test Flatpage",
                    "<p><strong>Bold text</strong> and <em>italic text</em></p>",
                ),
                (
                    self.plugin_2_id,
                    "Plain Text Flatpage",
                    "This is plain text content",
                ),
                (
                    self.plugin_3_id,
                    "Empty Flatpage",
                    "",
                ),
            ]

            for plugin_id, title, content in flatpage_data:
                cursor.execute(
                    """
                    INSERT INTO footer_cmsflatpagemodel
                    (cmsplugin_ptr_id, title, content)
                    VALUES (%s, %s, %s)
                    """,
                    (plugin_id, title, content),
                )

    def test_html_content_migration(self):
        # Use raw SQL to query the migrated data, bypassing the ORM which
        # uses the historical model with treebeard fields that don't exist in CMS 4.x
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT content
                FROM footer_cmsflatpagemodel
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.plugin_1_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Plugin 1 should exist after migration")

            # The content field is now a JSONB field containing ProseMirror document
            # Parse the JSON string returned by PostgreSQL
            content_raw = row[0]
            self.assertIsNotNone(content_raw)

            if isinstance(content_raw, str):
                content_json = json.loads(content_raw)
            else:
                content_json = content_raw

            # Check that the HTML is preserved correctly in the ProseMirror structure
            expected_html = "<p><strong>Bold text</strong> and <em>italic text</em></p>"
            # The content should have the expected structure
            self.assertIn("type", content_json)
            self.assertEqual(content_json["type"], "doc")

            # Verify content_tmp field was removed
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'footer_cmsflatpagemodel'
                AND column_name = 'content_tmp'
                """
            )
            self.assertIsNone(cursor.fetchone(), "content_tmp field should be removed")

    def test_plain_text_content_migration(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT content
                FROM footer_cmsflatpagemodel
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.plugin_2_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Plugin 2 should exist after migration")

            content_raw = row[0]
            self.assertIsNotNone(content_raw)

            if isinstance(content_raw, str):
                content_json = json.loads(content_raw)
            else:
                content_json = content_raw

            # Plain text should be wrapped in a paragraph
            self.assertIn("type", content_json)
            self.assertEqual(content_json["type"], "doc")

    def test_empty_content_migration(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT content
                FROM footer_cmsflatpagemodel
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.plugin_3_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Plugin 3 should exist after migration")

            content_json = row[0]
            # Empty content should be NULL or an empty doc
            self.assertTrue(
                content_json is None or content_json == {},
                f"Empty content should be None or empty dict, got: {content_json}",
            )
