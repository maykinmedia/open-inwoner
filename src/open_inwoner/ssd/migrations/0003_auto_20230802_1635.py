# Generated by Django 3.2.15 on 2023-08-02 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ssd", "0002_auto_20230728_1531"),
    ]

    operations = [
        migrations.AddField(
            model_name="ssdconfig",
            name="jaaropgave_endpoint",
            field=models.CharField(
                blank=True,
                help_text="Endpoint for the jaaropgave request",
                max_length=32,
                verbose_name="Jaaropgave endpoint",
            ),
        ),
        migrations.AddField(
            model_name="ssdconfig",
            name="maandspecificatie_endpoint",
            field=models.CharField(
                blank=True,
                help_text="Endpoint for the maandspecificatie request",
                max_length=32,
                verbose_name="Maandspecificatie endpoint",
            ),
        ),
    ]
