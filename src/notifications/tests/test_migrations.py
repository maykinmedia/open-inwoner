from zgw_consumers.constants import APITypes

from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations


class NotificationsAPILibraryMigrationTest(TestSuccessfulMigrations):
    migrate_from = "0001_initial"
    migrate_to = "0002_migrate_data_from_notifications_api_common"
    app = "notifications"

    def setUpBeforeMigration(self, apps):
        from notifications_api_common.models import (
            NotificationsConfig as LegacyNotificationsConfig,
            Subscription as LegacySubscription,
        )

        self.notification_service = ServiceFactory(api_type=APITypes.nrc)

        legacy_notifications_config = LegacyNotificationsConfig.objects.get()
        legacy_notifications_config.notifications_api_service = (
            self.notification_service
        )
        legacy_notifications_config.save()

        LegacySubscription.objects.create(
            callback_url="http://www.callback1.nl",
            client_id="client_id_1",
            secret="secret",
            channels=["zaken"],
            _subscription="http://subscription.nl",
        )
        LegacySubscription.objects.create(
            callback_url="http://www.callback2.nl",
            client_id="client_id_2",
            secret="secret_2",
            channels=["zaken", "other"],
            _subscription="http://subscription.nl",
        )

    def test_notifications_migration_0001_to_0002(self):
        NotificationsAPIConfig = self.apps.get_model(
            "notifications", "NotificationsAPIConfig"
        )
        Subscription = self.apps.get_model("notifications", "Subscription")

        self.assertEqual(Subscription.objects.count(), 2)
        self.assertEqual(
            NotificationsAPIConfig.objects.get().notifications_api_service.uuid,
            self.notification_service.uuid,
        )
