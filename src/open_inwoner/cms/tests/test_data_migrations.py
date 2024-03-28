from open_inwoner.utils.tests.test_migrations import TestMigrations

from ..collaborate.cms_apps import CollaborateApphook
from .cms_tools import create_apphook_page


class HelpTextMigrationTest(TestMigrations):
    app = "extensions"
    migrate_from = "0006_commonextension_help_text"
    migrate_to = "0007_help_texts"

    def setUpBeforeMigration(self, apps):
        create_apphook_page(
            CollaborateApphook,
            extension_args={
                "help_text": "",
            },
        )
        self.PageModel = apps.get_model("cms", "Page")

    def test_help_text(self):
        pages = self.PageModel.objects.filter(publisher_is_draft=False)

        import pdb

        pdb.set_trace()
