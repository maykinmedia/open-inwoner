# Generated by Django 3.2.7 on 2021-10-13 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_auto_20211008_1311"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="rsin",
            field=models.CharField(blank=True, max_length=9, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="login_type",
            field=models.CharField(
                choices=[
                    ("default", "Email en Wachtwoord"),
                    ("digid", "DigiD"),
                    ("eherkenning", "eHerkenning"),
                ],
                default="default",
                max_length=250,
            ),
        ),
    ]
