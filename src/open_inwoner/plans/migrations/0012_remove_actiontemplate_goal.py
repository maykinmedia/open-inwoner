# Generated by Django 3.2.15 on 2023-02-22 15:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("plans", "0011_remove_plan_contacts"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="actiontemplate",
            name="goal",
        ),
    ]
