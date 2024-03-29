# Generated by Django 3.2.23 on 2024-01-22 10:18

from django.db import migrations, models
import django_jsonform.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0057_siteconfiguration_theme_stylesheet"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfiguration",
            name="recipients_email_digest",
            field=django_jsonform.models.fields.ArrayField(
                base_field=models.EmailField(max_length=254),
                blank=True,
                default=list,
                help_text="The email addresses that should receive a daily report of items requiring attention.",
                size=None,
                verbose_name="recipients email digest",
            ),
        ),
    ]
