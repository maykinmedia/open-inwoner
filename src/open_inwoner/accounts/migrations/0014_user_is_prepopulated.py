# Generated by Django 3.2.7 on 2021-12-07 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_alter_user_deactivated_on"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_prepopulated",
            field=models.BooleanField(
                default=False,
                help_text="Indicates if fields have been prepopulated by Haal Central API.",
                verbose_name="prepopulated",
            ),
        ),
    ]
