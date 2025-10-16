from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class MenuIconsSuccessfulMigrations(TestSuccessfulMigrations):
    migrate_from = "0007_alter_commonextension_requires_auth_bsn_or_kvk"
    migrate_to = "0008_menu_icons"
    app = "extensions"

    def setUpBeforeMigration(self, apps):
        Site = apps.get_model("sites", "Site")
        CommonExtension = apps.get_model("extensions", "CommonExtension")
        Page = apps.get_model("cms", "Page")
        TreeNode = apps.get_model("cms", "TreeNode")

        site = Site.objects.create(domain="foo", name="foo")
        node = TreeNode.objects.create(site=site, path="0001", depth=1, numchild=0)
        page = Page.objects.create(node=node)

        self.ce_euro_outline = CommonExtension.objects.create(
            extended_object=page, menu_icon="euro_outline"
        )

    def test_menu_icons_upgrade_0007_to_0008(self):
        CommonExtension = self.apps.get_model("extensions", "CommonExtension")

        ce = CommonExtension.objects.get(pk=self.ce_euro_outline.pk)
        self.assertEqual(ce.menu_icon, "euro")
