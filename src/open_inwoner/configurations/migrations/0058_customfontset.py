# Generated by Django 3.2.23 on 2024-01-29 10:45

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import open_inwoner.configurations.models
import open_inwoner.utils.files


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0057_siteconfiguration_theme_stylesheet"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomFontSet",
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
                    "text_body_font",
                    open_inwoner.configurations.models.CustomFontField(
                        blank=True,
                        help_text="Upload text body font. TTF font types only.",
                        null=True,
                        storage=open_inwoner.utils.files.OverwriteStorage(),
                        upload_to=open_inwoner.configurations.models.CustomFontSet.update_filename_body,
                        validators=[
                            django.core.validators.FileExtensionValidator(["ttf"])
                        ],
                        verbose_name="Text body font",
                    ),
                ),
                (
                    "heading_font",
                    open_inwoner.configurations.models.CustomFontField(
                        blank=True,
                        help_text="Upload heading font. TTF font types only.",
                        null=True,
                        storage=open_inwoner.utils.files.OverwriteStorage(),
                        upload_to=open_inwoner.configurations.models.CustomFontSet.update_filename_heading,
                        validators=[
                            django.core.validators.FileExtensionValidator(["ttf"])
                        ],
                        verbose_name="Heading font",
                    ),
                ),
                (
                    "site_configuration",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="custom_fonts",
                        to="configurations.siteconfiguration",
                        verbose_name="Configuration",
                    ),
                ),
            ],
        ),
    ]
