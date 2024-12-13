# Generated by Django 4.2.16 on 2024-12-04 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("haalcentraal", "0003_haalcentraalconfig_api_verwerking_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="haalcentraalconfig",
            name="api_afnemer_oin",
            field=models.CharField(
                blank=True,
                help_text="Value of the 'x-afnemer-oin' header for Haalcentraal BRP API requests.",
                max_length=64,
                verbose_name="API 'OIN' afnemer header",
            ),
        ),
    ]
