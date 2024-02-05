# Generated by Django 3.2.23 on 2024-01-19 15:02

from django.db import migrations


def split_case_notification_mail_template(apps, schema_editor):
    """
    Split the `case_notification` email template into two separate templates, one for
    status notifications and one for document notifications
    """
    MailTemplate = apps.get_model("mail_editor", "MailTemplate")

    case_notification_template = MailTemplate.objects.filter(
        template_type="case_notification"
    ).first()

    if case_notification_template:
        case_notification_template.template_type = "case_status_notification"
        case_notification_template.save()

        case_notification_template.pk = None
        case_notification_template.template_type = "case_document_notification"
        case_notification_template.save()


def join_case_notification_mail_template(apps, schema_editor):
    MailTemplate = apps.get_model("mail_editor", "MailTemplate")

    case_notification_template = MailTemplate.objects.get(
        template_type="case_status_notification"
    )
    MailTemplate.objects.get(template_type="case_document_notification").delete()

    case_notification_template.template_type = "case_notification"
    case_notification_template.save()


class Migration(migrations.Migration):

    dependencies = [
        ("mail_editor", "0001_initial"),
        ("openzaak", "0041_configuration_cases_button"),
    ]

    operations = [
        migrations.RunPython(
            split_case_notification_mail_template, join_case_notification_mail_template
        )
    ]