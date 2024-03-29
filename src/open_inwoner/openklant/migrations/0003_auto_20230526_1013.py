# Generated by Django 3.2.15 on 2023-05-26 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("openklant", "0002_auto_20230519_1210"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="contactformsubject",
            options={
                "ordering": ("subject",),
                "verbose_name": "Contact formulier onderwerp",
                "verbose_name_plural": "Contact formulier onderwerpen",
            },
        ),
        migrations.AddField(
            model_name="openklantconfig",
            name="register_employee_id",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Gebruikersnaam van actieve medewerker uit e-Suite",
                max_length=24,
                verbose_name="Medewerker identificatie",
            ),
        ),
        migrations.AddField(
            model_name="openklantconfig",
            name="register_type",
            field=models.CharField(
                blank=True,
                default="Melding",
                help_text="Naam van 'contacttype' uit e-Suite",
                max_length=50,
                verbose_name="Contactmoment type",
            ),
        ),
        migrations.AlterField(
            model_name="openklantconfig",
            name="register_bronorganisatie_rsin",
            field=models.CharField(
                blank=True, default="", max_length=9, verbose_name="Organisatie RSIN"
            ),
        ),
    ]
