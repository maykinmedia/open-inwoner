from email import message_from_bytes, policy
from unittest.mock import patch

from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import TestCase, override_settings
from django.urls import reverse

from django_yubin import mailparser_utils
from django_yubin.models import Message
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import UserFactory

PDF_CONTENT = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\nfake pdf content\n"


def build_email() -> EmailMultiAlternatives:
    email = EmailMultiAlternatives(
        subject="Bevestiging aanvraag – café",
        body="Beste inwoner,\n\nUw aanvraag is ontvangen.",
        from_email="noreply@example.com",
        to=["to@example.com"],
        cc=["cc@example.com"],
        headers={"X-Mail-Queue-Priority": "now"},
    )
    email.attach_alternative("<p>Uw aanvraag is <b>ontvangen</b>.</p>", "text/html")
    email.attach("aanvraag.pdf", PDF_CONTENT, "application/pdf")
    return email


def summarise(email: EmailMultiAlternatives) -> dict:
    # parse with the stdlib so mail-parser isn't validating its own output
    msg = message_from_bytes(email.message().as_bytes(), policy=policy.default)
    return {
        "subject": msg["Subject"],
        "from": msg["From"],
        "to": msg["To"],
        "cc": msg["Cc"],
        "x-mail-queue-priority": msg["X-Mail-Queue-Priority"],
        "text": msg.get_body(("plain",)).get_content().strip(),
        "html": msg.get_body(("html",)).get_content().strip(),
        "attachments": [
            (part.get_filename(), part.get_content_type(), part.get_content())
            for part in msg.iter_attachments()
        ],
    }


@override_settings(
    EMAIL_BACKEND="django_yubin.backends.QueuedEmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
)
# yubin reads MAILER_* settings at import time, so override_settings has no effect
@patch(
    "django_yubin.settings.USE_BACKEND",
    "django.core.mail.backends.locmem.EmailBackend",
)
class YubinQueuedEmailTests(TestCase):
    def send_queued(self, email: EmailMultiAlternatives) -> Message:
        with self.captureOnCommitCallbacks(execute=True):
            email.send()
        return Message.objects.get()

    def test_queued_email_is_sent_unchanged(self):
        email = build_email()

        message = self.send_queued(email)

        self.assertEqual(
            message.status,
            Message.STATUS_SENT,
            msg=list(message.log_set.values_list("log_message", flat=True)),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(summarise(mail.outbox[0]), summarise(email))


# the send task only runs on commit, so the message stays queued
@disable_admin_mfa()
@override_settings(EMAIL_BACKEND="django_yubin.backends.QueuedEmailBackend")
class YubinMessageAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(is_superuser=True, is_staff=True)

    def setUp(self):
        self.client.force_login(self.user)
        build_email().send()
        self.message = Message.objects.get()

    def test_change_view(self):
        response = self.client.get(
            reverse("admin:django_yubin_message_change", args=(self.message.pk,))
        )

        self.assertEqual(response.status_code, 200)

    def test_detail_view(self):
        response = self.client.get(
            reverse("admin:mail_detail", args=(self.message.pk,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bevestiging aanvraag – café")
        self.assertContains(response, "aanvraag.pdf")

    def test_html_view(self):
        response = self.client.get(reverse("admin:mail_html", args=(self.message.pk,)))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<p>Uw aanvraag is <b>ontvangen</b>.</p>")

    def test_download_attachment(self):
        attachment = self.message.get_message_parser().attachments[0]
        signature = mailparser_utils.get_signature(attachment)

        response = self.client.get(
            reverse("admin:mail_download", args=(self.message.pk, signature))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response.content, PDF_CONTENT)
