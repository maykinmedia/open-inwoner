# Generated by Django 4.2.11 on 2024-04-12 07:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0048_alter_zaaktyperesultaattypeconfig_omschrijving"),
    ]

    operations = [
        migrations.DeleteModel(
            name="StatusTranslation",
        ),
    ]
