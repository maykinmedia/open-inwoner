from django.db import migrations, models


def multiply_by_24(apps, schema_editor):
    NotificationProcessingConfig = apps.get_model(
        "notifications", "NotificationProcessingConfig"
    )
    for config in NotificationProcessingConfig.objects.all():
        updates = {}
        if config.retention_hours is not None:
            updates["retention_hours"] = config.retention_hours * 24
        if config.stuck_processing_retention_hours is not None:
            updates["stuck_processing_retention_hours"] = (
                config.stuck_processing_retention_hours * 24
            )
        if updates:
            NotificationProcessingConfig.objects.filter(pk=config.pk).update(**updates)


def divide_by_24(apps, schema_editor):
    NotificationProcessingConfig = apps.get_model(
        "notifications", "NotificationProcessingConfig"
    )
    for config in NotificationProcessingConfig.objects.all():
        updates = {}
        if config.retention_hours is not None:
            updates["retention_hours"] = config.retention_hours // 24
        if config.stuck_processing_retention_hours is not None:
            updates["stuck_processing_retention_hours"] = (
                config.stuck_processing_retention_hours // 24
            )
        if updates:
            NotificationProcessingConfig.objects.filter(pk=config.pk).update(**updates)


class Migration(migrations.Migration):
    """
    Rename NotificationProcessingConfig's day-based retention fields to
    hour-based ones, now that the prune task runs hourly instead of daily.

    RenameField preserves the existing column/values, so the RunPython step
    only needs to rescale those values (*24 forward, //24 in reverse) to keep
    the same effective retention window under the new unit.
    """

    dependencies = [
        ("notifications", "0004_notificationrecord_uuid_pk"),
    ]

    operations = [
        migrations.RenameField(
            model_name="notificationprocessingconfig",
            old_name="retention_days",
            new_name="retention_hours",
        ),
        migrations.RenameField(
            model_name="notificationprocessingconfig",
            old_name="stuck_processing_retention_days",
            new_name="stuck_processing_retention_hours",
        ),
        migrations.AlterField(
            model_name="notificationprocessingconfig",
            name="retention_hours",
            field=models.PositiveIntegerField(
                blank=True,
                help_text=(
                    "Number of hours to retain notification records in terminal "
                    "states (SUCCESS, FAILED, SKIPPED). Records older than this "
                    "will be pruned. Leave empty to keep records indefinitely."
                ),
                null=True,
                verbose_name="retention hours",
            ),
        ),
        migrations.AlterField(
            model_name="notificationprocessingconfig",
            name="stuck_processing_retention_hours",
            field=models.PositiveIntegerField(
                blank=True,
                help_text=(
                    "Number of hours after which PROCESSING records are "
                    "considered stuck (worker killed before completion) and "
                    "will be pruned. Leave empty to never prune stuck records."
                ),
                null=True,
                verbose_name="stuck processing retention hours",
            ),
        ),
        migrations.RunPython(
            code=multiply_by_24,
            reverse_code=divide_by_24,
        ),
    ]
