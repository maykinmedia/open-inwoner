from datetime import date, timedelta
from unittest.mock import Mock, patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.plans.models import Plan
from open_inwoner.plans.tests.factories import PlanFactory

from ..tasks import schedule_user_notifications


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ExpiringPlansNotificationTest(TestCase):
    def test_send_emails_about_expiring_plans(self):
        harry = UserFactory(first_name="Harry")
        sally = UserFactory(first_name="Sally")
        # contrast: not associated with plan, should not trigger email
        UserFactory()
        plan_harry = PlanFactory(
            end_date=date.today(), created_by=harry, title="Harry's plan"
        )
        plan_sally = PlanFactory(
            end_date=date.today(), created_by=sally, title="Sally's plan"
        )

        schedule_user_notifications(notify_about="plans", channel="email")

        self.assertEqual(len(mail.outbox), 2)

        email_harry, email_sally = mail.outbox
        for email in (email_harry, email_sally):
            self.assertEqual(
                email.subject, "Plannen vervallen vandaag op Open Inwoner Platform"
            )
            html_body = email.alternatives[0][0]
            self.assertIn(reverse("collaborate:plan_list"), html_body)

        html_body = email_harry.alternatives[0][0]
        self.assertEqual(email_harry.to, [harry.email])
        self.assertIn(plan_harry.title, html_body)
        self.assertIn(plan_harry.goal, html_body)

        html_body = email_sally.alternatives[0][0]
        self.assertEqual(email_sally.to, [sally.email])
        self.assertIn(plan_sally.title, html_body)
        self.assertIn(plan_sally.goal, html_body)

    @patch("open_inwoner.userfeed.hooks.plan_expiring", autospec=True)
    def test_notify_about_expiring_plan_userfeed_hook(self, mock_plan_expiring: Mock):
        PlanFactory(end_date=date.today())

        schedule_user_notifications(notify_about="plans", channel="email")

        mock_plan_expiring.assert_called_once()

    def test_dont_notify_about_expiring_plan_when_disabled(self):
        PlanFactory(end_date=date.today(), created_by__plans_notifications=False)

        schedule_user_notifications(notify_about="plans", channel="email")

        self.assertEqual(len(mail.outbox), 0)

    def test_dont_notify_about_plan_not_expiring(self):
        PlanFactory(end_date=date.today() + timedelta(days=1))

        schedule_user_notifications(notify_about="plans", channel="email")

        self.assertEqual(len(mail.outbox), 0)

    def test_dont_notify_about_expired_plan(self):
        PlanFactory(end_date=date.today() - timedelta(days=1))

        schedule_user_notifications(notify_about="plans", channel="email")

        self.assertEqual(len(mail.outbox), 0)

    def test_dont_notify_about_expiring_plan_inactive_user(self):
        PlanFactory(end_date=date.today(), created_by__is_active=False)

        schedule_user_notifications(notify_about="plans", channel="email")

        self.assertEqual(len(mail.outbox), 0)

    def test_send_emails_about_expiring_plan_email_contact(self):
        user = UserFactory()
        contact = UserFactory()
        plan = PlanFactory(end_date=date.today(), created_by=user)
        plan.plan_contacts.add(contact)

        schedule_user_notifications(notify_about="plans", channel="email")

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(Plan.objects.count(), 1)

        sent_mail = mail.outbox[0]
        html_body = sent_mail.alternatives[0][0]

        self.assertEqual(
            sent_mail.subject, "Plannen vervallen vandaag op Open Inwoner Platform"
        )
        self.assertEqual(sent_mail.to, [user.email])
        self.assertIn(plan.title, html_body)
        self.assertIn(plan.goal, html_body)
        self.assertIn(reverse("collaborate:plan_list"), html_body)

        sent_mail2 = mail.outbox[1]
        html_body2 = sent_mail.alternatives[0][0]

        self.assertEqual(
            sent_mail2.subject, "Plannen vervallen vandaag op Open Inwoner Platform"
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

        schedule_user_notifications(notify_about="plans", channel="email")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Plan.objects.count(), 1)

        sent_mail = mail.outbox[0]
        html_body = sent_mail.alternatives[0][0]

        self.assertEqual(
            sent_mail.subject, "Plannen vervallen vandaag op Open Inwoner Platform"
        )
        self.assertEqual(sent_mail.to, [user.email])
        self.assertIn(plan.title, html_body)
        self.assertIn(plan.goal, html_body)
        self.assertIn(reverse("collaborate:plan_list"), html_body)
