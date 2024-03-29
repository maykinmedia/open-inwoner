# Generated by Django 3.2.20 on 2023-11-28 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0036_zaaktypeconfig_relevante_zaakperiode"),
    ]

    operations = [
        migrations.AddField(
            model_name="openzaakconfig",
            name="fetch_eherkenning_zaken_with_rsin",
            field=models.BooleanField(
                default=True,
                help_text="If enabled, Zaken for eHerkenning users are fetched using the company RSIN (Open Zaak). If not enabled, Zaken are fetched using the KvK number (eSuite).",
                verbose_name="Fetch Zaken for users authenticated with eHerkenning using RSIN",
            ),
        ),
    ]
