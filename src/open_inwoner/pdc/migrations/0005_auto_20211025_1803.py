# Generated by Django 3.2.7 on 2021-10-25 16:03

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import filer.fields.image
import localflavor.nl.models

import open_inwoner.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.FILER_IMAGE_MODEL),
        ("pdc", "0004_productlink_productlocation"),
    ]

    operations = [
        migrations.CreateModel(
            name="Neighbourhood",
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
                        help_text="Neighbourhood name",
                        max_length=100,
                        unique=True,
                        verbose_name="name",
                    ),
                ),
            ],
            options={
                "verbose_name": "neighbourhood",
                "verbose_name_plural": "neighbourhoods",
            },
        ),
        migrations.CreateModel(
            name="Organization",
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
                    "name",
                    models.CharField(
                        help_text="Name of the organization",
                        max_length=250,
                        verbose_name="name",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True,
                        help_text="The email address of the organization",
                        max_length=254,
                        verbose_name="Email address",
                    ),
                ),
                (
                    "phonenumber",
                    models.CharField(
                        blank=True,
                        help_text="The phone number of the organization",
                        max_length=100,
                        validators=[
                            open_inwoner.utils.validators.validate_phone_number
                        ],
                        verbose_name="Phonenumber",
                    ),
                ),
                (
                    "logo",
                    filer.fields.image.FilerImageField(
                        blank=True,
                        help_text="Logo of the orgaization",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="organization_logos",
                        to=settings.FILER_IMAGE_MODEL,
                    ),
                ),
                (
                    "neighbourhood",
                    models.ForeignKey(
                        blank=True,
                        help_text="The neighbourhood of the organization",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="organization",
                        to="pdc.neighbourhood",
                    ),
                ),
            ],
            options={
                "verbose_name": "organization",
                "verbose_name_plural": "organizations",
            },
        ),
        migrations.CreateModel(
            name="OrganizationType",
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
                        help_text="Organization type",
                        max_length=100,
                        unique=True,
                        verbose_name="name",
                    ),
                ),
            ],
            options={
                "verbose_name": "organization type",
                "verbose_name_plural": "organization types",
            },
        ),
        migrations.CreateModel(
            name="ProductContact",
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
                    "first_name",
                    models.CharField(
                        help_text="First name of the product contact",
                        max_length=255,
                        verbose_name="first name",
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        help_text="Last name of the product contact",
                        max_length=255,
                        verbose_name="last name",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True,
                        help_text="The email address of the product contact",
                        max_length=254,
                        verbose_name="Email address",
                    ),
                ),
                (
                    "phonenumber",
                    models.CharField(
                        blank=True,
                        help_text="The phone number of the product contact",
                        max_length=100,
                        validators=[
                            open_inwoner.utils.validators.validate_phone_number
                        ],
                        verbose_name="Phonenumber",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        help_text="The organization of the product contact",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="product_contacts",
                        to="pdc.organization",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        help_text="Related product",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_contacts",
                        to="pdc.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "product contact",
                "verbose_name_plural": "product contacts",
            },
        ),
        migrations.AddField(
            model_name="organization",
            name="type",
            field=models.ForeignKey(
                help_text="Organization type",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="organizations",
                to="pdc.organizationtype",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="organizations",
            field=models.ManyToManyField(
                blank=True,
                help_text="Organizations which provides this product",
                related_name="products",
                to="pdc.Organization",
            ),
        ),
    ]
