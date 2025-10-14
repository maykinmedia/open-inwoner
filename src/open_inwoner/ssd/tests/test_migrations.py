from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


class SSDConfigRichtTextMigrationTest(TestSuccessfulMigrations):
    migrate_from = (
        "0006_rename_jaaropgave_comments_ssdconfig_jaaropgave_pdf_comments_and_more"
    )
    migrate_to = "0018_ssdconfig_maandspecificatie_pdf_comments_schema_2"
    app = "ssd"

    def setUpBeforeMigration(self, apps):
        SSDConfig = apps.get_model("ssd", "SSDConfig")

        ssd_config = SSDConfig.objects.create()

        # Jaaropgave
        test_html = '<p>This is a <strong>test</strong> text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        ssd_config.jaaropgave_display_text = test_html

        test_html = "<p>These are PDF comments without formatting.</p>"
        ssd_config.jaaropgave_pdf_comments = test_html

        # Maandspecificatie
        test_html = '<p>This is a <strong>monthly statement</strong> text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        ssd_config.maandspecificatie_display_text = test_html

        test_html = (
            "<p>These are monthly statement PDF comments without formatting.</p>"
        )
        ssd_config.maandspecificatie_pdf_comments = test_html

        ssd_config.save()

    def test_migrate_rich_text(self):
        SSDConfig = self.apps.get_model("ssd", "SSDConfig")
        ssd_config = SSDConfig.objects.first()

        # Jaaropgave
        expected_content = '<p>This is a <strong>test</strong> text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        self.assertEqual(ssd_config.jaaropgave_display_text.html, expected_content)

        expected_content = "<p>These are PDF comments without formatting.</p>"
        self.assertEqual(ssd_config.jaaropgave_pdf_comments.html, expected_content)

        # Verify that the temporary fields were removed
        self.assertFalse(hasattr(ssd_config, "jaaropgave_display_text_tmp"))
        self.assertFalse(hasattr(ssd_config, "jaaropgave_pdf_comments_tmp"))

        # Maandspecificatie
        expected_content = '<p>This is a <strong>monthly statement</strong> text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        self.assertEqual(
            ssd_config.maandspecificatie_display_text.html, expected_content
        )
        expected_content = (
            "<p>These are monthly statement PDF comments without formatting.</p>"
        )
        self.assertEqual(
            ssd_config.maandspecificatie_pdf_comments.html, expected_content
        )

        # Verify that the temporary fields were removed
        self.assertFalse(hasattr(ssd_config, "maandspecificatie_display_text_tmp"))
        self.assertFalse(hasattr(ssd_config, "maandspecificatie_pdf_comments_tmp"))
