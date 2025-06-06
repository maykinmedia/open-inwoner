from datetime import datetime

from django.test import Client, TestCase

import pytz

from ..models import User


class TestPrevLogin(TestCase):
    def setUp(self):
        self.user = User(first_name="Foo", last_name="Bar")
        self.user.set_password("12345")
        self.user.email = "foo@foo.com"
        self.user.save()

        self.client = Client()

    def test_previous_login_gets_updated_on_last_login_update(self):
        """
        Check if 'previous_login' is set to the value
        of 'last_login' before 'last_login' is updated.
        """

        self.user.last_login = datetime(2025, 2, 22, 8, 0, 0, tzinfo=pytz.UTC)
        self.user.save(update_fields=["last_login"])

        # Should not be updated to a non-null value
        # yet, since this was the first login
        self.assertIsNone(self.user.previous_login)

        old_last_login = self.user.last_login

        self.user.last_login = datetime(2025, 8, 14, 7, 0, 0, tzinfo=pytz.UTC)
        self.user.save(update_fields=["last_login"])

        self.assertEqual(self.user.previous_login, old_last_login)

    def test_previous_login_gets_updated_on_login(self):
        """
        Check if 'previous_login' is set to the value
        of 'last_login' before 'last_login' is updated.
        """

        self.client.login(email=self.user.email, password="12345")
        self.user.refresh_from_db()

        # Should not be updated to a non-null value
        # yet, since this was the first login
        self.assertIsNone(self.user.previous_login)

        old_last_login = self.user.last_login

        self.client.logout()
        self.client.login(email=self.user.email, password="12345")
        self.user.refresh_from_db()

        self.assertEqual(self.user.previous_login, old_last_login)

    def test_programmatically_created_user_does_not_break_previous_login_signal(self):
        try:
            new_user = User(first_name="Foo", last_name="Bar")
            new_user.save()
        except Exception as e:
            self.fail(f"Exception raised on trying to save unsaved user: {e}")

    def test_programmatically_created_user_does_not_break_previous_login_signal_via_account_creation(
        self,
    ):
        try:
            new_user = User.objects.create_user(
                first_name="Foo",
                last_name="Bar",
                password="12345",
                email="foo@foo2.com",
            )

            self.client.login(email=new_user.email, password="12345")
        except Exception as e:
            self.fail(f"Exception raised on trying to save unsaved user: {e}")
