# Generated by Django 3.2.20 on 2023-11-23 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0036_zaaktypeconfig_relevante_zaakperiode"),
    ]

    operations = [
        migrations.AlterField(
            model_name="zaaktyperesultaattypeconfig",
            name="description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Determines the text that will be shown to the user if a case is set to this result",
                verbose_name="Result description",
            ),
        ),
    ]