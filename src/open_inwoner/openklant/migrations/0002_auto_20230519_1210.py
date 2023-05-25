# Generated by Django 3.2.15 on 2023-05-19 10:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_consumers", "0016_auto_20220818_1412"),
        ("openklant", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="openklantconfig",
            name="register_bronorganisatie_rsin",
            field=models.CharField(
                blank=True, default="", max_length=9, verbose_name="RSIN"
            ),
        ),
        migrations.AddField(
            model_name="openklantconfig",
            name="register_contact_moment",
            field=models.BooleanField(
                default=False, verbose_name="Registreer in Contactmomenten API"
            ),
        ),
        migrations.AddField(
            model_name="openklantconfig",
            name="register_email",
            field=models.EmailField(
                blank=True, max_length=254, verbose_name="Registreer op email adres"
            ),
        ),
        migrations.AlterField(
            model_name="openklantconfig",
            name="contactmomenten_service",
            field=models.OneToOneField(
                blank=True,
                limit_choices_to={"api_type": "cmc"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="zgw_consumers.service",
                verbose_name="Contactmomenten API",
            ),
        ),
        migrations.AlterField(
            model_name="openklantconfig",
            name="klanten_service",
            field=models.OneToOneField(
                blank=True,
                limit_choices_to={"api_type": "kc"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="zgw_consumers.service",
                verbose_name="Klanten API",
            ),
        ),
        migrations.CreateModel(
            name="ContactFormSubject",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("subject", models.CharField(max_length=255, verbose_name="Onderwerp")),
                (
                    "config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="openklant.openklantconfig",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contact formulier onderwerp",
                "ordering": ("subject",),
            },
        ),
    ]