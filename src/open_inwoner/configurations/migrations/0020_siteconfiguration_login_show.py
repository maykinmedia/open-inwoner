# Generated by Django 3.2.13 on 2022-09-20 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0019_auto_20220704_1002"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfiguration",
            name="login_show",
            field=models.BooleanField(
                default=True,
                help_text="Wanneer deze optie uit staat dan kan nog wel worden ingelogd via /accounts/login/ , echter het inloggen is verborgen",
                verbose_name="Toon inlogknop rechts bovenin",
            ),
        ),
    ]
