# Generated by Django 3.2.7 on 2022-01-12 14:53

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plans", "0010_auto_20220112_1215"),
    ]

    operations = [
        migrations.AddField(
            model_name="planfile",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]
