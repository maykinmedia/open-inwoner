import uuid

from django.db import migrations, models


def populate_uuids(apps, schema_editor):
    """
    Backfill UUIDs to every existing NotificationRecord.
    """
    NotificationRecord = apps.get_model("notifications", "NotificationRecord")
    records = NotificationRecord.objects.only("pk")
    for record in records:
        record.id_new = uuid.uuid4()
    NotificationRecord.objects.bulk_update(records, ["id_new"], batch_size=1000)


class Migration(migrations.Migration):
    """
    Switch NotificationRecord's primary key from an auto-incrementing
    BigAutoField to a UUIDField.

    No other model has a ForeignKey to NotificationRecord, so this can be
    done in-place without touching any related tables. The swap happens in
    stages because a column can't change identity (regular field -> primary
    key) in a single step:

    1. Add a new nullable `id_new` UUID column.
    2. Backfill it with a unique UUID per existing row.
    3. Make it required and unique.
    4. Drop the old `id` column (and with it, the old primary key).
    5. Promote `id_new` to primary key.
    6. Rename `id_new` back to `id`.
    """

    dependencies = [
        ("notifications", "0003_notificationprocessingconfig_notificationrecord"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationrecord",
            name="id_new",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.RunPython(populate_uuids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="notificationrecord",
            name="id_new",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.RemoveField(
            model_name="notificationrecord",
            name="id",
        ),
        migrations.AlterField(
            model_name="notificationrecord",
            name="id_new",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.RenameField(
            model_name="notificationrecord",
            old_name="id_new",
            new_name="id",
        ),
    ]
