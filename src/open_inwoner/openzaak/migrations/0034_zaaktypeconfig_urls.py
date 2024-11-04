# Generated by Django 3.2.20 on 2023-11-20 10:06

from django.db import migrations, models
import django_jsonform.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0033_openzaakconfig_enable_categories_filtering_with_zaken"),
    ]

    operations = [
        migrations.AddField(
            model_name="zaaktypeconfig",
            name="urls",
            field=django_jsonform.models.fields.ArrayField(
                base_field=models.URLField(verbose_name="Zaaktype URL"),
                default=list,
                size=None,
            ),
        ),
    ]
