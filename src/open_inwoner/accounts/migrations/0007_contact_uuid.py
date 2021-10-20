# Generated by Django 3.2.7 on 2021-10-19 09:14

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_auto_20211013_1415"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4,
                help_text="Used as a reference in the contacts api.",
                unique=True,
                verbose_name="UUID",
            ),
        ),
    ]
