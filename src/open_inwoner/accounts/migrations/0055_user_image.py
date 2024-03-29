# Generated by Django 3.2.15 on 2023-02-28 08:45

from django.db import migrations, models
import open_inwoner.accounts.models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0054_remove_action_goal"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text="Image",
                null=True,
                upload_to=open_inwoner.accounts.models.generate_uuid_image_name,
                verbose_name="Image",
            ),
        ),
    ]
