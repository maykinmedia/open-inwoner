# Generated by Django 3.2.13 on 2022-05-18 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0041_migrate_invite_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invite",
            name="invitee_email",
            field=models.EmailField(
                help_text="The email used to send the invite",
                max_length=254,
                verbose_name="Invitee email",
            ),
        ),
    ]
