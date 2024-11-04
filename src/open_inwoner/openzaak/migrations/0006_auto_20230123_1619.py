# Generated by Django 3.2.15 on 2023-01-23 15:19

from django.db import migrations, models
import django_jsonform.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0005_openzaakconfig_zaak_max_confidentiality"),
    ]

    operations = [
        migrations.AddField(
            model_name="openzaakconfig",
            name="allowed_file_extensions",
            field=django_jsonform.models.fields.ArrayField(
                base_field=models.CharField(
                    max_length=8, verbose_name="Allowed file extensions"
                ),
                default=[
                    "pdf",
                    "doc",
                    "docx",
                    "xls",
                    "xlsx",
                    "ppt",
                    "pptx",
                    "vsd",
                    "png",
                    "gif",
                    "jpg",
                    "tiff",
                    "msg",
                    "txt",
                    "rtf",
                    "jpeg",
                    "bmp",
                ],
                help_text="A list of the allowed file extensions.",
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="openzaakconfig",
            name="max_upload_size",
            field=models.PositiveIntegerField(
                default=50,
                help_text="The max size of the file (in MB) which is uploaded.",
                verbose_name="Max upload file size (in MB)",
            ),
        ),
    ]
