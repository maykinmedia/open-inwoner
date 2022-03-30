from datetime import date, timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from open_inwoner.accounts.tests.factories import ContactFactory, UserFactory
from open_inwoner.plans.models import Plan

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

    def test_notify_about_expiring_plan_inactive_user(self):
        user = UserFactory(is_active=False)
        plan = PlanFactory(end_date=date.today(), created_by=user)
        call_command("plans_expire")
        self.assertEqual(len(mail.outbox), 0)

    def test_notify_about_expiring_plan(self):
        user = UserFactory()
        user2 = UserFactory()
        contact = ContactFactory(contact_user=user2)
        plan = PlanFactory(end_date=date.today(), created_by=user)
        plan.contacts.add(contact)

        call_command("plans_expire")
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(Plan.objects.count(), 1)

        sent_mail = mail.outbox[0]
        html_body = sent_mail.alternatives[0][0]

        self.assertEqual(
            sent_mail.subject, "Plans about to end today at Open Inwoner Platform"
        )
        self.assertEqual(sent_mail.to, [user.email])
        self.assertIn(plan.title, html_body)
        self.assertIn(plan.goal, html_body)
        self.assertIn(reverse("plans:plan_list"), html_body)

        sent_mail2 = mail.outbox[1]
        html_body2 = sent_mail.alternatives[0][0]

        self.assertEqual(
            sent_mail2.subject, "Plans about to end today at Open Inwoner Platform"
        )
        self.assertEqual(sent_mail2.to, [user2.email])
        self.assertIn(plan.title, html_body2)
        self.assertIn(plan.goal, html_body2)
        self.assertIn(reverse("plans:plan_list"), html_body2)
