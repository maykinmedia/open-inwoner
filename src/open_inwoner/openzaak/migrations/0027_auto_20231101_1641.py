# Generated by Django 3.2.20 on 2023-11-01 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0026_zaaktypestatustypeconfig_document_upload_description"),
    ]

    operations = [
        migrations.AlterField(
            model_name="openzaakconfig",
            name="title_text",
            field=models.TextField(
                default="Hier vindt u een overzicht van al uw lopende en afgeronde aanvragen.",
                help_text="The title/introductory text shown on the list view of 'Mijn aanvragen'.",
                verbose_name="Title text",
            ),
        ),
        migrations.AlterField(
            model_name="zaaktypestatustypeconfig",
            name="status_indicator",
            field=models.CharField(
                blank=True,
                choices=[
                    ("info", "Info"),
                    ("warning", "Warning"),
                    ("failure", "Failure"),
                    ("success", "Success"),
                ],
                help_text="Determines what color will be shown to the user if a case is set to this status",
                max_length=32,
                verbose_name="Statustype indicator",
            ),
        ),
        migrations.AlterField(
            model_name="zaaktypestatustypeconfig",
            name="status_indicator_text",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Determines the text that will be shown to the user if a case is set to this status",
                verbose_name="Statustype indicator text",
            ),
        ),
    ]
