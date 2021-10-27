# Generated by Django 3.2.7 on 2021-10-20 13:21

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models

import localflavor.nl.models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0003_auto_20211020_1234"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductLocation",
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
                    "street",
                    models.CharField(
                        blank=True,
                        help_text="Address street",
                        max_length=250,
                        verbose_name="street",
                    ),
                ),
                (
                    "housenumber",
                    models.CharField(
                        blank=True,
                        help_text="Address house number",
                        max_length=250,
                        verbose_name="house number",
                    ),
                ),
                (
                    "postcode",
                    localflavor.nl.models.NLZipCodeField(
                        help_text="Address postcode",
                        max_length=7,
                        verbose_name="postcode",
                    ),
                ),
                (
                    "city",
                    models.CharField(
                        help_text="Address city", max_length=250, verbose_name="city"
                    ),
                ),
                (
                    "geometry",
                    django.contrib.gis.db.models.fields.PointField(
                        help_text="Geo coordinates of the location",
                        srid=4326,
                        verbose_name="geometry",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        help_text="Related product",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="locations",
                        to="pdc.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "product location",
                "verbose_name_plural": "product locations",
            },
        ),
        migrations.CreateModel(
            name="ProductLink",
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
                    "name",
                    models.CharField(
                        help_text="Name for the link",
                        max_length=100,
                        verbose_name="name",
                    ),
                ),
                (
                    "url",
                    models.URLField(help_text="Url of the link", verbose_name="url"),
                ),
                (
                    "product",
                    models.ForeignKey(
                        help_text="Related product",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="links",
                        to="pdc.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "product link",
                "verbose_name_plural": "product links",
            },
        ),
    ]
