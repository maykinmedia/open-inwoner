from datetime import date, timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.accounts.tests.factories import ActionFactory, UserFactory

from ..tasks import schedule_user_notifications


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ExpiringActionsNotificationTest(TestCase):
    def test_send_emails_about_expiring_actions(self):
        harry = UserFactory()
        sally = UserFactory()
        joe = UserFactory()
        schmoe = UserFactory()
        ActionFactory(end_date=date.today(), created_by=harry, is_for=joe)
        ActionFactory(end_date=date.today(), created_by=sally, is_for=schmoe)
        # contrast: no email for user without action
        UserFactory()

        schedule_user_notifications.delay(notify_about="actions", channel="email")

        self.assertEqual(len(mail.outbox), 2)

        email1, email2 = mail.outbox

        for email, recipient in zip([email1, email2], [joe, schmoe]):
            self.assertEqual(
                email.subject, "Acties verlopen vandaag op Open Inwoner Platform"
            )
            html_body = email.alternatives[0][0]
            self.assertIn(reverse("profile:action_list"), html_body)

            self.assertEqual(email.to, [recipient.email])

    def test_no_email_about_expiring_action_when_disabled(self):
        ActionFactory(end_date=date.today(), created_by__plans_notifications=False)

        schedule_user_notifications.delay(notify_about="actions", channel="email")

        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_about_action_not_yet_expiring(self):
        ActionFactory(end_date=date.today() + timedelta(days=1))

        schedule_user_notifications.delay(notify_about="actions", channel="email")

        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_about_action_already_expired(self):
        ActionFactory(end_date=date.today() - timedelta(days=1))

        schedule_user_notifications.delay(notify_about="actions", channel="email")

        self.assertEqual(len(mail.outbox), 0)

    def test_no_email_about_expiring_action_inactive_user(self):
        ActionFactory(end_date=date.today(), created_by__is_active=False)

        schedule_user_notifications.delay(notify_about="actions", channel="email")

        self.assertEqual(len(mail.outbox), 0)
