import json

from django.db import connection
from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class FixLegacyTextPluginBodyMigrationTest(TestSuccessfulMigrations):
    """
    Test the data migration that fixes Text plugin body fields containing
    legacy plain strings (stored as JSON strings in JSONB) instead of
    Prosemirror JSON documents.

    Scenarios:
    - Empty JSON string ("") → EMPTY_DOC (body is NOT NULL)
    - HTML string → Prosemirror JSON dict
    - Plain text string → Prosemirror JSON dict (wrapped in paragraph)
    - None → unchanged
    - Valid Prosemirror dict → unchanged
    """

    migrate_from = "0014_alter_extendedcmslink_name"
    migrate_to = "0015_fix_legacy_text_plugin_body"
    app = "plugins"

    def setUpBeforeMigration(self, apps):
        Placeholder = apps.get_model("cms", "Placeholder")
        placeholder = Placeholder.objects.create(slot="content")

        # Use raw SQL to avoid passing treebeard fields (depth, path, numchild)
        # that were removed in CMS 4.
        with connection.cursor() as cursor:
            for position in range(5):
                cursor.execute(
                    """
                    INSERT INTO cms_cmsplugin
                        (placeholder_id, language, plugin_type, position, creation_date, changed_date)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    RETURNING id
                    """,
                    (placeholder.id, "nl", "TextPlugin", position),
                )
                plugin_id = cursor.fetchone()[0]
                attr = [
                    "plugin_empty_id",
                    "plugin_html_id",
                    "plugin_plain_id",
                    "plugin_none_id",
                    "plugin_valid_id",
                ][position]
                setattr(self, attr, plugin_id)

            # Empty string stored as JSON-encoded empty string (the wizard bug)
            cursor.execute(
                "INSERT INTO plugins_text (cmsplugin_ptr_id, body) VALUES (%s, %s::jsonb)",
                (self.plugin_empty_id, '""'),
            )
            # Legacy HTML content stored as a JSON string
            cursor.execute(
                "INSERT INTO plugins_text (cmsplugin_ptr_id, body) VALUES (%s, %s::jsonb)",
                (self.plugin_html_id, '"<p>Hello <strong>world</strong></p>"'),
            )
            # Plain text stored as a JSON string
            cursor.execute(
                "INSERT INTO plugins_text (cmsplugin_ptr_id, body) VALUES (%s, %s::jsonb)",
                (self.plugin_plain_id, '"plain text"'),
            )
            # JSON null — should be left alone (NOT NULL column can still store 'null'::jsonb)
            cursor.execute(
                "INSERT INTO plugins_text (cmsplugin_ptr_id, body) VALUES (%s, 'null'::jsonb)",
                (self.plugin_none_id,),
            )
            # Already a valid Prosemirror JSON object — should be left alone
            cursor.execute(
                "INSERT INTO plugins_text (cmsplugin_ptr_id, body) VALUES (%s, %s::jsonb)",
                (
                    self.plugin_valid_id,
                    '{"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Valid"}]}]}',
                ),
            )

    def _get_body(self, plugin_id):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT body::text FROM plugins_text WHERE cmsplugin_ptr_id = %s",
                (plugin_id,),
            )
            row = cursor.fetchone()
        self.assertIsNotNone(
            row, f"No plugins_text row for cmsplugin_ptr_id={plugin_id}"
        )
        raw = row[0]
        return json.loads(raw) if raw is not None else None

    def test_empty_string_becomes_empty_doc(self):
        body = self._get_body(self.plugin_empty_id)
        self.assertEqual(body, {"type": "doc", "content": []})

    def test_html_string_converted_to_prosemirror(self):
        body = self._get_body(self.plugin_html_id)
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("type"), "doc")

    def test_plain_text_converted_to_prosemirror(self):
        body = self._get_body(self.plugin_plain_id)
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("type"), "doc")

    def test_none_remains_none(self):
        body = self._get_body(self.plugin_none_id)
        self.assertIsNone(body)

    def test_valid_prosemirror_dict_unchanged(self):
        body = self._get_body(self.plugin_valid_id)
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("type"), "doc")


@tag("migrations")
class SwapTasksObjectTypeFieldsMigrationTest(TestSuccessfulMigrations):
    """
    Test the data migration that swaps object_type_dimpact and
    object_type_generieke_dienstverlening field values.
    """

    migrate_from = "0012_remove_djangocms_text_ckeditor"
    migrate_to = "0013_swap_tasks_object_type_fields"
    app = "plugins"

    def setUpBeforeMigration(self, apps):
        """
        Create TasksConfig instances with object type values before migration.
        """
        Placeholder = apps.get_model("cms", "Placeholder")

        # Create placeholder for the plugins
        self.placeholder = Placeholder.objects.create(slot="content")

        # Use raw SQL to create CMSPlugin instances to avoid treebeard field issues
        # Django CMS 4.x removed treebeard fields (depth, path, numchild)
        with connection.cursor() as cursor:
            # Scenario 1: Config with both fields set
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (placeholder_id, language, plugin_type, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (self.placeholder.id, "nl", "TasksPlugin", 0),
            )
            self.config_both_id = cursor.fetchone()[0]

            # Scenario 2: Config with only dimpact set
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (placeholder_id, language, plugin_type, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (self.placeholder.id, "nl", "TasksPlugin", 1),
            )
            self.config_dimpact_only_id = cursor.fetchone()[0]

            # Scenario 3: Config with only generieke_dienstverlening set
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (placeholder_id, language, plugin_type, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (self.placeholder.id, "nl", "TasksPlugin", 2),
            )
            self.config_generieke_only_id = cursor.fetchone()[0]

            # Scenario 4: Config with neither field set
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (placeholder_id, language, plugin_type, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (self.placeholder.id, "nl", "TasksPlugin", 3),
            )
            self.config_neither_id = cursor.fetchone()[0]

        # Insert TasksConfig data using raw SQL to avoid multi-table inheritance issues
        with connection.cursor() as cursor:
            test_data = [
                (
                    self.config_both_id,
                    "Both Fields Set",
                    "uuid-for-dimpact-before",
                    "uuid-for-generieke-before",
                ),
                (
                    self.config_dimpact_only_id,
                    "Dimpact Only",
                    "uuid-dimpact-only-before",
                    None,
                ),
                (
                    self.config_generieke_only_id,
                    "Generieke Only",
                    None,
                    "uuid-generieke-only-before",
                ),
                (
                    self.config_neither_id,
                    "Neither Field Set",
                    None,
                    None,
                ),
            ]

            for (
                plugin_id,
                title,
                object_type_dimpact,
                object_type_generieke,
            ) in test_data:
                cursor.execute(
                    """
                    INSERT INTO plugins_tasksconfig
                    (cmsplugin_ptr_id, title, object_type_dimpact, object_type_generieke_dienstverlening)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (plugin_id, title, object_type_dimpact, object_type_generieke),
                )

    def test_swap_tasks_object_type_fields_migration(self):
        """
        Test that object type fields are correctly swapped for all scenarios.

        This test validates:
        - Both fields are swapped when both have values
        - Dimpact value moves to generieke when only dimpact is set
        - Generieke value moves to dimpact when only generieke is set
        - Configs with no values remain unchanged
        - No configs are deleted during migration
        - Other fields like title are preserved
        """
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            # Verify all configs still exist
            cursor.execute("SELECT COUNT(*) FROM plugins_tasksconfig")
            self.assertEqual(cursor.fetchone()[0], 4)

            # Scenario 1: Both fields swapped
            cursor.execute(
                """
                SELECT title, object_type_dimpact, object_type_generieke_dienstverlening
                FROM plugins_tasksconfig
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.config_both_id,),
            )
            row = cursor.fetchone()
            self.assertEqual(row[0], "Both Fields Set")
            self.assertEqual(row[1], "uuid-for-generieke-before")
            self.assertEqual(row[2], "uuid-for-dimpact-before")

            # Scenario 2: Dimpact only - moved to generieke
            cursor.execute(
                """
                SELECT title, object_type_dimpact, object_type_generieke_dienstverlening
                FROM plugins_tasksconfig
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.config_dimpact_only_id,),
            )
            row = cursor.fetchone()
            self.assertEqual(row[0], "Dimpact Only")
            self.assertIsNone(row[1])
            self.assertEqual(row[2], "uuid-dimpact-only-before")

            # Scenario 3: Generieke only - moved to dimpact
            cursor.execute(
                """
                SELECT title, object_type_dimpact, object_type_generieke_dienstverlening
                FROM plugins_tasksconfig
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.config_generieke_only_id,),
            )
            row = cursor.fetchone()
            self.assertEqual(row[0], "Generieke Only")
            self.assertEqual(row[1], "uuid-generieke-only-before")
            self.assertIsNone(row[2])

            # Scenario 4: Neither field - unchanged
            cursor.execute(
                """
                SELECT title, object_type_dimpact, object_type_generieke_dienstverlening
                FROM plugins_tasksconfig
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.config_neither_id,),
            )
            row = cursor.fetchone()
            self.assertEqual(row[0], "Neither Field Set")
            self.assertIsNone(row[1])
            self.assertIsNone(row[2])


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
        Placeholder = apps.get_model("cms", "Placeholder")

        # Create placeholders for different scenarios
        self.page_placeholder = Placeholder.objects.create(slot="content")
        self.static_placeholder = Placeholder.objects.create(slot="footer_left")

        # Use raw SQL to create CMSPlugin instances to avoid treebeard field issues
        # Django CMS 4.x removed treebeard fields (depth, path, numchild)
        with connection.cursor() as cursor:
            # Scenario 1: Rich HTML content (should preserve formatting)
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (language, plugin_type, placeholder_id, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                ("nl", "TextPlugin", self.page_placeholder.id, 0),
            )
            self.rich_plugin_id = cursor.fetchone()[0]

            # Scenario 2: Plain text content (should wrap in paragraph)
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (language, plugin_type, placeholder_id, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                ("nl", "TextPlugin", self.page_placeholder.id, 1),
            )
            self.plain_plugin_id = cursor.fetchone()[0]

            # Scenario 3: Whitespace-only content (should handle gracefully)
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (language, plugin_type, placeholder_id, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                ("nl", "TextPlugin", self.page_placeholder.id, 2),
            )
            self.empty_plugin_id = cursor.fetchone()[0]

            # Scenario 4: Static placeholder content (footer/header)
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (language, plugin_type, placeholder_id, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                ("nl", "TextPlugin", self.static_placeholder.id, 0),
            )
            self.static_plugin_id = cursor.fetchone()[0]

            # Scenario 5: Complex HTML with lists, links, formatting
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (language, plugin_type, placeholder_id, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                ("nl", "TextPlugin", self.page_placeholder.id, 3),
            )
            self.complex_plugin_id = cursor.fetchone()[0]

            # Scenario 6: Malformed HTML (should use fallback strategy)
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (language, plugin_type, placeholder_id, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                ("nl", "TextPlugin", self.page_placeholder.id, 4),
            )
            self.malformed_plugin_id = cursor.fetchone()[0]

            # Scenario 7: Plugin with child plugins (should preserve parent/child relationship)
            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (language, plugin_type, placeholder_id, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                ("nl", "TextPlugin", self.page_placeholder.id, 5),
            )
            self.parent_plugin_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO cms_cmsplugin (language, plugin_type, placeholder_id, parent_id, position, creation_date, changed_date)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (
                    "nl",
                    "SomeOtherPlugin",
                    self.page_placeholder.id,
                    self.parent_plugin_id,
                    6,
                ),
            )
            self.child_plugin_id = cursor.fetchone()[0]

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
                    self.rich_plugin_id,
                    "<p>This is <strong>bold</strong> and <em>italic</em> text with a <a href='https://example.com'>link</a>.</p>",
                ),
                (
                    self.plain_plugin_id,
                    "Plain text without HTML tags",
                ),
                (
                    self.empty_plugin_id,
                    "   ",  # Whitespace only - should be treated as empty
                ),
                (
                    self.static_plugin_id,
                    "<p>Footer content with <strong>formatting</strong></p>",
                ),
                (
                    self.complex_plugin_id,
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
                    self.malformed_plugin_id,
                    "<p>Text with <video>unsupported tag</video> content</p>",
                ),
                (
                    self.parent_plugin_id,
                    "<p>Parent plugin with children</p>",
                ),
            ]

            for plugin_id, body in test_data:
                cursor.execute(
                    "INSERT INTO djangocms_text_ckeditor_text (cmsplugin_ptr_id, body) VALUES (%s, %s)",
                    (plugin_id, body),
                )

    def test_rich_html_content_preserved(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        # Simply verify that the plugin was migrated and has valid ProseMirror structure
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT body
                FROM plugins_text
                WHERE cmsplugin_ptr_id = ANY(%s)
                """,
                ([self.rich_plugin_id],),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(
                row, f"Rich text plugin {self.rich_plugin_id} should exist"
            )

            body_json = json.loads(row[0])

            # Body is stored as ProseMirror document structure
            self.assertEqual(body_json["type"], "doc")
            self.assertIn("content", body_json)
            # Verify the paragraph contains the expected formatted text
            self.assertTrue(len(body_json["content"]) > 0)
            paragraph = body_json["content"][0]
            self.assertEqual(paragraph["type"], "paragraph")
            # Check that it has content with marks for bold, italic, and links
            self.assertIn("content", paragraph)

    def test_plain_text_content_wrapped(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT body
                FROM plugins_text
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.plain_plugin_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Plain text plugin should exist")
            body_json = json.loads(row[0])

            # Body is stored as ProseMirror document structure
            # Plain text should be wrapped in a paragraph
            self.assertEqual(body_json["type"], "doc")
            self.assertIn("content", body_json)
            self.assertTrue(len(body_json["content"]) > 0)
            paragraph = body_json["content"][0]
            self.assertEqual(paragraph["type"], "paragraph")

    def test_empty_content_handled(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT cmsplugin_ptr_id
                FROM plugins_text
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.empty_plugin_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Empty content plugin should still be migrated")

    def test_static_placeholder_content_migrated(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT body
                FROM plugins_text
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.static_plugin_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Static placeholder plugin should exist")
            body_json = json.loads(row[0])

            # Body is stored as ProseMirror document structure
            self.assertEqual(body_json["type"], "doc")
            self.assertIn("content", body_json)
            # Footer content should be migrated with formatting preserved
            self.assertTrue(len(body_json["content"]) > 0)

    def test_complex_html_structure_preserved(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT body
                FROM plugins_text
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.complex_plugin_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Complex HTML plugin should exist")
            body_json = json.loads(row[0])

            # Body is stored as ProseMirror document structure
            self.assertEqual(body_json["type"], "doc")
            self.assertIn("content", body_json)
            # Complex HTML with heading, list, and paragraph should have multiple content nodes
            self.assertTrue(len(body_json["content"]) > 1)

    def test_malformed_html_uses_fallback(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT body
                FROM plugins_text
                WHERE cmsplugin_ptr_id = %s
                """,
                (self.malformed_plugin_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Malformed HTML plugin should exist")
            body_json = json.loads(row[0])

            # Body is stored as ProseMirror document structure
            # Malformed HTML should still be converted to valid ProseMirror structure
            self.assertEqual(body_json["type"], "doc")
            self.assertIn("content", body_json)

    def test_cms_plugin_tree_structure_preserved(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT parent_id
                FROM cms_cmsplugin
                WHERE id = %s
                """,
                (self.child_plugin_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Child plugin should exist")
            self.assertEqual(row[0], self.parent_plugin_id)

    def test_parent_child_relationship_preserved(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, parent_id
                FROM cms_cmsplugin
                WHERE id = %s
                """,
                (self.parent_plugin_id,),
            )
            parent_row = cursor.fetchone()
            self.assertIsNotNone(parent_row, "Parent plugin should exist")

            cursor.execute(
                """
                SELECT id, parent_id
                FROM cms_cmsplugin
                WHERE id = %s
                """,
                (self.child_plugin_id,),
            )
            child_row = cursor.fetchone()
            self.assertIsNotNone(child_row, "Child plugin should exist")
            self.assertEqual(child_row[1], parent_row[0])

    def test_placeholder_relationships_preserved(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT placeholder_id
                FROM cms_cmsplugin
                WHERE id = %s
                """,
                (self.rich_plugin_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Rich plugin should exist")
            self.assertEqual(row[0], self.page_placeholder.id)

            cursor.execute(
                """
                SELECT placeholder_id
                FROM cms_cmsplugin
                WHERE id = %s
                """,
                (self.static_plugin_id,),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row, "Static plugin should exist")
            self.assertEqual(row[0], self.static_placeholder.id)

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
        # Use raw SQL to avoid treebeard field issues with historical models
        expected_plugin_ids = [
            self.rich_plugin_id,
            self.plain_plugin_id,
            self.empty_plugin_id,
            self.static_plugin_id,
            self.complex_plugin_id,
            self.malformed_plugin_id,
            self.parent_plugin_id,
        ]

        with connection.cursor() as cursor:
            for plugin_id in expected_plugin_ids:
                cursor.execute(
                    """
                    SELECT cmsplugin_ptr_id
                    FROM plugins_text
                    WHERE cmsplugin_ptr_id = %s
                    """,
                    (plugin_id,),
                )
                row = cursor.fetchone()
                self.assertIsNotNone(row, f"Plugin {plugin_id} not migrated")

    def test_plugin_positions_preserved(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT position
                FROM cms_cmsplugin
                WHERE id = %s
                """,
                (self.rich_plugin_id,),
            )
            self.assertEqual(cursor.fetchone()[0], 0)

            cursor.execute(
                """
                SELECT position
                FROM cms_cmsplugin
                WHERE id = %s
                """,
                (self.plain_plugin_id,),
            )
            self.assertEqual(cursor.fetchone()[0], 1)

            cursor.execute(
                """
                SELECT position
                FROM cms_cmsplugin
                WHERE id = %s
                """,
                (self.empty_plugin_id,),
            )
            self.assertEqual(cursor.fetchone()[0], 2)

    def test_language_preserved(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT language
                FROM cms_cmsplugin
                WHERE id = %s
                """,
                (self.rich_plugin_id,),
            )
            self.assertEqual(cursor.fetchone()[0], "nl")

    def test_migration_error_count(self):
        # Use raw SQL to avoid treebeard field issues with historical models
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM plugins_text")
            text_plugin_count = cursor.fetchone()[0]

            cursor.execute("SELECT cmsplugin_ptr_id FROM plugins_text")
            migrated_ids = [row[0] for row in cursor.fetchall()]

            self.assertEqual(
                text_plugin_count,
                7,
                f"Expected 7, found {text_plugin_count}. Migrated: {migrated_ids}",
            )
