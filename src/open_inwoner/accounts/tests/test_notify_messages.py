from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.configurations.models import SiteConfiguration

from ..tasks import schedule_user_notifications
from .factories import MessageFactory, UserFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class MessagesNotificationTest(TestCase):
    def test_send_emails_about_messages(self):
        jack = UserFactory.create(first_name="Jack")
        jill = UserFactory.create(first_name="Jill")
        harry = UserFactory.create(first_name="Harry")
        sally = UserFactory.create(first_name="Sally")
        harry_to_jack = MessageFactory.create(receiver=jack, sender=harry)
        sally_to_jack = MessageFactory.create_batch(2, receiver=jack, sender=sally)
        harry_to_jill = MessageFactory.create(receiver=jill, sender=harry)
        sally_to_jill = MessageFactory.create_batch(3, receiver=jill, sender=sally)

        messages = [harry_to_jack, *sally_to_jack, harry_to_jill, *sally_to_jill]

        schedule_user_notifications.delay(notify_about="messages", channel="email")

        self.assertEqual(len(mail.outbox), 2)

        email1, email2 = sorted(mail.outbox, key=lambda x: x.to, reverse=True)
        for email in [email1, email2]:
            self.assertEqual(email.subject, "Nieuwe berichten op Open Inwoner Platform")
            html_body = email.alternatives[0][0]
            self.assertIn(reverse("inbox:index"), html_body)

        self.assertEqual(email1.to, [jill.email])
        self.assertIn("U heeft 4 berichten ontvangen van 2 gebruikers.", email1.body)
        self.assertEqual(email2.to, [jack.email])
        self.assertIn("U heeft 3 berichten ontvangen van 2 gebruikers.", email2.body)

        for message in messages:
            message.refresh_from_db()
            self.assertTrue(message.sent)

    def test_no_email_about_received_message_if_disabled_globally(self):
        config = SiteConfiguration.get_solo()
        config.notifications_messages_enabled = False
        config.save()

        user = UserFactory()
        sender = UserFactory()
        message = MessageFactory.create(receiver=user, sender=sender)

        schedule_user_notifications.delay(notify_about="messages", channel="email")

        self.assertEqual(len(mail.outbox), 0)

        message.refresh_from_db()

        self.assertFalse(message.sent)

    def test_no_email_about_received_message_when_disabled_by_user(self):
        user = UserFactory(messages_notifications=False)
        sender = UserFactory()
        message = MessageFactory.create(receiver=user, sender=sender)

        self.assertFalse(message.sent)

        schedule_user_notifications.delay(notify_about="messages", channel="email")

        self.assertEqual(len(mail.outbox), 0)

        message.refresh_from_db()

        self.assertFalse(message.sent)

    def test_no_email_about_already_seen_message(self):
        user = UserFactory.create()

        message = MessageFactory.create(receiver=user, seen=True)

        schedule_user_notifications.delay(notify_about="messages", channel="email")

        self.assertEqual(len(mail.outbox), 0)

        message.refresh_from_db()
        self.assertFalse(message.sent)

    def test_no_email_about_sent_message(self):
        user = UserFactory.create()

        MessageFactory.create(receiver=user, sent=True)

        schedule_user_notifications.delay(notify_about="messages", channel="email")

        self.assertEqual(len(mail.outbox), 0)
