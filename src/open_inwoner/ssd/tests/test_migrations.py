from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


class _SsdFieldWithContentMixin:
    """Mixin: creates a singleton SSDConfig with markdown content before migration."""

    field_name: str
    content: str

    def setUpBeforeMigration(self, apps):
        SSDConfig = apps.get_model("ssd", "SSDConfig")
        SSDConfig.objects.create(**{f"{self.field_name}_tmp": self.content})

    def test_content_is_converted_to_prosemirror(self):
        SSDConfig = self.apps.get_model("ssd", "SSDConfig")
        config = SSDConfig.objects.first()
        pm_value = getattr(config, self.field_name).raw_data
        self.assertIsNotNone(pm_value)
        self.assertEqual(pm_value["type"], "doc")


class _SsdFieldEmptyContentMixin:
    """Mixin: creates a singleton SSDConfig with empty content before migration."""

    field_name: str

    def setUpBeforeMigration(self, apps):
        SSDConfig = apps.get_model("ssd", "SSDConfig")
        SSDConfig.objects.create(**{f"{self.field_name}_tmp": ""})

    def test_empty_content_is_skipped(self):
        SSDConfig = self.apps.get_model("ssd", "SSDConfig")
        config = SSDConfig.objects.first()
        self.assertIsNone(getattr(config, self.field_name).raw_data)


@tag("migrations")
class JaaropgaveDisplayTextWithContentTest(
    _SsdFieldWithContentMixin, TestSuccessfulMigrations
):
    """Migration 0008: jaaropgave_display_text_tmp (markdown) → PM field."""

    app = "ssd"
    migrate_from = "0007_ssdconfig_jaaropgave_display_text_schema_1"
    migrate_to = "0008_ssdconfig_jaaropgave_display_text_data"
    field_name = "jaaropgave_display_text"
    content = "**Bold** display text"


@tag("migrations")
class JaaropgaveDisplayTextEmptyContentTest(
    _SsdFieldEmptyContentMixin, TestSuccessfulMigrations
):
    app = "ssd"
    migrate_from = "0007_ssdconfig_jaaropgave_display_text_schema_1"
    migrate_to = "0008_ssdconfig_jaaropgave_display_text_data"
    field_name = "jaaropgave_display_text"


@tag("migrations")
class JaaropgavePdfCommentsWithContentTest(
    _SsdFieldWithContentMixin, TestSuccessfulMigrations
):
    """Migration 0011: jaaropgave_pdf_comments_tmp (plain text) → PM field."""

    app = "ssd"
    migrate_from = "0010_ssdconfig_jaaropgave_pdf_comments_schema_1"
    migrate_to = "0011_ssdconfig_jaaropgave_pdf_comments_data"
    field_name = "jaaropgave_pdf_comments"
    content = "PDF comment text"


@tag("migrations")
class JaaropgavePdfCommentsEmptyContentTest(
    _SsdFieldEmptyContentMixin, TestSuccessfulMigrations
):
    app = "ssd"
    migrate_from = "0010_ssdconfig_jaaropgave_pdf_comments_schema_1"
    migrate_to = "0011_ssdconfig_jaaropgave_pdf_comments_data"
    field_name = "jaaropgave_pdf_comments"


@tag("migrations")
class MaandspecificatieDisplayTextWithContentTest(
    _SsdFieldWithContentMixin, TestSuccessfulMigrations
):
    """Migration 0014: maandspecificatie_display_text_tmp (markdown) → PM field."""

    app = "ssd"
    migrate_from = "0013_ssdconfig_maandspecificatie_display_text_schema_1"
    migrate_to = "0014_ssdconfig_maandspecificatie_display_text_data"
    field_name = "maandspecificatie_display_text"
    content = "**Bold** display text"


@tag("migrations")
class MaandspecificatieDisplayTextEmptyContentTest(
    _SsdFieldEmptyContentMixin, TestSuccessfulMigrations
):
    app = "ssd"
    migrate_from = "0013_ssdconfig_maandspecificatie_display_text_schema_1"
    migrate_to = "0014_ssdconfig_maandspecificatie_display_text_data"
    field_name = "maandspecificatie_display_text"


@tag("migrations")
class MaandspecificatiePdfCommentsWithContentTest(
    _SsdFieldWithContentMixin, TestSuccessfulMigrations
):
    """Migration 0017: maandspecificatie_pdf_comments_tmp (plain text) → PM field."""

    app = "ssd"
    migrate_from = "0016_ssdconfig_maandspecificatie_pdf_comments_schema_1"
    migrate_to = "0017_ssdconfig_maandspecificatie_pdf_comments_data"
    field_name = "maandspecificatie_pdf_comments"
    content = "PDF comment text"


@tag("migrations")
class MaandspecificatiePdfCommentsEmptyContentTest(
    _SsdFieldEmptyContentMixin, TestSuccessfulMigrations
):
    app = "ssd"
    migrate_from = "0016_ssdconfig_maandspecificatie_pdf_comments_schema_1"
    migrate_to = "0017_ssdconfig_maandspecificatie_pdf_comments_data"
    field_name = "maandspecificatie_pdf_comments"


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
    Test migration 0020: strip unsafe hrefs from stored prosemirror link marks
    on SSDConfig.jaaropgave_display_text/maandspecificatie_display_text.

    jaaropgave_pdf_comments/maandspecificatie_pdf_comments are excluded:
    their schema forbids the LINK mark entirely (allowed_mark_types=[]).
    """

    app = "ssd"
    migrate_from = "0019_alter_ssdconfig_jaaropgave_display_text_and_more"
    migrate_to = "0020_sanitize_prosemirror_link_hrefs"

    def setUpBeforeMigration(self, apps):
        SSDConfig = apps.get_model("ssd", "SSDConfig")
        self.config = SSDConfig.objects.create()
        SSDConfig.objects.filter(pk=self.config.pk).update(
            jaaropgave_display_text=_text_with_link("click", "javascript:alert(1)"),
            maandspecificatie_display_text=_text_with_link(
                "click", "https://example.com"
            ),
        )

    def _get(self):
        SSDConfig = self.apps.get_model("ssd", "SSDConfig")
        return SSDConfig.objects.get(pk=self.config.pk)

    def test_unsafe_href_stripped_from_jaaropgave_display_text(self):
        config = self._get()
        text_node = config.jaaropgave_display_text.raw_data["content"][0]["content"][0]
        self.assertEqual(text_node["marks"], [])

    def test_safe_href_preserved_on_maandspecificatie_display_text(self):
        config = self._get()
        text_node = config.maandspecificatie_display_text.raw_data["content"][0][
            "content"
        ][0]
        self.assertEqual(text_node["marks"][0]["attrs"]["href"], "https://example.com")
