# Generated by Django 3.2.23 on 2024-02-08 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0066_category_access_groups"),
        ("accounts", "0072_merge_20240129_1610"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="selected_categories",
            field=models.ManyToManyField(
                blank=True,
                related_name="selected_by",
                to="pdc.Category",
                verbose_name="Selected categories",
            ),
        ),
    ]
