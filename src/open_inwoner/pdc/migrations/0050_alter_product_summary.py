# Generated by Django 3.2.15 on 2023-02-22 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0049_auto_20230222_0901"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="summary",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Short description of the product, limited to 300 characters.",
                max_length=300,
                verbose_name="Summary",
            ),
        ),
    ]
