# Generated by Django 3.2.15 on 2023-02-20 10:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_consumers", "0016_auto_20220818_1412"),
        ("openzaak", "0014_auto_20230209_1055"),
    ]

    operations = [
        migrations.AddField(
            model_name="openzaakconfig",
            name="form_service",
            field=models.OneToOneField(
                limit_choices_to={"api_type": "orc"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="zgw_consumers.service",
                verbose_name="Form API",
            ),
        ),
    ]
