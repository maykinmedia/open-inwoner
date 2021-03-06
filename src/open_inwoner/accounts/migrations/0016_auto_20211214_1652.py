# Generated by Django 3.2.7 on 2021-12-14 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0016_merge_20211206_1627"),
        ("accounts", "0015_auto_20211214_1136"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="action",
            options={"ordering": ("-updated_on", "-created_on")},
        ),
        migrations.AddField(
            model_name="user",
            name="selected_themes",
            field=models.ManyToManyField(related_name="selected_by", to="pdc.Category"),
        ),
    ]
