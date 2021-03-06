# Generated by Django 3.2.12 on 2022-05-04 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0036_alter_user_login_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="contact_type",
            field=models.CharField(
                choices=[
                    ("contact", "Contactpersoon"),
                    ("begeleider", "Begeleider"),
                    ("organization", "Organisatie"),
                ],
                default="contact",
                help_text="The type of contact",
                max_length=200,
                verbose_name="Contact type",
            ),
        ),
    ]
