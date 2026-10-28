from django.test import tag

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
                ("script-src", PDOK_ACHTERGRONDKAART, "migrated-from-settings"),
                (
                    "script-src",
                    "https://www.googletagmanager.com",
                    "migrated-from-custom-csp",
                ),
            ],
        )
