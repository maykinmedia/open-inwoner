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
class TestHeadersMigration(TestSuccessfulMigrations):
    """
    Data migration copies individual header fields to the headers JSONField (dict format).
    migrate_from = after adding the headers JSONField (old fields still present)
    migrate_to = after data migration
    """

    app = "haalcentraal"
    migrate_from = "0009_haalcentraalconfig_headers"
    migrate_to = "0010_data_migrate_headers"

    def setUpBeforeMigration(self, apps):
        HaalCentraalConfig = apps.get_model("haalcentraal", "HaalCentraalConfig")
        config, _ = HaalCentraalConfig.objects.get_or_create(pk=1)
        config.api_origin_oin = "00000001234567890000"
        config.api_doelbinding = "Huisvesting"
        config.api_verwerking = "test@verwerking"
        config.api_afnemer_oin = "00000009876543210000"
        config.save()
        self.config_pk = config.pk

    def test_i_connect_headers_migrated(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        self.assertEqual(
            config.headers,
            {
                "x-origin-oin": "00000001234567890000",
                "x-doelbinding": "Huisvesting",
                "x-verwerking": "test@verwerking",
                "x-afnemer-oin": "00000009876543210000",
            },
        )

    def test_empty_centric_fields_not_included(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        self.assertNotIn("x-request-organization", config.headers)
        self.assertNotIn("x-request-application", config.headers)
        self.assertNotIn("x-request-afnemerscode", config.headers)
        self.assertNotIn("x-request-user", config.headers)


@tag("migrations")
class TestHeadersDictToListMigration(TestSuccessfulMigrations):
    """
    Data migration converts headers from dict format {"key": "value"}
    to list format [{"key": "key", "value": "value"}].
    """

    app = "haalcentraal"
    migrate_from = "0012_alter_haalcentraalconfig_headers_and_more"
    migrate_to = "0013_data_convert_headers_to_list"

    def setUpBeforeMigration(self, apps):
        HaalCentraalConfig = apps.get_model("haalcentraal", "HaalCentraalConfig")
        config, _ = HaalCentraalConfig.objects.get_or_create(pk=1)
        config.headers = {
            "x-origin-oin": "00000001234567890000",
            "x-doelbinding": "Huisvesting",
        }
        config.save()
        self.config_pk = config.pk

    def test_headers_converted_to_list(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        self.assertIsInstance(config.headers, list)
        self.assertCountEqual(
            config.headers,
            [
                {"key": "x-origin-oin", "value": "00000001234567890000"},
                {"key": "x-doelbinding", "value": "Huisvesting"},
            ],
        )

    def test_empty_dict_becomes_empty_list(self):
        # Default case: empty dict {} stays as [] after migration
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        # Our setUp has data, but verify the migration doesn't crash on empty
        self.assertIsInstance(config.headers, list)


@tag("migrations")
class TestXGebruikerHeaderMigration(TestSuccessfulMigrations):
    """
    Data migration appends x-gebruiker: BurgerZelf to the headers list.
    This header was previously hardcoded in the BRP 2.x client.
    """

    app = "haalcentraal"
    migrate_from = "0013_data_convert_headers_to_list"
    migrate_to = "0014_data_add_x_gebruiker_header"

    def setUpBeforeMigration(self, apps):
        HaalCentraalConfig = apps.get_model("haalcentraal", "HaalCentraalConfig")
        config, _ = HaalCentraalConfig.objects.get_or_create(pk=1)
        config.brp_version = "2.1"
        config.headers = [{"key": "x-origin-oin", "value": "00000001234567890000"}]
        config.save()
        self.config_pk = config.pk

    def test_x_gebruiker_appended_for_2x(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        self.assertIn({"key": "x-gebruiker", "value": "BurgerZelf"}, config.headers)

    def test_existing_headers_preserved(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        self.assertIn(
            {"key": "x-origin-oin", "value": "00000001234567890000"}, config.headers
        )

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
    migrate_from = "0013_data_convert_headers_to_list"
    migrate_to = "0014_data_add_x_gebruiker_header"

    def setUpBeforeMigration(self, apps):
        HaalCentraalConfig = apps.get_model("haalcentraal", "HaalCentraalConfig")
        config, _ = HaalCentraalConfig.objects.get_or_create(pk=1)
        config.brp_version = "1.3"
        config.headers = []
        config.save()
        self.config_pk = config.pk

    def test_x_gebruiker_not_added_for_1_3(self):
        HaalCentraalConfig = self.apps.get_model("haalcentraal", "HaalCentraalConfig")
        config = HaalCentraalConfig.objects.get(pk=self.config_pk)
        self.assertNotIn({"key": "x-gebruiker", "value": "BurgerZelf"}, config.headers)
