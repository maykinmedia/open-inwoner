# Generated by Django 3.2.12 on 2022-02-18 12:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import colorfield.fields
import filer.fields.image


class Migration(migrations.Migration):

    dependencies = [
        ("flatpages", "0001_initial"),
        migrations.swappable_dependency(settings.FILER_IMAGE_MODEL),
        (
            "configurations",
            "0008_merge_0007_auto_20220202_1307_0007_auto_20220202_1835",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="siteconfiguration",
            name="accent_color",
            field=colorfield.fields.ColorField(
                default="#FFFFFF",
                help_text="The accent color of the municipality's site",
                max_length=18,
                verbose_name="Accent color",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="accent_font_color",
            field=models.CharField(
                choices=[("#FFFFFF", "light"), ("#4B4B4B", "dark")],
                default="#4B4B4B",
                help_text="The font color for when the background is the accent color",
                max_length=50,
                verbose_name="Accent font color",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="flatpages",
            field=models.ManyToManyField(
                related_name="configurations",
                through="configurations.SiteConfigurationPage",
                to="flatpages.FlatPage",
                verbose_name="Flatpages",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="hero_image_login",
            field=filer.fields.image.FilerImageField(
                blank=True,
                help_text="Hero image on the login page",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="hero_image_login",
                to=settings.FILER_IMAGE_MODEL,
                verbose_name="Hero image login",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="logo",
            field=filer.fields.image.FilerImageField(
                blank=True,
                help_text="Logo of the municipality",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="site_logo",
                to=settings.FILER_IMAGE_MODEL,
                verbose_name="Logo",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="name",
            field=models.CharField(
                help_text="The name of the municipality",
                max_length=255,
                verbose_name="Name",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="primary_color",
            field=colorfield.fields.ColorField(
                default="#FFFFFF",
                help_text="The primary color of the municipality's site",
                max_length=18,
                verbose_name="Primary color",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="primary_font_color",
            field=models.CharField(
                choices=[("#FFFFFF", "light"), ("#4B4B4B", "dark")],
                default="#FFFFFF",
                help_text="The font color for when the background is the primary color",
                max_length=50,
                verbose_name="Primary font color",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="secondary_color",
            field=colorfield.fields.ColorField(
                default="#FFFFFF",
                help_text="The secondary color of the municipality's site",
                max_length=18,
                verbose_name="Secondary color",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="secondary_font_color",
            field=models.CharField(
                choices=[("#FFFFFF", "light"), ("#4B4B4B", "dark")],
                default="#FFFFFF",
                help_text="The font color for when the background is the secondary color",
                max_length=50,
                verbose_name="Secondary font color",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfigurationpage",
            name="configuration",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ordered_configurations",
                to="configurations.siteconfiguration",
                verbose_name="Configuration",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfigurationpage",
            name="flatpage",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ordered_flatpages",
                to="flatpages.flatpage",
                verbose_name="Flatpage",
            ),
        ),
    ]
