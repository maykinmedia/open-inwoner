# Generated by Django 3.2.7 on 2022-01-28 12:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_consumers", "0013_oas_field"),
        ("openzaak", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="openzaakconfig",
            old_name="service",
            new_name="zaak_service",
        ),
        migrations.AddField(
            model_name="openzaakconfig",
            name="catalogi_service",
            field=models.OneToOneField(
                limit_choices_to={"api_type": "ztc"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="zgw_consumers.service",
                verbose_name="Catalogi API",
            ),
        ),
    ]
