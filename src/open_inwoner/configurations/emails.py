from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from django_yubin.models import Message
from mail_editor.helpers import find_template

from open_inwoner.configurations.models import SiteConfiguration


def inform_admins_about_failing_emails():
    config = SiteConfiguration.get_solo()
    inform_users = config.recipients_email_digest

    if not inform_users:
        return

    now = timezone.now()
    period_start = now - timedelta(days=1)

    failed_emails = (
        Message.objects.filter(
            date_created__gt=period_start, status=Message.STATUS_FAILED
        )
        .annotate(recipient=F("to_address"), date=F("date_created"))
        .values("subject", "recipient", "date")
    )

    if not failed_emails:
        return

    template = find_template("daily_email_digest")
    context = {"failed_emails": failed_emails, "date": now.date()}

    return template.send_email(inform_users, context)
