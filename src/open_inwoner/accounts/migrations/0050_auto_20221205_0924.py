# Generated by Django 3.2.15 on 2022-12-05 08:24

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("plans", "0011_remove_plan_contacts"),
        ("accounts", "0049_auto_20221205_0921"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="invite",
            name="contact",
        ),
        migrations.AlterField(
            model_name="invite",
            name="invitee_first_name",
            field=models.CharField(
                help_text="The first name of the invitee.",
                max_length=250,
                verbose_name="First name",
            ),
        ),
        migrations.AlterField(
            model_name="invite",
            name="invitee_last_name",
            field=models.CharField(
                help_text="The last name of the invitee",
                max_length=250,
                verbose_name="Last name",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4,
                help_text="Unique identifier.",
                unique=True,
                verbose_name="UUID",
            ),
        ),
        migrations.DeleteModel(
            name="Contact",
        ),
    ]
