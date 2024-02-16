from open_inwoner.utils.tests.test_migrations import TestMigrations


class APIRootMigrationTest(TestMigrations):
    migrate_from = "0003_auto_20240209_1259"
    migrate_to = "0004_api_root"
    app = "kvk"

    def setUpBeforeMigration(self, apps):
        KvKConfig = apps.get_model("kvk", "KvKConfig")

        KvKConfig.objects.create(
            api_root="https://kvk.example.nl/api/v1/", api_key="dummy"
        )

    def test_migrate_api_root(self):
        KvKConfig = self.apps.get_model("kvk", "KvKConfig")

        config = KvKConfig.objects.first()

        self.assertEqual(config.api_root, "https://kvk.example.nl/api")
