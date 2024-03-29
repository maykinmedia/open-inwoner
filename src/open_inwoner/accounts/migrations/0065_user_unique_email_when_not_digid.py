# Generated by Django 3.2.20 on 2023-09-07 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0064_alter_user_email"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("login_type", "digid"), _negated=True),
                fields=("email",),
                name="unique_email_when_not_digid",
            ),
        ),
    ]
