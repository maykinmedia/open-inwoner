# Generated by Django 4.2.16 on 2024-10-15 08:42

from django.db import migrations, models

import open_inwoner.haalcentraal.validators


class Migration(migrations.Migration):

    dependencies = [
        ("haalcentraal", "0002_auto_20230206_1511"),
    ]

    operations = [
        migrations.AddField(
            model_name="haalcentraalconfig",
            name="api_verwerking",
            field=models.CharField(
                blank=True,
                help_text="Value of the 'x-verwerking' header for Haalcentraal BRP API requests",
                max_length=242,
                validators=[
                    open_inwoner.haalcentraal.validators.validate_verwerking_header
                ],
                verbose_name="API 'verwerking' header",
            ),
        ),
        migrations.AlterField(
            model_name="haalcentraalconfig",
            name="api_doelbinding",
            field=models.CharField(
                blank=True,
                help_text="Value of the 'x-doelbinding' header for Haalcentraal BRP API requests.",
                max_length=64,
                verbose_name="API 'doelbinding' header",
            ),
        ),
        migrations.AlterField(
            model_name="haalcentraalconfig",
            name="api_origin_oin",
            field=models.CharField(
                blank=True,
                help_text="Value of the 'x-origin-oin' header for Haalcentraal BRP API requests.",
                max_length=64,
                verbose_name="API 'OIN' header",
            ),
        ),
    ]
