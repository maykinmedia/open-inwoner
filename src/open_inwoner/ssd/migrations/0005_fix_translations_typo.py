# Generated by Django 3.2.20 on 2023-09-04 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ssd", "0004_auto_20230808_1043"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ssdconfig",
            name="mijn_uitkeringen_text",
            field=models.TextField(
                blank=True,
                help_text="The text displayed as overview of the 'Mijn Uitkeringen' section.",
                verbose_name="Overview text",
            ),
        ),
    ]
