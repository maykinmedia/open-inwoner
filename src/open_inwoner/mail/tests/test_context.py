from django.test import TestCase

from open_inwoner.mail.context import mail_context


class TestMailContext(TestCase):
    def test_context_ok(self):
        context = mail_context()
        self.assertIsNotNone(context)

        self.assertIn("logo", context)
        self.assertIn("theming", context)

        self.assertIn("login_page", context)
        self.assertIn("profile_notifications", context)
        self.assertIn("profile_page", context)

        self.assertIn("contact_page", context)
        self.assertIn("contact_phonenumber", context)
