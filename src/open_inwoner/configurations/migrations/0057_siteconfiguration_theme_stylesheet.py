# Generated by Django 3.2.23 on 2023-12-19 08:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0056_alter_siteconfiguration_eherkenning_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfiguration",
            name="theme_stylesheet",
            field=models.FileField(
                blank=True,
                help_text="Additional CSS file added to the page.",
                null=True,
                upload_to="themes/",
                validators=[django.core.validators.FileExtensionValidator(["css"])],
                verbose_name="Theme stylesheet",
            ),
        ),
    ]
