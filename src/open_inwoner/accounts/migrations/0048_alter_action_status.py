# Generated by Django 3.2.15 on 2022-12-06 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0047_action_is_deleted"),
    ]

    operations = [
        migrations.AlterField(
            model_name="action",
            name="status",
            field=models.CharField(
                choices=[
                    ("open", "Open"),
                    ("approval", "Accordering"),
                    ("closed", "Afgerond"),
                ],
                default="open",
                help_text="The current status of the action",
                max_length=200,
                verbose_name="Status",
            ),
        ),
    ]
