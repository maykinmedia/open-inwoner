# Generated by Django 4.2.11 on 2024-03-28 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0064_auto_20240304_1200"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfiguration",
            name="email_verification_required",
            field=models.BooleanField(
                default=False,
                help_text="Whether to require users to verify their email address",
                verbose_name="Email verification required",
            ),
        ),
    ]