from datetime import date

from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from mail_editor.models import MailTemplate

DEFAULT_CUTOFF = date(2026, 3, 4)


class Command(BaseCommand):
    help = (
        "List mail templates saved on or after a given date (default: 2026-03-04), "
        "when CKEditor was re-added without CKEDITOR_CONFIGS, which may have stripped "
        "CSS classes from the body. Pass --email to receive the full template bodies "
        "at that address."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--since",
            type=date.fromisoformat,
            default=DEFAULT_CUTOFF,
            metavar="YYYY-MM-DD",
            help=f"Only report templates saved on or after this date (default: {DEFAULT_CUTOFF}).",
        )
        parser.add_argument(
            "--email",
            help="Send the affected templates to this address.",
        )

    def handle(self, *args, **options):
        since = options["since"]
        ct = ContentType.objects.get_for_model(MailTemplate)

        log_entries = (
            LogEntry.objects.filter(
                content_type=ct,
                action_time__date__gte=since,
                action_flag__in=[ADDITION, CHANGE],
            )
            .select_related("user")
            .order_by("object_id", "action_time")
        )

        if not log_entries.exists():
            self.stdout.write(f"No mail templates were saved on or after {since}.")
            return

        # LogEntry.object_id is a CharField; cast to int to avoid a type mismatch in Postgre
        affected_pks = [
            int(pk) for pk in log_entries.values_list("object_id", flat=True).distinct()
        ]
        templates = MailTemplate.objects.filter(pk__in=affected_pks).order_by(
            "template_type", "language"
        )
        entries_by_pk = {}
        for entry in log_entries:
            entries_by_pk.setdefault(entry.object_id, []).append(entry)

        self.stdout.write(
            self.style.WARNING(
                f"Found {templates.count()} mail template(s) saved on or after {since}:"
            )
        )
        self.stdout.write("")

        blocks = []
        for template in templates:
            pk_str = str(template.pk)
            saves = entries_by_pk.get(pk_str, [])
            last_save = saves[-1]

            label = template.template_type
            if template.language:
                label += f" ({template.language})"

            self.stdout.write(self.style.SUCCESS(label))
            self.stdout.write(f"  Subject : {template.subject}")
            self.stdout.write(
                f"  Last saved : {last_save.action_time:%Y-%m-%d %H:%M} "
                f"by {last_save.user}"
            )
            self.stdout.write(f"  Saves since cutoff : {len(saves)}")
            self.stdout.write("")

            blocks.append((label, template))

        email_address = options["email"]
        if not email_address:
            return

        domain = get_current_site(None).domain
        lines = []
        list_items = []

        for label, template in blocks:
            path = reverse("admin:mail_editor_mailtemplate_change", args=[template.pk])
            url = f"https://{domain}{path}"
            lines.append(f"{label}: {url}")
            list_items.append(f'<li><a href="{url}">{label}</a></li>')

        subject = f"Mail templates saved on or after {since}"
        plain_body = "\n".join(lines)
        html_body = f"<ul>{''.join(list_items)}</ul>"

        message = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            to=[email_address],
        )
        message.attach_alternative(html_body, "text/html")

        try:
            message.send()
        except Exception as exc:
            raise CommandError(f"Failed to send email: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"Sent to {email_address}."))
