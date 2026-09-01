import uuid

from django.test import tag

from zgw_consumers.constants import APITypes

from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


@tag("migrations")
class NotificationRecordUUIDPrimaryKeyMigrationTest(TestSuccessfulMigrations):
    """
    Test the data migration that swaps NotificationRecord's primary key from
    an auto-incrementing integer to a UUID.
    """

    migrate_from = "0003_notificationprocessingconfig_notificationrecord"
    migrate_to = "0004_notificationrecord_uuid_pk"
    app = "notifications"

    def setUpBeforeMigration(self, apps):
        Service = apps.get_model("zgw_consumers", "Service")
        NotificationsAPIConfig = apps.get_model(
            "notifications", "NotificationsAPIConfig"
        )
        Subscription = apps.get_model("notifications", "Subscription")
        NotificationRecord = apps.get_model("notifications", "NotificationRecord")

        service = Service.objects.create(
            api_root="http://some-api-root/api/v1/",
            api_type=APITypes.nrc,
            slug="service",
        )
        config = NotificationsAPIConfig.objects.create(
            notifications_api_service=service
        )
        self.subscription_id = Subscription.objects.create(
            notifications_api_config=config,
            callback_url="https://example.com/callback",
            client_id="test_client",
            secret="test_secret",
            channels=["zaken"],
        ).pk

        self.kanalen = [f"kanaal-{i}" for i in range(5)]
        self.old_ids = [
            NotificationRecord.objects.create(
                subscription_id=self.subscription_id,
                payload={"kanaal": kanaal},
                kanaal=kanaal,
            ).pk
            for kanaal in self.kanalen
        ]

    def test_records_are_preserved_with_new_uuid_pks(self):
        NotificationRecord = self.apps.get_model("notifications", "NotificationRecord")

        records = list(NotificationRecord.objects.order_by("kanaal"))
        self.assertEqual([r.kanaal for r in records], sorted(self.kanalen))
        self.assertEqual(
            [r.payload for r in records],
            [{"kanaal": r.kanaal} for r in records],
        )
        self.assertTrue(all(r.subscription_id == self.subscription_id for r in records))

    def test_new_pks_are_unique_uuids(self):
        NotificationRecord = self.apps.get_model("notifications", "NotificationRecord")

        new_ids = list(NotificationRecord.objects.values_list("id", flat=True))
        self.assertEqual(len(new_ids), len(self.old_ids))
        self.assertEqual(len(new_ids), len(set(new_ids)))
        for new_id in new_ids:
            self.assertIsInstance(new_id, uuid.UUID)
