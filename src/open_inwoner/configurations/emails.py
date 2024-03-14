from datetime import timedelta

from django.utils import timezone

from mail_editor.helpers import find_template
from mailer.models import RESULT_SUCCESS, MessageLog

from open_inwoner.configurations.models import SiteConfiguration


def inform_admins_about_failing_emails():
    config = SiteConfiguration.get_solo()
    inform_users = config.recipients_email_digest

    if not inform_users:
        return
    now = timezone.now()
    period_start = now - timedelta(days=1)

    failed_email_objects = MessageLog.objects.filter(
        when_attempted__gt=period_start
    ).exclude(result=RESULT_SUCCESS)

    # wrap with what the existing mail-template expects
    failed_email_logs = []
    for log in failed_email_objects:
        # re-use expensive pickled .email property
        email = log.email
        failed_email_logs.append(
            {
                "subject": email.subject,
                "recipient": ", ".join(email.to),
                "date": log.when_attempted,
            }
        )

    if not failed_email_logs:
        return

    template = find_template("daily_email_digest")
    context = {"failed_emails": failed_email_logs, "date": now.date()}

    return template.send_email(inform_users, context)
