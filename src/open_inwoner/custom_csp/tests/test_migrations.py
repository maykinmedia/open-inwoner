from django.test import tag

from maykin_common.csp.models import CSPSetting as MaykinCommonCSPSetting

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations

PDOK_ACHTERGRONDKAART = (
    "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/"
)


@tag("migrations")
class MigrateToMaykinCommonCSPMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0001_initial"
    migrate_to = "0002_migrate_to_maykin_common_csp"
    app = "custom_csp"

    def setUpBeforeMigration(self, apps):
        OldCSPSetting = apps.get_model("custom_csp", "CSPSetting")

        OldCSPSetting.objects.create(
            directive="script-src", value="https://www.googletagmanager.com"
        )
        OldCSPSetting.objects.create(
            directive="connect-src", value="https://www.google-analytics.com"
        )

    def test_settings_are_migrated_to_maykin_common_csp(self):
        CSPSetting = self.apps.get_model("maykin_common_csp", "CSPSetting")

        self.assertEqual(
            list(
                CSPSetting.objects.order_by("directive", "value").values_list(
                    "directive", "value", "identifier"
                )
            ),
            [
                (
                    "connect-src",
                    "https://www.google-analytics.com",
                    "migrated-from-custom-csp",
                ),
                ("img-src", PDOK_ACHTERGRONDKAART, "migrated-from-settings"),
                (
                    "script-src",
                    "https://www.googletagmanager.com",
                    "migrated-from-custom-csp",
                ),
            ],
        )


@tag("migrations")
class RevertMigrateToMaykinCommonCSPMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0002_migrate_to_maykin_common_csp"
    migrate_to = "0001_initial"
    app = "custom_csp"

    def setUpBeforeMigration(self, apps):
        CSPSetting = apps.get_model("maykin_common_csp", "CSPSetting")

        # drop the settings added when the test database was migrated
        CSPSetting.objects.all().delete()
        CSPSetting.objects.create(
            directive="img-src",
            value=PDOK_ACHTERGRONDKAART,
            identifier="migrated-from-settings",
        )
        CSPSetting.objects.create(
            directive="script-src",
            value="https://www.googletagmanager.com",
            identifier="migrated-from-custom-csp",
        )
        CSPSetting.objects.create(
            directive="connect-src", value="https://www.google-analytics.com"
        )

    def test_settings_are_migrated_back_to_custom_csp(self):
        OldCSPSetting = self.apps.get_model("custom_csp", "CSPSetting")

        self.assertEqual(
            list(
                OldCSPSetting.objects.order_by("directive", "value").values_list(
                    "directive", "value"
                )
            ),
            [
                ("connect-src", "https://www.google-analytics.com"),
                ("script-src", "https://www.googletagmanager.com"),
            ],
        )
        # only the settings added in the admin since are kept, everything else is
        # provided by the settings or custom_csp again
        self.assertEqual(
            list(
                MaykinCommonCSPSetting.objects.order_by(
                    "directive", "value"
                ).values_list("directive", "value", "identifier")
            ),
            [("connect-src", "https://www.google-analytics.com", "")],
        )
