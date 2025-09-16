from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


class PartialEditPermissionsMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0082_alter_siteconfigurationpage_cms_page"
    migrate_to = "0085_create_partial_admin_edit_permissions"
    app = "configurations"

    def setUpBeforeMigration(self, apps):
        Permission = apps.get_model("auth", "Permission")

        for codename in (
            "siteconfig_fieldset_color",
            "siteconfig_fieldset_images",
            "siteconfig_fieldset_warning_banner",
            "siteconfig_fieldset_page_texts",
            "siteconfig_fieldset_help_texts",
        ):
            qs = Permission.objects.filter(codename=codename)

            self.assertFalse(qs.exists())

    def test_edit_permission_create(self):
        Permission = self.apps.get_model("auth", "Permission")

        for codename in (
            "siteconfig_fieldset_color",
            "siteconfig_fieldset_images",
            "siteconfig_fieldset_warning_banner",
            "siteconfig_fieldset_page_texts",
            "siteconfig_fieldset_help_texts",
        ):
            qs = Permission.objects.filter(codename=codename)

            self.assertTrue(qs.exists())
