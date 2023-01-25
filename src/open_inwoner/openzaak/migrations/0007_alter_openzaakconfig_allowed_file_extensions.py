# Generated by Django 3.2.15 on 2023-01-25 10:12

from django.db import migrations, models
import django_better_admin_arrayfield.models.fields
import open_inwoner.openzaak.models


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0006_auto_20230123_1619"),
    ]

    operations = [
        migrations.AlterField(
            model_name="openzaakconfig",
            name="allowed_file_extensions",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(
                    max_length=8, verbose_name="Allowed file extensions"
                ),
                default=open_inwoner.openzaak.models.generate_default_file_extensions,
                help_text="A list of the allowed file extensions.",
                size=None,
            ),
        ),
    ]
