# Generated by Django 4.2.16 on 2024-12-11 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "openzaak",
            "0058_remove_zaaktypeconfig_unique_identificatie_in_catalogus_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="openzaakconfig",
            name="show_cases_without_status",
            field=models.BooleanField(
                default=False,
                verbose_name="By default cases are only shown if they have a status set.",
            ),
        ),
    ]
