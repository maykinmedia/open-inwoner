# Generated by Django 3.2.12 on 2022-03-30 12:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0015_siteconfiguration_show_product_finder"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="siteconfigurationpage",
            options={
                "verbose_name": "Flatpage in the footer",
                "verbose_name_plural": "Flatpages in the footer",
            },
        ),
    ]
