from datetime import date, timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from open_inwoner.accounts.tests.factories import ActionFactory, UserFactory


class NotifyComandTests(TestCase):
    def test_notify_about_expiring_action(self):
        user = UserFactory()
        action = ActionFactory(end_date=date.today(), created_by=user)

        call_command("actions_expire")
        self.assertEqual(len(mail.outbox), 1)

        sent_mail = mail.outbox[0]
        html_body = sent_mail.alternatives[0][0]

        self.assertEqual(
            sent_mail.subject, "Actions about to end today at Open Inwoner Platform"
        )
        self.assertEqual(sent_mail.to, [user.email])
        self.assertIn(action.name, html_body)
        self.assertIn(reverse("accounts:action_list"), html_body)

    def test_action_does_not_expire_yet(self):
        user = UserFactory()
        ActionFactory(end_date=date.today() + timedelta(days=1), created_by=user)
        call_command("actions_expire")
        self.assertEqual(len(mail.outbox), 0)

    def test_action_does_not_expired(self):
        user = UserFactory()
        ActionFactory(end_date=date.today() - timedelta(days=1), created_by=user)
        call_command("actions_expire")
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_about_expiring_action_inactive_user(self):
        user = UserFactory(is_active=False)
        action = ActionFactory(end_date=date.today(), created_by=user)
        call_command("actions_expire")
        self.assertEqual(len(mail.outbox), 0)
