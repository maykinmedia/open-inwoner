# Generated by Django 3.2.15 on 2023-02-06 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("haalcentraal", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="haalcentraalconfig",
            name="api_doelbinding",
            field=models.CharField(
                blank=True,
                help_text="Value of the 'x-doelbinding' header for Haalcentraal BRP API requests.",
                max_length=64,
                verbose_name="API 'doelbinding' header",
            ),
        ),
        migrations.AddField(
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
