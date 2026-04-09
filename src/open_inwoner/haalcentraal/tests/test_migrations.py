from django.test import tag

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class TestBrpVersionMigration(TestSuccessfulMigrations):
    """
    Data migration reads BRP_VERSION from settings and writes it to the singleton.
    In the test environment BRP_VERSION is not set, so it defaults to "2.0".
    """

    app = "haalcentraal"
    migrate_from = "0001_squashed_0006_haalcentraalconfig_x_request_user"
    migrate_to = "0007_haalcentraalconfig_brp_version"

    def setUpBeforeMigration(self, apps):
        HaalCentraalConfig = apps.get_model("haalcentraal", "HaalCentraalConfig")
        HaalCentraalConfig.objects.get_or_create(pk=1)

    def test_brp_version_defaults_to_2_0_when_setting_absent(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=1)
        self.assertEqual(config.brp_version, "2.0")


@tag("migrations")
class TestHeadersReplaceMigration(TestSuccessfulMigrations):
    """
    Single migration replaces 8 individual header fields with a headers JSONField
    (list of key/value dicts) and appends x-gebruiker for BRP 2.x configs.
    """

    app = "haalcentraal"
    migrate_from = "0007_haalcentraalconfig_brp_version"
    migrate_to = "0008_replace_header_fields_with_jsonfield"

    def setUpBeforeMigration(self, apps):
        HaalCentraalConfig = apps.get_model("haalcentraal", "HaalCentraalConfig")
        config, _ = HaalCentraalConfig.objects.get_or_create(pk=1)
        config.brp_version = "2.1"
        config.api_origin_oin = "00000001234567890000"
        config.api_doelbinding = "Huisvesting"
        config.api_verwerking = "test@verwerking"
        config.api_afnemer_oin = "00000009876543210000"
        config.save()
        self.config_pk = config.pk

    def test_old_header_fields_migrated_to_list(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        self.assertIsInstance(config.headers, list)
        self.assertCountEqual(
            config.headers,
            [
                {"key": "x-origin-oin", "value": "00000001234567890000"},
                {"key": "x-doelbinding", "value": "Huisvesting"},
                {"key": "x-verwerking", "value": "test@verwerking"},
                {"key": "x-afnemer-oin", "value": "00000009876543210000"},
                {"key": "x-gebruiker", "value": "BurgerZelf"},
            ],
        )

    def test_empty_centric_fields_not_included(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        header_keys = {item["key"] for item in config.headers}
        self.assertNotIn("x-request-organization", header_keys)
        self.assertNotIn("x-request-application", header_keys)
        self.assertNotIn("x-request-afnemerscode", header_keys)
        self.assertNotIn("x-request-user", header_keys)


@tag("migrations")
class TestXGebruikerHeaderMigration(TestSuccessfulMigrations):
    """x-gebruiker: BurgerZelf is appended for BRP 2.x configs."""

    app = "haalcentraal"
    migrate_from = "0007_haalcentraalconfig_brp_version"
    migrate_to = "0008_replace_header_fields_with_jsonfield"

    def setUpBeforeMigration(self, apps):
        HaalCentraalConfig = apps.get_model("haalcentraal", "HaalCentraalConfig")
        config, _ = HaalCentraalConfig.objects.get_or_create(pk=1)
        config.brp_version = "2.1"
        config.save()
        self.config_pk = config.pk

    def test_x_gebruiker_appended_for_2x(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        self.assertIn({"key": "x-gebruiker", "value": "BurgerZelf"}, config.headers)

    def test_x_gebruiker_not_duplicated_if_already_present(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        x_gebruiker_entries = [
            item for item in config.headers if item.get("key") == "x-gebruiker"
        ]
        self.assertEqual(len(x_gebruiker_entries), 1)


@tag("migrations")
class TestXGebruikerHeaderMigrationSkipped13(TestSuccessfulMigrations):
    """x-gebruiker must NOT be added for BRP 1.3 configs."""

    app = "haalcentraal"
    migrate_from = "0007_haalcentraalconfig_brp_version"
    migrate_to = "0008_replace_header_fields_with_jsonfield"

    def setUpBeforeMigration(self, apps):
        HaalCentraalConfig = apps.get_model("haalcentraal", "HaalCentraalConfig")
        config, _ = HaalCentraalConfig.objects.get_or_create(pk=1)
        config.brp_version = "1.3"
        config.save()
        self.config_pk = config.pk

    def test_x_gebruiker_not_added_for_1_3(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        self.assertNotIn({"key": "x-gebruiker", "value": "BurgerZelf"}, config.headers)
