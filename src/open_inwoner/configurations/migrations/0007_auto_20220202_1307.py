# Generated by Django 3.2.7 on 2022-02-02 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0006_auto_20220117_1626"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfiguration",
            name="email_new_message",
            field=models.BooleanField(
                default=True,
                help_text="Whether to send email about each new message the user receives",
                verbose_name="Send email about a new message",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="login_allow_registration",
            field=models.BooleanField(
                default=False,
                help_text="Wanneer deze optie uit staat is het enkel toegestaan om met DigiD in te loggen. Zet deze instelling aan om ook het inloggen met gebruikersnaam/wachtwoord en het aanmelden zonder DigiD toe te staan.",
                verbose_name="Sta lokale registratie toe",
            ),
        ),
    ]
