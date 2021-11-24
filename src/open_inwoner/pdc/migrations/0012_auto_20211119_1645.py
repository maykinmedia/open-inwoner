# Generated by Django 3.2.7 on 2021-11-19 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0011_migrate_slugs"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organization",
            name="slug",
            field=models.SlugField(
                help_text="Slug of the organization",
                max_length=100,
                unique=True,
                verbose_name="slug",
            ),
        ),
        migrations.AlterField(
            model_name="tag",
            name="slug",
            field=models.SlugField(
                help_text="Slug of the tag",
                max_length=100,
                unique=True,
                verbose_name="slug",
            ),
        ),
    ]
