# Generated by Django 3.2.7 on 2021-10-13 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Description of the category",
                verbose_name="description",
            ),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="Product",
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
                        help_text="Name of the product",
                        max_length=100,
                        verbose_name="name",
                    ),
                ),
                (
                    "summary",
                    models.TextField(
                        blank=True,
                        help_text="Short description of the product",
                        verbose_name="summary",
                    ),
                ),
                (
                    "link",
                    models.URLField(
                        blank=True,
                        help_text="Action link to request the product",
                        verbose_name="link",
                    ),
                ),
                (
                    "content",
                    models.TextField(
                        help_text="Product content with build-in WYSIWYG editor",
                        verbose_name="content",
                    ),
                ),
                (
                    "costs",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Cost of the product in EUR",
                        max_digits=8,
                        verbose_name="costs",
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="This is the date the product was created. This field is automatically set.",
                        verbose_name="Created on",
                    ),
                ),
                (
                    "updated_on",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="This is the date when the product was last changed. This field is automatically set.",
                        verbose_name="Updated on",
                    ),
                ),
                (
                    "categories",
                    models.ManyToManyField(
                        help_text="Categories which the product relates to",
                        related_name="product",
                        to="pdc.Category",
                    ),
                ),
                (
                    "related_products",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Related products to this product",
                        to="pdc.Product",
                    ),
                ),
            ],
            options={
                "verbose_name": "product",
                "verbose_name_plural": "products",
            },
        ),
    ]
