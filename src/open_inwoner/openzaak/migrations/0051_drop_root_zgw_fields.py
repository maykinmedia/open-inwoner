# Generated by Django 4.2.11 on 2024-06-04 10:02

import logging
from django.db import migrations


logger = logging.getLogger(__name__)


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0050_migrate_zgw_root_fields_to_multi_backend"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="openzaakconfig",
            name="catalogi_service",
        ),
        migrations.RemoveField(
            model_name="openzaakconfig",
            name="document_service",
        ),
        migrations.RemoveField(
            model_name="openzaakconfig",
            name="form_service",
        ),
        migrations.RemoveField(
            model_name="openzaakconfig",
            name="zaak_service",
        ),
    ]