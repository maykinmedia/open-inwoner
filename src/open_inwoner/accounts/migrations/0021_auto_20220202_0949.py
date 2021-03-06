# Generated by Django 3.2.7 on 2022-02-02 08:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import privates.storages


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0020_invite"),
    ]

    operations = [
        migrations.AddField(
            model_name="action",
            name="description",
            field=models.TextField(
                blank=True,
                default="",
                help_text="The description of the action",
                verbose_name="description",
            ),
        ),
        migrations.AddField(
            model_name="action",
            name="file",
            field=models.FileField(
                blank=True,
                help_text="The document that is uploaded to the file",
                null=True,
                storage=privates.storages.PrivateMediaFileSystemStorage(),
                upload_to="",
                verbose_name="File",
            ),
        ),
        migrations.AddField(
            model_name="action",
            name="goal",
            field=models.CharField(
                blank=True,
                default="",
                help_text="The goal of the action",
                max_length=250,
                verbose_name="goal",
            ),
        ),
        migrations.AddField(
            model_name="action",
            name="is_for",
            field=models.ForeignKey(
                blank=True,
                help_text="The person that needs to do this action.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="actions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Is for",
            ),
        ),
    ]
