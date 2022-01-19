# Generated by Django 3.2.7 on 2022-01-10 14:29

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("filer", "0012_file_mime_type"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("plans", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="PlanFiles",
            new_name="PlanFile",
        ),
        migrations.AddField(
            model_name="plan",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="plan",
            name="created_by",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="accounts.user",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="plan",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="goal",
            name="explaination",
            field=models.TextField(help_text=""),
        ),
    ]
