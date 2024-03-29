# Generated by Django 3.2.15 on 2023-08-09 06:33

from django.db import migrations, models

import colorfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0049_siteconfiguration_extra_css"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfiguration",
            name="warning_banner_background_color",
            field=colorfield.fields.ColorField(
                default="#FFDBAD",
                help_text="The background color for the warning banner",
                max_length=18,
                verbose_name="Warning banner background",
            ),
        ),
        migrations.AddField(
            model_name="siteconfiguration",
            name="warning_banner_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Whether the warning banner should be displayed",
                verbose_name="Show warning banner",
            ),
        ),
        migrations.AddField(
            model_name="siteconfiguration",
            name="warning_banner_font_color",
            field=colorfield.fields.ColorField(
                default="#000000",
                help_text="The font color for the warning banner",
                max_length=18,
                verbose_name="Warning banner font",
            ),
        ),
        migrations.AddField(
            model_name="siteconfiguration",
            name="warning_banner_text",
            field=models.TextField(
                blank=True,
                help_text="Text will be displayed on the warning banner",
                verbose_name="Warning banner text",
            ),
        ),
    ]
