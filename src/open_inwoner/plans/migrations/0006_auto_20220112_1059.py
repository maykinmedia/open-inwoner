# Generated by Django 3.2.7 on 2022-01-12 09:59

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plans", "0005_auto_20220110_1733"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="plan",
            name="slug",
        ),
        migrations.AddField(
            model_name="plan",
            name="uuid",
            field=models.UUIDField(auto_created=True, blank=True, default=uuid.uuid4),
        ),
        migrations.AlterField(
            model_name="goal",
            name="explaination",
            field=models.TextField(help_text=""),
        ),
    ]
