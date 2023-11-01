# Generated by Django 3.2.20 on 2023-10-26 10:05

import django.db.models.deletion
from django.db import migrations, models

import django_better_admin_arrayfield.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0026_zaaktypestatustypeconfig_document_upload_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="ZaakTypeResultaatTypeConfig",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "resultaattype_url",
                    models.URLField(max_length=1000, verbose_name="Resultaattype URL"),
                ),
                (
                    "omschrijving",
                    models.CharField(max_length=20, verbose_name="Omschrijving"),
                ),
                (
                    "zaaktype_uuids",
                    django_better_admin_arrayfield.models.fields.ArrayField(
                        base_field=models.UUIDField(verbose_name="Zaaktype UUID"),
                        default=list,
                        size=None,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Determines the text that will be shown to the user if a case is set to this result",
                        verbose_name="Frontend description",
                    ),
                ),
                (
                    "zaaktype_config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="openzaak.zaaktypeconfig",
                    ),
                ),
            ],
            options={
                "verbose_name": "Zaaktype Resultaattype Configuration",
            },
        ),
        migrations.AddConstraint(
            model_name="zaaktyperesultaattypeconfig",
            constraint=models.UniqueConstraint(
                fields=("zaaktype_config", "resultaattype_url"),
                name="unique_zaaktype_config_resultaattype_url",
            ),
        ),
    ]
