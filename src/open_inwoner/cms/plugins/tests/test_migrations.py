from django.db import connection
from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class CKEditorToTextPluginMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0011_alter_tasksconfig_object_type_dimpact_and_more"
    migrate_to = "0012_remove_djangocms_text_ckeditor"
    app = "plugins"

    def setUpBeforeMigration(self, apps):
        """
        Create test data in old CKEditor format before migration runs.

        This migration is complex because:
        1. The old plugin table (djangocms_text_ckeditor_text) has no Django model
        2. Both old and new plugins use plugin_type='TextPlugin'
        3. Must preserve cms_cmsplugin tree structure (depth, path, numchild)
        4. Must handle HTML conversion failures gracefully
        5. Must handle orphaned plugins
        """
        CMSPlugin = apps.get_model("cms", "CMSPlugin")
        Placeholder = apps.get_model("cms", "Placeholder")

        # Create placeholders for different scenarios
        self.page_placeholder = Placeholder.objects.create(slot="content")
        self.static_placeholder = Placeholder.objects.create(slot="footer_left")

        # Scenario 1: Rich HTML content (should preserve formatting)
        self.rich_plugin = CMSPlugin.objects.create(
            language="nl",
            plugin_type="TextPlugin",
            placeholder=self.page_placeholder,
            position=0,
            path="0001",
            depth=1,
            numchild=0,
        )

        # Scenario 2: Plain text content (should wrap in paragraph)
        self.plain_plugin = CMSPlugin.objects.create(
            language="nl",
            plugin_type="TextPlugin",
            placeholder=self.page_placeholder,
            position=1,
            path="0002",
            depth=1,
            numchild=0,
        )

        # Scenario 3: Whitespace-only content (should handle gracefully)
        self.empty_plugin = CMSPlugin.objects.create(
            language="nl",
            plugin_type="TextPlugin",
            placeholder=self.page_placeholder,
            position=2,
            path="0003",
            depth=1,
            numchild=0,
        )

        # Scenario 4: Static placeholder content (footer/header)
        self.static_plugin = CMSPlugin.objects.create(
            language="nl",
            plugin_type="TextPlugin",
            placeholder=self.static_placeholder,
            position=0,
            path="0004",
            depth=1,
            numchild=0,
        )

        # Scenario 5: Complex HTML with lists, links, formatting
        self.complex_plugin = CMSPlugin.objects.create(
            language="nl",
            plugin_type="TextPlugin",
            placeholder=self.page_placeholder,
            position=3,
            path="0005",
            depth=1,
            numchild=0,
        )

        # Scenario 6: Malformed HTML (should use fallback strategy)
        self.malformed_plugin = CMSPlugin.objects.create(
            language="nl",
            plugin_type="TextPlugin",
            placeholder=self.page_placeholder,
            position=4,
            path="0006",
            depth=1,
            numchild=0,
        )

        # Scenario 7: Plugin with child plugins (should preserve tree)
        self.parent_plugin = CMSPlugin.objects.create(
            language="nl",
            plugin_type="TextPlugin",
            placeholder=self.page_placeholder,
            position=5,
            path="0007",
            depth=1,
            numchild=1,
        )
        self.child_plugin = CMSPlugin.objects.create(
            language="nl",
            plugin_type="SomeOtherPlugin",
            placeholder=self.page_placeholder,
            parent_id=self.parent_plugin.id,
            position=0,
            path="00070001",
            depth=2,
            numchild=0,
        )

        # Insert raw data into djangocms_text_ckeditor_text table
        with connection.cursor() as cursor:
            # Create the old CKEditor table (simulating it exists from old package)
            # Note: body field allows NULL in case of empty content
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS djangocms_text_ckeditor_text (
                    cmsplugin_ptr_id INTEGER PRIMARY KEY,
                    body TEXT
                )
            """)

            # Insert test data
            test_data = [
                (
                    self.rich_plugin.id,
                    "<p>This is <strong>bold</strong> and <em>italic</em> text with a <a href='https://example.com'>link</a>.</p>",
                ),
                (
                    self.plain_plugin.id,
                    "Plain text without HTML tags",
                ),
                (
                    self.empty_plugin.id,
                    "   ",  # Whitespace only - should be treated as empty
                ),
                (
                    self.static_plugin.id,
                    "<p>Footer content with <strong>formatting</strong></p>",
                ),
                (
                    self.complex_plugin.id,
                    """
                    <h2>Heading</h2>
                    <ul>
                        <li>Item 1</li>
                        <li>Item 2 with <strong>bold</strong></li>
                    </ul>
                    <p>Paragraph with <a href='#'>link</a> and <code>code</code>.</p>
                    """,
                ),
                (
                    self.malformed_plugin.id,
                    "<p>Text with <video>unsupported tag</video> content</p>",
                ),
                (
                    self.parent_plugin.id,
                    "<p>Parent plugin with children</p>",
                ),
            ]

            for plugin_id, body in test_data:
                cursor.execute(
                    "INSERT INTO djangocms_text_ckeditor_text (cmsplugin_ptr_id, body) VALUES (%s, %s)",
                    (plugin_id, body),
                )

    def test_rich_html_content_preserved(self):
        Text = self.apps.get_model("plugins", "Text")

        text_plugin = Text.objects.get(cmsplugin_ptr_id=self.rich_plugin.id)

        self.assertEqual(
            text_plugin.body.html,
            '<p>This is <strong>bold</strong> and <em>italic</em> text with a <a href="https://example.com">link</a>.</p>',
        )

    def test_plain_text_content_wrapped(self):
        Text = self.apps.get_model("plugins", "Text")

        text_plugin = Text.objects.get(cmsplugin_ptr_id=self.plain_plugin.id)

        self.assertEqual(
            text_plugin.body.html,
            "<p>Plain text without HTML tags</p>",
        )

    def test_empty_content_handled(self):
        Text = self.apps.get_model("plugins", "Text")

        text_plugin = Text.objects.filter(cmsplugin_ptr_id=self.empty_plugin.id).first()
        self.assertIsNotNone(
            text_plugin, "Empty content plugin should still be migrated"
        )

    def test_static_placeholder_content_migrated(self):
        Text = self.apps.get_model("plugins", "Text")

        text_plugin = Text.objects.get(cmsplugin_ptr_id=self.static_plugin.id)

        self.assertEqual(
            text_plugin.body.html,
            "<p>Footer content with <strong>formatting</strong></p>",
        )

    def test_complex_html_structure_preserved(self):
        Text = self.apps.get_model("plugins", "Text")

        text_plugin = Text.objects.get(cmsplugin_ptr_id=self.complex_plugin.id)

        self.assertEqual(
            text_plugin.body.html,
            '<h2>Heading</h2><ul><li><p>Item 1</p></li><li><p>Item 2 with <strong>bold</strong></p></li></ul><p>Paragraph with <a href="#">link</a> and <code>code</code>.</p>',
        )

    def test_malformed_html_uses_fallback(self):
        Text = self.apps.get_model("plugins", "Text")

        text_plugin = Text.objects.get(cmsplugin_ptr_id=self.malformed_plugin.id)

        self.assertEqual(
            text_plugin.body.html,
            "<p>Text with unsupported tag content</p>",
        )

    def test_cms_plugin_tree_structure_preserved(self):
        CMSPlugin = self.apps.get_model("cms", "CMSPlugin")

        parent = CMSPlugin.objects.get(id=self.parent_plugin.id)
        self.assertEqual(parent.depth, 1)
        self.assertEqual(parent.path, "0007")
        self.assertEqual(parent.numchild, 1)

        child = CMSPlugin.objects.get(id=self.child_plugin.id)
        self.assertEqual(child.depth, 2)
        self.assertEqual(child.path, "00070001")
        self.assertEqual(child.parent_id, self.parent_plugin.id)

    def test_parent_child_relationship_preserved(self):
        CMSPlugin = self.apps.get_model("cms", "CMSPlugin")

        parent = CMSPlugin.objects.get(id=self.parent_plugin.id)
        child = CMSPlugin.objects.get(id=self.child_plugin.id)

        self.assertEqual(child.parent_id, parent.id)

    def test_placeholder_relationships_preserved(self):
        CMSPlugin = self.apps.get_model("cms", "CMSPlugin")

        page_plugin = CMSPlugin.objects.get(id=self.rich_plugin.id)
        self.assertEqual(page_plugin.placeholder_id, self.page_placeholder.id)

        static_plugin = CMSPlugin.objects.get(id=self.static_plugin.id)
        self.assertEqual(static_plugin.placeholder_id, self.static_placeholder.id)

    def test_old_ckeditor_table_dropped(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'djangocms_text_ckeditor_text'
                )
            """)
            table_exists = cursor.fetchone()[0]

            remaining_records = []
            if table_exists:
                cursor.execute(
                    "SELECT cmsplugin_ptr_id FROM djangocms_text_ckeditor_text"
                )
                remaining_records = [row[0] for row in cursor.fetchall()]

        self.assertFalse(
            table_exists,
            f"Table should be dropped. Remaining records: {remaining_records}",
        )

    def test_all_plugins_migrated_to_new_text_model(self):
        Text = self.apps.get_model("plugins", "Text")

        expected_plugin_ids = [
            self.rich_plugin.id,
            self.plain_plugin.id,
            self.empty_plugin.id,
            self.static_plugin.id,
            self.complex_plugin.id,
            self.malformed_plugin.id,
            self.parent_plugin.id,
        ]

        for plugin_id in expected_plugin_ids:
            text_plugin = Text.objects.filter(cmsplugin_ptr_id=plugin_id).first()
            self.assertIsNotNone(text_plugin, f"Plugin {plugin_id} not migrated")

    def test_plugin_positions_preserved(self):
        CMSPlugin = self.apps.get_model("cms", "CMSPlugin")

        rich = CMSPlugin.objects.get(id=self.rich_plugin.id)
        plain = CMSPlugin.objects.get(id=self.plain_plugin.id)
        empty = CMSPlugin.objects.get(id=self.empty_plugin.id)

        self.assertEqual(rich.position, 0)
        self.assertEqual(plain.position, 1)
        self.assertEqual(empty.position, 2)

    def test_language_preserved(self):
        CMSPlugin = self.apps.get_model("cms", "CMSPlugin")

        plugin = CMSPlugin.objects.get(id=self.rich_plugin.id)
        self.assertEqual(plugin.language, "nl")

    def test_migration_error_count(self):
        Text = self.apps.get_model("plugins", "Text")

        text_plugin_count = Text.objects.count()
        migrated_ids = list(Text.objects.values_list("cmsplugin_ptr_id", flat=True))

        self.assertEqual(
            text_plugin_count,
            7,
            f"Expected 7, found {text_plugin_count}. Migrated: {migrated_ids}",
        )
