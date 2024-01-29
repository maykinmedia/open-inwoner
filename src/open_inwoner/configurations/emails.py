from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from django_yubin.constants import RESULT_FAILED
from django_yubin.models import Log
from mail_editor.helpers import find_template

from open_inwoner.configurations.models import SiteConfiguration


def inform_admins_about_failing_emails():
    config = SiteConfiguration.get_solo()
    inform_users = config.recipients_email_digest

    if not inform_users:
        return

    now = timezone.now()
    period_start = now - timedelta(days=1)

    failed_email_logs = (
        Log.objects.filter(date__gt=period_start, result=RESULT_FAILED)
        .annotate(subject=F("message__subject"), recipient=F("message__to_address"))
        .values("subject", "recipient", "date")
    )

    if not failed_email_logs:
        return

    template = find_template("daily_email_digest")
    context = {"failed_emails": failed_email_logs, "date": now.date()}

    return template.send_email(inform_users, context)
