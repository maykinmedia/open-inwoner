# Generated by Django 3.2.15 on 2022-12-21 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0028_siteconfiguration_show_actions"),
    ]

    operations = [
        migrations.AlterField(
            model_name="siteconfiguration",
            name="home_questionnaire_intro",
            field=models.TextField(
                blank=True,
                default="Test met een paar simpele vragen of u recht heeft op een product",
                help_text="Questionnaire intro text on the home page.",
                verbose_name="Home page questionaire intro",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="plans_intro",
            field=models.TextField(
                blank=True,
                default="Hier werkt u aan uw doelen. Dit doet u samen met uw contactpersoon bij de gemeente. ",
                help_text="The sub-title for the plan page.",
                verbose_name="Plan pages intro",
            ),
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="select_questionnaire_intro",
            field=models.TextField(
                blank=True,
                default="Kies hieronder één van de volgende vragenlijsten om de zelfdiagnose te starten.",
                help_text="Questionaire selector intro on the theme and profile pages.",
                verbose_name="Questionaire selector widget intro",
            ),
        ),
    ]
