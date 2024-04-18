from django.core import mail
from django.test import TestCase

from open_inwoner.mail.service import send_contact_confirmation_mail


class TestServices(TestCase):
    def test_send_contact_confirmation_mail(self):
        send_contact_confirmation_mail("foo@example.com", "My subject")

        self.assertEqual(len(mail.outbox), 1)

        sent_mail = mail.outbox[0]
        html_body = sent_mail.alternatives[0][0]

        self.assertIn("Vraag ontvangen op ", sent_mail.subject)
        self.assertEqual(sent_mail.to, ["foo@example.com"])
        self.assertIn("My subject", html_body)
