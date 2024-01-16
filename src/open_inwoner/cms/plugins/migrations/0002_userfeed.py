# Generated by Django 3.2.23 on 2024-01-05 08:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0022_auto_20180620_1551"),
        ("plugins", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserFeed",
            fields=[
                (
                    "cmsplugin_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        related_name="plugins_userfeed",
                        serialize=False,
                        to="cms.cmsplugin",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("cms.cmsplugin",),
        ),
    ]