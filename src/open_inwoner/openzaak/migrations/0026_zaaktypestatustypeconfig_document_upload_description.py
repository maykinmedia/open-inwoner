# Generated by Django 3.2.20 on 2023-10-16 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0025_auto_20231016_0957"),
    ]

    operations = [
        migrations.AddField(
            model_name="zaaktypestatustypeconfig",
            name="document_upload_description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Description that will be shown above the document upload widget in a case detail page",
                verbose_name="Document upload description",
            ),
        ),
    ]