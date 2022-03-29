from datetime import date, timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from open_inwoner.accounts.tests.factories import UserFactory

from .factories import PlanFactory


class NotifyComandTests(TestCase):
    def test_notify_about_expiring_plan(self):
        user = UserFactory()
        plan = PlanFactory(end_date=date.today(), created_by=user)

        call_command("plans_expire")
        self.assertEqual(len(mail.outbox), 1)

        sent_mail = mail.outbox[0]
        html_body = sent_mail.alternatives[0][0]

        self.assertEqual(
            sent_mail.subject, "Plans about to end today at Open Inwoner Platform"
        )
        self.assertEqual(sent_mail.to, [user.email])
        self.assertIn(plan.title, html_body)
        self.assertIn(plan.goal, html_body)
        self.assertIn(reverse("plans:plan_list"), html_body)

    def test_plan_does_not_expire_yet(self):
        user = UserFactory()
        PlanFactory(end_date=date.today() + timedelta(days=1), created_by=user)
        call_command("plans_expire")
        self.assertEqual(len(mail.outbox), 0)

    def test_plan_does_not_expired(self):
        user = UserFactory()
        PlanFactory(end_date=date.today() - timedelta(days=1), created_by=user)
        call_command("plans_expire")
        self.assertEqual(len(mail.outbox), 0)
