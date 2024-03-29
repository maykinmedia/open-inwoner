# Generated by Django 3.2.20 on 2023-11-13 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0028_merge_20231101_1705"),
    ]

    operations = [
        migrations.AddField(
            model_name="zaaktypestatustypeconfig",
            name="notify_status_change",
            field=models.BooleanField(
                verbose_name="Notify of status change",
                default=True,
                help_text="Whether the user should be notfied if a case is set to this type of status",
            ),
        ),
        migrations.AlterField(
            model_name="zaaktypeconfig",
            name="notify_status_changes",
            field=models.BooleanField(
                default=False,
                help_text="Whether the user should be notified of status changes for cases with this zaak type",
                verbose_name="Notify of status changes",
            ),
        ),
    ]
