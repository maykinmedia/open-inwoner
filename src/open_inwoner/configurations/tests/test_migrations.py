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


class WarningBannerTextMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0085_create_partial_admin_edit_permissions"
    migrate_to = "0088_siteconfiguration_warning_banner_text_schema_2"
    app = "configurations"

    def setUpBeforeMigration(self, apps):
        SiteConfiguration = apps.get_model("configurations", "SiteConfiguration")

        config = SiteConfiguration.objects.create()

        test_html = '<p>This is a <strong>test</strong> warning with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        config.warning_banner_text = test_html
        config.save()

    def test_warning_banner_text(self):
        SiteConfiguration = self.apps.get_model("configurations", "SiteConfiguration")
        config = SiteConfiguration.objects.first()

        expected_content = '<p>This is a <strong>test</strong> warning with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        self.assertEqual(config.warning_banner_text.html, expected_content)

        # Verify that the temporary field was removed
        self.assertFalse(hasattr(config, "warning_banner_text_tmp"))


class LoginTextMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0088_siteconfiguration_warning_banner_text_schema_2"
    migrate_to = "0091_siteconfiguration_login_text_schema_2"
    app = "configurations"

    def setUpBeforeMigration(self, apps):
        SiteConfiguration = apps.get_model("configurations", "SiteConfiguration")

        config = SiteConfiguration.objects.create()

        test_html = '<p>This is a <strong>test</strong> login text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        config.login_text = test_html
        config.save()

    def test_login_text(self):
        SiteConfiguration = self.apps.get_model("configurations", "SiteConfiguration")
        config = SiteConfiguration.objects.first()

        expected_content = '<p>This is a <strong>test</strong> login text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        self.assertEqual(config.login_text.html, expected_content)

        # Verify that the temporary field was removed
        self.assertFalse(hasattr(config, "login_text_tmp"))


class SearchZeroResultsTextMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0091_siteconfiguration_login_text_schema_2"
    migrate_to = "0094_siteconfiguration_search_zero_results_text_schema_2"
    app = "configurations"

    def setUpBeforeMigration(self, apps):
        SiteConfiguration = apps.get_model("configurations", "SiteConfiguration")

        config = SiteConfiguration.objects.create()

        test_html = '<p>This is a <strong>test</strong> login text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        config.search_zero_results_text = test_html
        config.save()

    def test_login_text(self):
        SiteConfiguration = self.apps.get_model("configurations", "SiteConfiguration")
        config = SiteConfiguration.objects.first()

        expected_content = '<p>This is a <strong>test</strong> login text with <em>formatting</em> and a <a href="https://example.com">link</a>.</p>'
        self.assertEqual(config.search_zero_results_text.html, expected_content)

        # Verify that the temporary field was removed
        self.assertFalse(hasattr(config, "search_zero_results_text_tmp"))
