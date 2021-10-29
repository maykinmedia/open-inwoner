# Generated by Django 3.2.7 on 2021-10-27 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0008_alter_product_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(
                help_text="Slug of the category",
                max_length=100,
                unique=True,
                verbose_name="slug",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.SlugField(
                help_text="Slug of the category",
                max_length=100,
                unique=True,
                verbose_name="slug",
            ),
        ),
    ]
