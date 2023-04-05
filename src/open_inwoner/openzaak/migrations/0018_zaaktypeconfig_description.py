# Generated by Django 3.2.15 on 2023-04-04 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0017_auto_20230331_1418"),
    ]

    operations = [
        migrations.AddField(
            model_name="zaaktypeconfig",
            name="description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Description - clarification of why a user should upload a document for this case type",
                verbose_name="Description",
            ),
        ),
    ]
