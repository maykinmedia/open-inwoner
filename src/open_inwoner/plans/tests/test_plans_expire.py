from datetime import date, timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.plans.models import Plan

from .factories import PlanFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
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
        self.assertIn(reverse("collaborate:plan_list"), html_body)

    def test_no_notification_about_expiring_plan_when_disabled(self):
        user = UserFactory(plans_notifications=False)
        plan = PlanFactory(end_date=date.today(), created_by=user)
        call_command("plans_expire")
        self.assertEqual(len(mail.outbox), 0)

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
        contact = UserFactory()
        plan = PlanFactory(end_date=date.today(), created_by=user)
        plan.plan_contacts.add(contact)

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
        self.assertIn(reverse("collaborate:plan_list"), html_body)

        sent_mail2 = mail.outbox[1]
        html_body2 = sent_mail.alternatives[0][0]

        self.assertEqual(
            sent_mail2.subject, "Plans about to end today at Open Inwoner Platform"
        )
        self.assertEqual(sent_mail2.to, [contact.email])
        self.assertIn(plan.title, html_body2)
        self.assertIn(plan.goal, html_body2)
        self.assertIn(reverse("collaborate:plan_list"), html_body2)

    def test_notify_only_user_with_active_notifications(self):
        user = UserFactory()
        contact = UserFactory(plans_notifications=False)
        plan = PlanFactory(end_date=date.today(), created_by=user)
        plan.plan_contacts.add(contact)

        call_command("plans_expire")
        self.assertEqual(len(mail.outbox), 1)
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
