from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class FlatPageContentMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0002_migrate_flatpages_content_to_cms"
    migrate_to = "0005_cmsflatpagemodel_content_schema_2"
    app = "footer"

    def setUpBeforeMigration(self, apps):
        CMSFlatPageModel = apps.get_model("footer", "CMSFlatPageModel")
        Placeholder = apps.get_model("cms", "Placeholder")

        placeholder = Placeholder.objects.create(slot="test")

        CMSFlatPageModel.objects.create(
            language="nl",
            plugin_type="CMSFlatPagePlugin",
            placeholder=placeholder,
            position=1,
            path="0001",
            depth=1,
            numchild=0,
            title="Test Flatpage",
            content="<p><strong>Bold text</strong> and <em>italic text</em></p>",
        )

        CMSFlatPageModel.objects.create(
            language="nl",
            plugin_type="CMSFlatPagePlugin",
            placeholder=placeholder,
            position=2,
            path="0002",
            depth=1,
            numchild=0,
            title="Plain Text Flatpage",
            content="This is plain text content",
        )

        CMSFlatPageModel.objects.create(
            language="nl",
            plugin_type="CMSFlatPagePlugin",
            placeholder=placeholder,
            position=3,
            path="0003",
            depth=1,
            numchild=0,
            title="Empty Flatpage",
            content="",
        )

    def test_html_content_migration(self):
        CMSFlatPageModel = self.apps.get_model("footer", "CMSFlatPageModel")

        flatpage = CMSFlatPageModel.objects.filter(title="Test Flatpage").first()

        expected_html = "<p><strong>Bold text</strong> and <em>italic text</em></p>"
        self.assertEqual(flatpage.content.html, expected_html)

        self.assertFalse(hasattr(flatpage, "content_tmp"))

    def test_plain_text_content_migration(self):
        CMSFlatPageModel = self.apps.get_model("footer", "CMSFlatPageModel")

        flatpage = CMSFlatPageModel.objects.filter(title="Plain Text Flatpage").first()

        expected_html = "<p>This is plain text content</p>"
        self.assertEqual(flatpage.content.html, expected_html)

        self.assertFalse(hasattr(flatpage, "content_tmp"))

    def test_empty_content_migration(self):
        CMSFlatPageModel = self.apps.get_model("footer", "CMSFlatPageModel")

        flatpage = CMSFlatPageModel.objects.filter(title="Empty Flatpage").first()

        self.assertTrue(flatpage.content is None or flatpage.content.html == "")

        self.assertFalse(hasattr(flatpage, "content_tmp"))
