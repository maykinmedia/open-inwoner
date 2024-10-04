import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def migrate_from_notifications_api_common(apps, schema_editor):
    """
    Migrate data for integration of Notificaties API from library to OIP
    """
    try:
        LegacyNotificationsConfig = apps.get_model(
            "notifications_api_common", "NotificationsConfig"
        )
        LegacySubscription = apps.get_model("notifications_api_common", "Subscription")
    except LookupError as exc:
        exc.add_note(
            "notifications_api_common must be in INSTALLED_APPS in order to run the migrations"
        )
        raise

    NotificationsAPIConfig = apps.get_model("notifications", "NotificationsAPIConfig")
    Subscription = apps.get_model("notifications", "Subscription")

    # migrate notifications config
    try:
        legacy_config = LegacyNotificationsConfig.objects.get()
    except LegacyNotificationsConfig.DoesNotExist:
        return

    if not legacy_config.notifications_api_service:
        return

    config = NotificationsAPIConfig.objects.create(
        notifications_api_service=getattr(
            legacy_config, "notifications_api_service", None
        ),
        notification_delivery_max_retries=legacy_config.notification_delivery_max_retries,
        notification_delivery_retry_backoff=legacy_config.notification_delivery_retry_backoff,
        notification_delivery_retry_backoff_max=legacy_config.notification_delivery_retry_backoff_max,
    )

    # migrate subscriptions
    legacy_subs = LegacySubscription.objects.all()
    for legacy_sub in legacy_subs:
        Subscription.objects.create(
            notifications_api_config=config,
            callback_url=legacy_sub.callback_url,
            client_id=legacy_sub.client_id,
            secret=legacy_sub.secret,
            channels=legacy_sub.channels,
            _subscription=legacy_sub._subscription,
        )


def reverse_migrate_from_notifications_api_common(apps, schema_editor):
    """
    Reverse-migrate data for integration of Notificaties API to library
    """
    try:
        LegacyNotificationsConfig = apps.get_model(
            "notifications_api_common", "NotificationsConfig"
        )
        LegacySubscription = apps.get_model("notifications_api_common", "Subscription")
    except LookupError as exc:
        exc.add_note(
            "notifications_api_common must be in INSTALLED_APPS in order to run the migrations"
        )
        raise

    NotificationsAPIConfig = apps.get_model("notifications", "NotificationsAPIConfig")
    Subscription = apps.get_model("notifications", "Subscription")

    # reverse-migrate config(s)
    configs = NotificationsAPIConfig.objects.all()

    if configs.count() == 0:
        logger.info(
            "No configuration models for Notifications API found; "
            "skipping data migration for notifications_api_common"
        )
        return
    elif configs.count() > 1:
        raise ValueError(
            "Multiple configuration models for Notifications API found; "
            "reversing the migration for notifications_api_common requires that "
            "there be only one configuration model"
        )
    else:
        config = configs.get()
        LegacyNotificationsConfig.objects.create(
            notifications_api_service=getattr(
                config, "notifications_api_service", None
            ),
            notification_delivery_max_retries=config.notification_delivery_max_retries,
            notification_delivery_retry_backoff=config.notification_delivery_retry_backoff,
            notification_delivery_retry_backoff_max=config.notification_delivery_retry_backoff_max,
        )

    # reverse-migrate subscriptions
    subs = Subscription.objects.all()
    for sub in subs:
        LegacySubscription.objects.create(
            callback_url=sub.callback_url,
            client_id=sub.client_id,
            secret=sub.secret,
            channels=sub.channels,
            _subscription=sub._subscription,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0001_initial"),
        (
            "notifications_api_common",
            "0008_merge_0006_auto_20221213_0214_0007_auto_20221206_0414",
        ),
    ]
    operations = [
        migrations.RunPython(
            code=migrate_from_notifications_api_common,
            reverse_code=reverse_migrate_from_notifications_api_common,
        )
    ]
