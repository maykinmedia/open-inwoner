# Generated by Django 3.2.13 on 2022-05-03 12:18

from django.db import migrations


def forwards(apps, schema_editor):
    QuestionnaireStep = apps.get_model("questionnaire", "QuestionnaireStep")
    for questionnaire_step in QuestionnaireStep.objects.all():
        questionnaire_step.code = questionnaire_step.slug
        questionnaire_step.save()


def backwards(apps, schema_editor):
    QuestionnaireStep = apps.get_model("questionnaire", "QuestionnaireStep")
    for questionnaire_step in QuestionnaireStep.objects.all():
        questionnaire_step.code = ""
        questionnaire_step.save()


class Migration(migrations.Migration):
    dependencies = [
        ("questionnaire", "0012_questionnairestep_code"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
